
from copy import deepcopy
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse
import uuid
import asyncio
import inspect
import json
import threading
import time

import aiohttp
import requests
from requests.adapters import HTTPAdapter

from ..._ljp_coro.base_class import Ljp_BaseClass
from ljp_page._ljp_config.request_config.request_config import RequestConfig, TimeoutConfig, merge_request_config, \
    get_request_config
from ljp_page._ljp_config.request_config.session_config import HookValue, SessionMetrics, SessionHooks, LjpResponse, \
    PreparedRequest, RequestMetadata, LjpRequestException


class SyncVerbMixin:
    """HTTP verbs for SyncSession."""

    def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("DELETE", url, **kwargs)


class AsyncVerbMixin:
    """HTTP verbs for AsyncSession."""

    async def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url, **kwargs)


class SessionBase(Ljp_BaseClass, ABC):
    """Common configuration, logging, metrics, hooks and retry helpers."""

    def __init__(
        self,
        config: RequestConfig,
        *,
        logger: Any = None,
        hooks: HookValue = None,
    ) -> None:
        super().__init__(logger=logger)
        self.config = deepcopy(config)
        self.metrics = SessionMetrics()
        self.hooks = SessionHooks.from_value(hooks)
        self._state_lock = threading.RLock()
        self._cookie_store = deepcopy(self.config.cookies)

    @property
    def headers(self) -> dict[str, str]:
        """Return a copy of current default headers."""

        with self._state_lock:
            return deepcopy(self.config.headers)

    @property
    def cookies(self) -> dict[str, str]:
        """Return a copy of persisted cookies."""

        with self._state_lock:
            return deepcopy(self._cookie_store)

    def update_headers(self, headers: Mapping[str, str]) -> None:
        """Merge default headers into the session snapshot."""

        with self._state_lock:
            self.config.headers.update(dict(headers))
        self._sync_headers_to_native()

    def update_cookies(self, cookies: Mapping[str, str]) -> None:
        """Merge cookies into the persisted cookie store."""

        with self._state_lock:
            self._cookie_store.update(dict(cookies))
        self._sync_cookies_to_native()

    def _store_cookies(self, cookies: Mapping[str, str]) -> None:
        with self._state_lock:
            self._cookie_store.update(dict(cookies))

    def _record_success(self, elapsed: float, retries: int) -> None:
        with self._state_lock:
            self.metrics.request_count += 1
            self.metrics.retry_count += retries
            self.metrics.total_elapsed += elapsed

    def _record_failure(self, elapsed: float, retries: int) -> None:
        with self._state_lock:
            self.metrics.request_count += 1
            self.metrics.error_count += 1
            self.metrics.retry_count += retries
            self.metrics.total_elapsed += elapsed

    def _resolve_timeout(self, timeout: Any) -> TimeoutConfig:
        if timeout is None:
            return deepcopy(self.config.timeout)
        if isinstance(timeout, TimeoutConfig):
            return deepcopy(timeout)
        if isinstance(timeout, (int, float)):
            value = float(timeout)
            return TimeoutConfig(connect=value, read=value)
        if isinstance(timeout, tuple) and len(timeout) == 2:
            return TimeoutConfig(connect=float(timeout[0]), read=float(timeout[1]))
        if isinstance(timeout, Mapping):
            return merge_request_config(self.config, timeout=timeout).timeout
        raise TypeError(f"Unsupported timeout type: {type(timeout).__name__}")

    def _resolve_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        if not self.config.base_url:
            raise ValueError("Relative URL requires base_url in request config")
        return urljoin(f"{self.config.base_url.rstrip('/')}/", url.lstrip("/"))

    def _resolve_proxy(
        self,
        url: str,
        proxy: str | None,
        proxies: Mapping[str, str] | None,
    ) -> tuple[dict[str, str] | None, str | None]:
        scheme = urlparse(url).scheme or "http"
        if proxy:
            return {scheme: proxy}, proxy
        if proxies:
            proxy_dict = dict(proxies)
            return proxy_dict, proxy_dict.get(scheme)
        proxy_dict = self.config.proxy.as_requests()
        return proxy_dict, self.config.proxy.for_scheme(scheme)

    @staticmethod
    def _safe_payload(payload: Any) -> Any:
        if payload is None:
            return None
        if isinstance(payload, bytes):
            return f"<bytes:{len(payload)}>"
        if isinstance(payload, Mapping):
            return dict(payload)
        if isinstance(payload, (list, tuple)):
            return list(payload)
        return str(payload)

    def _prepare_request(
        self,
        method: str,
        url: str,
        kwargs: Mapping[str, Any],
    ) -> PreparedRequest:
        method_name = method.upper()
        final_url = self._resolve_url(url)
        request_kwargs = dict(kwargs)
        custom_headers = request_kwargs.pop("headers", None) or {}
        custom_cookies = request_kwargs.pop("cookies", None) or {}
        timeout = self._resolve_timeout(request_kwargs.pop("timeout", None))
        proxy = request_kwargs.pop("proxy", None)
        proxies = request_kwargs.pop("proxies", None)
        allow_redirects = bool(
            request_kwargs.pop("allow_redirects", self.config.allow_redirects)
        )
        stream = bool(request_kwargs.pop("stream", self.config.stream))
        verify_ssl = bool(request_kwargs.pop("verify_ssl", self.config.verify_ssl))
        trace_id = str(request_kwargs.pop("trace_id", uuid.uuid4().hex))

        headers = self.headers
        headers.update(dict(custom_headers))
        cookies = self.cookies
        cookies.update(dict(custom_cookies))
        resolved_proxies, proxy_url = self._resolve_proxy(final_url, proxy, proxies)
        metadata = RequestMetadata(
            trace_id=trace_id,
            method=method_name,
            url=final_url,
            headers=headers,
            cookies=cookies,
            timeout=timeout.requests_timeout,
            allow_redirects=allow_redirects,
            stream=stream,
            verify_ssl=verify_ssl,
            proxy=proxy_url,
            payload={
                "params": self._safe_payload(request_kwargs.get("params")),
                "data": self._safe_payload(request_kwargs.get("data")),
                "json": self._safe_payload(request_kwargs.get("json")),
            },
        )
        request_kwargs["headers"] = headers
        request_kwargs["cookies"] = cookies
        request_kwargs["allow_redirects"] = allow_redirects
        return PreparedRequest(
            metadata=metadata,
            request_kwargs=request_kwargs,
            proxies=resolved_proxies,
            proxy_url=proxy_url,
        )
    def _build_response(
        self,
        *,
        metadata: RequestMetadata,
        status_code: int,
        headers: Mapping[str, str],
        content: bytes,
        encoding: str | None,
        elapsed: float,
        retries: int,
    ) -> LjpResponse:
        return LjpResponse(
            status_code=status_code,
            headers=dict(headers),
            encoding=encoding,
            content=content,
            elapsed=elapsed,
            retries=retries,
            request=metadata,
        )

    def _should_retry_status(self, method: str, status_code: int) -> bool:
        retry = self.config.retry
        return (
            method.upper() in retry.allowed_methods
            and status_code in retry.status_forcelist
        )

    def _should_retry_exception(self, method: str, exc: LjpRequestException) -> bool:
        if method.upper() not in self.config.retry.allowed_methods:
            return False
        return exc.category in {"timeout", "network", "proxy", "ssl"}

    def _backoff_delay(self, attempt: int) -> float:
        return self.config.retry.backoff_factor * (2 ** attempt)

    def _run_callbacks_sync(
        self,
        callbacks: Iterable[Callable[..., Any]],
        payload: Any,
    ) -> None:
        for callback in callbacks:
            result = callback(self, payload)
            if inspect.isawaitable(result):
                raise TypeError("Async hook is not supported in sync session")

    async def _run_callbacks_async(
        self,
        callbacks: Iterable[Callable[..., Any]],
        payload: Any,
    ) -> None:
        for callback in callbacks:
            result = callback(self, payload)
            if inspect.isawaitable(result):
                await result

    @abstractmethod
    def _sync_headers_to_native(self) -> None:
        """Propagate default headers to native session state."""

    @abstractmethod
    def _sync_cookies_to_native(self) -> None:
        """Propagate cookie store to native session state."""

class SyncSession(SessionBase, SyncVerbMixin):
    """Thread-safe sync runtime backed by per-thread requests.Session."""

    def __init__(
        self,
        config: RequestConfig,
        *,
        logger: Any = None,
        hooks: HookValue = None,
    ) -> None:
        super().__init__(config, logger=logger, hooks=hooks)
        self._thread_local = threading.local()
        self._native_sessions: list[requests.Session] = []

    def _new_native_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=self.config.pool.max_connections,
            pool_maxsize=self.config.pool.max_keepalive_connections,
            max_retries=0,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.headers)
        session.cookies.update(self.cookies)
        session.verify = self.config.verify_ssl
        session.trust_env = self.config.trust_env
        proxies = self.config.proxy.as_requests()
        if proxies:
            session.proxies.update(proxies)
        with self._state_lock:
            self._native_sessions.append(session)
        return session

    def get_native_session(self) -> requests.Session:
        """Return the thread-local native session."""

        native = getattr(self._thread_local, "session", None)
        if native is None:
            native = self._new_native_session()
            self._thread_local.session = native
        return native

    def _sync_headers_to_native(self) -> None:
        headers = self.headers
        with self._state_lock:
            sessions = list(self._native_sessions)
        for session in sessions:
            session.headers.clear()
            session.headers.update(headers)

    def _sync_cookies_to_native(self) -> None:
        cookies = self.cookies
        with self._state_lock:
            sessions = list(self._native_sessions)
        for session in sessions:
            session.cookies.update(cookies)

    def _copy_cookies_from_native(self, session: requests.Session) -> None:
        self._store_cookies(session.cookies.get_dict())

    @staticmethod
    def _map_exception(
        exc: Exception,
        *,
        trace_id: str,
        method: str,
        url: str,
        retries: int,
        elapsed: float,
    ) -> LjpRequestException:
        if isinstance(exc, requests.Timeout):
            category = "timeout"
        elif isinstance(exc, requests.exceptions.SSLError):
            category = "ssl"
        elif isinstance(exc, requests.exceptions.ProxyError):
            category = "proxy"
        elif isinstance(exc, requests.RequestException):
            category = "network"
        else:
            category = "unknown"
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return LjpRequestException(
            "Sync request failed",
            trace_id=trace_id,
            method=method,
            url=url,
            category=category,
            retries=retries,
            elapsed=elapsed,
            status_code=status_code,
            original_exception=exc,
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        native_session: requests.Session | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        """Execute a sync HTTP request."""

        prepared = self._prepare_request(method, url, kwargs)
        total_start = time.perf_counter()
        delay = max(0.0, self.config.request_delay)
        if delay:
            time.sleep(delay)
        self._run_callbacks_sync(self.hooks.before_request, prepared.metadata)
        total_retries = self.config.retry.total
        for attempt in range(total_retries + 1):
            active_session = native_session or self.get_native_session()
            active_session.cookies.update(prepared.metadata.cookies)
            try:
                response = active_session.request(
                    prepared.metadata.method,
                    prepared.metadata.url,
                    timeout=prepared.metadata.timeout,
                    stream=prepared.metadata.stream,
                    verify=prepared.metadata.verify_ssl,
                    proxies=prepared.proxies,
                    **prepared.request_kwargs,
                )
                self._copy_cookies_from_native(active_session)
                if (
                    attempt < total_retries
                    and self._should_retry_status(
                        prepared.metadata.method,
                        response.status_code,
                    )
                ):
                    response.close()
                    time.sleep(self._backoff_delay(attempt))
                    continue
                built_response = self._build_response(
                    metadata=prepared.metadata,
                    status_code=response.status_code,
                    headers=response.headers,
                    content=response.content,
                    encoding=response.encoding,
                    elapsed=time.perf_counter() - total_start,
                    retries=attempt,
                )
                self._record_success(built_response.elapsed, attempt)
                self._run_callbacks_sync(self.hooks.after_response, built_response)
                return built_response
            except Exception as exc:  # pragma: no cover - branch tested via subclasses
                mapped = self._map_exception(
                    exc,
                    trace_id=prepared.metadata.trace_id,
                    method=prepared.metadata.method,
                    url=prepared.metadata.url,
                    retries=attempt,
                    elapsed=time.perf_counter() - total_start,
                )
                if attempt < total_retries and self._should_retry_exception(
                    prepared.metadata.method,
                    mapped,
                ):
                    time.sleep(self._backoff_delay(attempt))
                    continue
                self._record_failure(mapped.elapsed or 0.0, attempt)
                self._run_callbacks_sync(self.hooks.on_error, mapped)
                raise mapped from exc
        raise AssertionError("unreachable")

    def close(self) -> None:
        """Close all native sessions created by this wrapper."""

        with self._state_lock:
            sessions = list(self._native_sessions)
            self._native_sessions.clear()
        for session in sessions:
            session.close()
        if hasattr(self._thread_local, "session"):
            del self._thread_local.session

    def __enter__(self) -> "SyncSession":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

class AsyncSession(SessionBase, AsyncVerbMixin):
    """Coroutine-safe async runtime backed by aiohttp.ClientSession."""

    def __init__(
        self,
        config: RequestConfig,
        *,
        logger: Any = None,
        hooks: HookValue = None,
    ) -> None:
        super().__init__(config, logger=logger, hooks=hooks)
        self._session: aiohttp.ClientSession | None = None
        self._session_lock: asyncio.Lock | None = None

    def _get_session_lock(self) -> asyncio.Lock:
        if self._session_lock is None:
            self._session_lock = asyncio.Lock()
        return self._session_lock

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session
        async with self._get_session_lock():
            if self._session and not self._session.closed:
                return self._session
            connector = aiohttp.TCPConnector(
                limit=self.config.pool.max_connections,
                limit_per_host=self.config.pool.max_connections_per_host,
                ssl=self.config.verify_ssl,
            )
            jar = aiohttp.CookieJar(unsafe=True)
            jar.update_cookies(self.cookies)
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                cookie_jar=jar,
                connector=connector,
                timeout=self.config.timeout.aiohttp_timeout,
                trust_env=self.config.trust_env,
            )
            return self._session

    async def get_native_session(self) -> aiohttp.ClientSession:
        """Return the underlying aiohttp session."""

        return await self._ensure_session()

    def _sync_headers_to_native(self) -> None:
        if self._session and not self._session.closed:
            self._session.headers.clear()
            self._session.headers.update(self.headers)

    def _sync_cookies_to_native(self) -> None:
        if self._session and not self._session.closed:
            self._session.cookie_jar.update_cookies(self.cookies)

    def _copy_cookies_from_native(self, session: aiohttp.ClientSession) -> None:
        cookies = {cookie.key: cookie.value for cookie in session.cookie_jar}
        self._store_cookies(cookies)

    @staticmethod
    def _map_exception(
        exc: Exception,
        *,
        trace_id: str,
        method: str,
        url: str,
        retries: int,
        elapsed: float,
    ) -> LjpRequestException:
        if isinstance(exc, asyncio.TimeoutError):
            category = "timeout"
        elif isinstance(exc, aiohttp.ClientSSLError):
            category = "ssl"
        elif isinstance(exc, aiohttp.ClientProxyConnectionError):
            category = "proxy"
        elif isinstance(exc, aiohttp.ClientError):
            category = "network"
        else:
            category = "unknown"
        status_code = getattr(exc, "status", None)
        return LjpRequestException(
            "Async request failed",
            trace_id=trace_id,
            method=method,
            url=url,
            category=category,
            retries=retries,
            elapsed=elapsed,
            status_code=status_code,
            original_exception=exc,
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        native_session: aiohttp.ClientSession | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        """Execute an async HTTP request."""

        prepared = self._prepare_request(method, url, kwargs)
        total_start = time.perf_counter()
        delay = max(0.0, self.config.request_delay)
        if delay:
            await asyncio.sleep(delay)
        await self._run_callbacks_async(self.hooks.before_request, prepared.metadata)
        total_retries = self.config.retry.total
        for attempt in range(total_retries + 1):
            active_session = native_session or await self._ensure_session()
            active_session.cookie_jar.update_cookies(prepared.metadata.cookies)
            try:
                request_kwargs = dict(prepared.request_kwargs)
                request_kwargs["timeout"] = self._resolve_timeout(
                    kwargs.get("timeout")
                ).aiohttp_timeout
                async with active_session.request(
                    prepared.metadata.method,
                    prepared.metadata.url,
                    ssl=prepared.metadata.verify_ssl,
                    proxy=prepared.proxy_url,
                    **request_kwargs,
                ) as response:
                    content = await response.read()
                    self._copy_cookies_from_native(active_session)
                    if (
                        attempt < total_retries
                        and self._should_retry_status(
                            prepared.metadata.method,
                            response.status,
                        )
                    ):
                        await asyncio.sleep(self._backoff_delay(attempt))
                        continue
                    built_response = self._build_response(
                        metadata=prepared.metadata,
                        status_code=response.status,
                        headers=response.headers,
                        content=content,
                        encoding=response.charset,
                        elapsed=time.perf_counter() - total_start,
                        retries=attempt,
                    )
                    self._record_success(built_response.elapsed, attempt)
                    await self._run_callbacks_async(
                        self.hooks.after_response,
                        built_response,
                    )
                    return built_response
            except Exception as exc:  # pragma: no cover - branch tested via subclasses
                mapped = self._map_exception(
                    exc,
                    trace_id=prepared.metadata.trace_id,
                    method=prepared.metadata.method,
                    url=prepared.metadata.url,
                    retries=attempt,
                    elapsed=time.perf_counter() - total_start,
                )
                if attempt < total_retries and self._should_retry_exception(
                    prepared.metadata.method,
                    mapped,
                ):
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                self._record_failure(mapped.elapsed or 0.0, attempt)
                await self._run_callbacks_async(self.hooks.on_error, mapped)
                raise mapped from exc
        raise AssertionError("unreachable")

    async def open(self) -> "AsyncSession":
        """Eagerly create the underlying aiohttp session."""

        await self._ensure_session()
        return self

    async def close(self) -> None:
        """Close the underlying aiohttp session."""

        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "AsyncSession":
        return await self.open()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

def create_session(
    mode: Literal["sync", "async"]='sync',
    **options: Any,
) -> SyncSession | AsyncSession:
    """Create a ready-to-use custom session wrapper."""

    logger = options.pop("logger", None)
    hooks = options.pop("hooks", None)
    config_override = options.pop("config", None)
    base_config = deepcopy(config_override) if config_override else get_request_config()
    config = merge_request_config(base_config, **options)
    if mode == "sync":
        return SyncSession(config, logger=logger, hooks=hooks)
    if mode == "async":
        return AsyncSession(config, logger=logger, hooks=hooks)
    raise ValueError("mode must be 'sync' or 'async'")


__all__ = [
    "AsyncSession",
    "LjpRequestException",
    "LjpResponse",
    "RequestMetadata",
    "SessionHooks",
    "SessionMetrics",
    "SyncSession",
    "create_session",
]