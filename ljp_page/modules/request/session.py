
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from copy import deepcopy
from typing import Any, Awaitable, Callable, Literal, Mapping, Sequence
from urllib.parse import urljoin, urlparse

import aiohttp
import requests

from ...config.request_config import (
    LjpConfig,
    TimeoutConfig,
    get_request_config,
    merge_request_config,
)
from ...config.request_config.session_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
    SessionMetrics,
)
from ...utils.logger.logger import Logger
from ...core.adapters import (
    AdapterResponse,
    AiohttpTransportAdapter,
    AsyncTransportAdapter,
    RequestsTransportAdapter,
    SyncTransportAdapter,
)
from ...core.middleware import (
    AsyncMiddleware,
    AsyncRequestMiddleware,
    AsyncResponseMiddleware,
    AsyncRetryMiddleware,
    RequestMiddleware,
    ResponseMiddleware,
    SyncMiddleware,
    SyncRetryMiddleware,
)
from .base import RequestModuleBase


class SyncVerbMixin:

    def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("DELETE", url, **kwargs)


class AsyncVerbMixin:

    async def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url, **kwargs)


class SessionBase(RequestModuleBase):

    def __init__(self, config: LjpConfig, logger: Any = None) -> None:
        super().__init__(config=deepcopy(config), logger=logger)
        self.metrics = SessionMetrics()
        self._state_lock = threading.RLock()
        self._cookie_store = deepcopy(self.config.request.cookies)
        self.logger = logger or self._build_default_logger()
        if isinstance(self.logger, Logger):
            self.logger.set_enabled_levels(self.config.log.enabled_levels)
            self.logger.set_default_level(self.config.log.default_level)

    def _build_default_logger(self) -> Logger:
        return Logger(
            log_file_path=self.config.log.log_file_path,
            log_level=self.config.log.default_level,
            enabled_levels=self.config.log.enabled_levels,
            level_names=self.config.log.level_names,
            aliases=self.config.log.aliases,
            output_console=self.config.log.output_console,
            output_file=self.config.log.output_file,
        )

    @property
    def headers(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self.config.request.headers)

    @property
    def cookies(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self._cookie_store)

    def update_headers(self, headers: Mapping[str, str]) -> None:
        with self._state_lock:
            self.config.request.headers.update(dict(headers))
        self._sync_headers_to_native()

    def update_cookies(self, cookies: Mapping[str, str]) -> None:
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

    def _resolve_timeout(self, timeout: Any) -> tuple[float, float]:
        if timeout is None:
            return self.config.timeout.requests_timeout
        if isinstance(timeout, TimeoutConfig):
            return timeout.requests_timeout
        if isinstance(timeout, (int, float)):
            numeric = float(timeout)
            return numeric, numeric
        if isinstance(timeout, tuple) and len(timeout) == 2:
            return float(timeout[0]), float(timeout[1])
        if isinstance(timeout, Mapping):
            return merge_request_config(self.config, timeout=timeout).timeout.requests_timeout
        raise TypeError(f"涓嶆敮鎸佺殑 timeout 绫诲瀷: {type(timeout).__name__}")

    def _resolve_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        if not self.config.request.base_url:
            raise ValueError("鐩稿璺緞璇锋眰闇€瑕侀厤缃?base_url")
        return urljoin(f"{self.config.request.base_url.rstrip('/')}/", url.lstrip("/"))

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

    def _build_context(
        self,
        method: str,
        url: str,
        kwargs: Mapping[str, Any],
        *,
        attempt: int,
        native_session: Any = None,
    ) -> RequestContext:
        request_kwargs = dict(kwargs)
        custom_headers = request_kwargs.pop("headers", None) or {}
        custom_cookies = request_kwargs.pop("cookies", None) or {}

        timeout = self._resolve_timeout(request_kwargs.pop("timeout", None))
        proxy = request_kwargs.pop("proxy", None)
        proxies = request_kwargs.pop("proxies", None)
        allow_redirects = bool(
            request_kwargs.pop("allow_redirects", self.config.request.allow_redirects)
        )
        stream = bool(request_kwargs.pop("stream", self.config.request.stream))
        verify_ssl = bool(request_kwargs.pop("verify_ssl", self.config.request.verify_ssl))
        trace_id = str(request_kwargs.pop("trace_id", uuid.uuid4().hex))

        params = request_kwargs.pop("params", None)
        data = request_kwargs.pop("data", None)
        json_data = request_kwargs.pop("json", None)

        headers = self.headers
        headers.update(dict(custom_headers))
        cookies = self.cookies
        cookies.update(dict(custom_cookies))

        final_url = self._resolve_url(url)
        resolved_proxies, proxy_url = self._resolve_proxy(final_url, proxy, proxies)

        extra = dict(request_kwargs)
        if native_session is not None:
            extra["native_session"] = native_session

        return RequestContext(
            trace_id=trace_id,
            method=method.upper(),
            url=final_url,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            allow_redirects=allow_redirects,
            stream=stream,
            verify_ssl=verify_ssl,
            proxy_url=proxy_url,
            proxies=resolved_proxies,
            params=params,
            data=data,
            json_data=json_data,
            extra=extra,
            attempt=attempt,
        )

    @staticmethod
    def _build_response(
        context: RequestContext,
        adapter_response: AdapterResponse,
        elapsed: float,
        retries: int,
    ) -> LjpResponse:
        return LjpResponse(
            status_code=adapter_response.status_code,
            headers=dict(adapter_response.headers),
            encoding=adapter_response.encoding,
            content=adapter_response.content,
            elapsed=elapsed,
            retries=retries,
            request=context,
        )

    def _sync_headers_to_native(self) -> None:
        raise NotImplementedError

    def _sync_cookies_to_native(self) -> None:
        raise NotImplementedError


class SyncSession(SessionBase, SyncVerbMixin):

    def __init__(
        self,
        config: LjpConfig,
        *,
        logger: Any = None,
        adapter: SyncTransportAdapter | None = None,
        middlewares: Sequence[SyncMiddleware] | None = None,
        retry_middleware: SyncRetryMiddleware | None = None,
    ) -> None:
        super().__init__(config=config, logger=logger)
        self.adapter = adapter or RequestsTransportAdapter(self.config)
        self.middlewares = list(
            middlewares if middlewares is not None else self._build_default_middlewares()
        )
        if retry_middleware is not None:
            self.retry_middleware: SyncRetryMiddleware | None = retry_middleware
        elif self.config.middleware.enable_retry_middleware:
            self.retry_middleware = SyncRetryMiddleware(self.config)
        else:
            self.retry_middleware = None

    def _build_default_middlewares(self) -> list[SyncMiddleware]:
        chain: list[SyncMiddleware] = []
        if self.config.middleware.enable_request_middleware:
            chain.append(RequestMiddleware())
        if self.config.middleware.enable_response_middleware:
            chain.append(ResponseMiddleware())
        return chain

    def use(self, middleware: SyncMiddleware) -> "SyncSession":

        self.middlewares.append(middleware)
        return self

    def get_native_session(self) -> requests.Session:
        if isinstance(self.adapter, RequestsTransportAdapter):
            return self.adapter.get_native_session()
        raise TypeError("褰撳墠閫傞厤鍣ㄤ笉鏀寔杩斿洖 requests.Session")

    def _sync_headers_to_native(self) -> None:
        self.adapter.sync_defaults(self.headers, self.cookies)

    def _sync_cookies_to_native(self) -> None:
        self.adapter.sync_defaults(self.headers, self.cookies)

    @staticmethod
    def _map_exception(
        exc: Exception,
        *,
        context: RequestContext,
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
            "鍚屾璇锋眰澶辫触",
            trace_id=context.trace_id,
            method=context.method,
            url=context.url,
            category=category,
            retries=retries,
            elapsed=elapsed,
            status_code=status_code,
            original_exception=exc,
        )

    def _notify_error_middlewares(
        self,
        context: RequestContext,
        error: LjpRequestException,
        middlewares: Sequence[SyncMiddleware],
    ) -> None:
        for middleware in reversed(middlewares):
            middleware.on_error(context, error, self)

    def _send_once(
        self,
        context: RequestContext,
        *,
        attempt: int,
        total_start: float,
    ) -> LjpResponse:

        try:
            adapter_response = self.adapter.send(context)
        except Exception as exc:
            raise self._map_exception(
                exc,
                context=context,
                retries=attempt,
                elapsed=time.perf_counter() - total_start,
            ) from exc

        self._store_cookies(adapter_response.cookies)
        return self._build_response(
            context=context,
            adapter_response=adapter_response,
            elapsed=time.perf_counter() - total_start,
            retries=attempt,
        )

    def _build_middleware_chain(
        self,
        sender: Callable[[RequestContext], LjpResponse],
        middlewares: Sequence[SyncMiddleware],
    ) -> Callable[[RequestContext], LjpResponse]:

        chain = sender
        for middleware in reversed(middlewares):
            next_handler = chain

            def _make_layer(
                mw: SyncMiddleware,
                nxt: Callable[[RequestContext], LjpResponse],
            ) -> Callable[[RequestContext], LjpResponse]:
                def _layer(ctx: RequestContext) -> LjpResponse:
                    return mw.handle(ctx, nxt, self)

                return _layer

            chain = _make_layer(middleware, next_handler)
        return chain

    def request(
        self,
        method: str,
        url: str,
        *,
        native_session: requests.Session | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        delay = max(0.0, self.config.request.request_delay)
        if delay > 0:
            time.sleep(delay)
        request_middlewares = kwargs.pop("middlewares", None)
        active_middlewares = (
            list(request_middlewares)
            if request_middlewares is not None
            else list(self.middlewares)
        )

        total_retries = self.config.retry.total if self.retry_middleware else 0
        for attempt in range(total_retries + 1):
            context = self._build_context(
                method,
                url,
                kwargs,
                attempt=attempt,
                native_session=native_session,
            )

            def _sender(ctx: RequestContext) -> LjpResponse:
                return self._send_once(ctx, attempt=attempt, total_start=total_start)

            pipeline = self._build_middleware_chain(_sender, active_middlewares)

            try:
                response = pipeline(context)
            except Exception as exc:
                if isinstance(exc, LjpRequestException):
                    mapped = exc
                else:
                    mapped = self._map_exception(
                        exc,
                        context=context,
                        retries=attempt,
                        elapsed=time.perf_counter() - total_start,
                    )
                    self._notify_error_middlewares(context, mapped, active_middlewares)

                if (
                    self.retry_middleware is not None
                    and attempt < total_retries
                    and self.retry_middleware.should_retry_exception(context, mapped)
                ):
                    self.retry_middleware.wait(attempt)
                    continue

                self._record_failure(mapped.elapsed or 0.0, attempt)
                raise mapped from exc

            if (
                self.retry_middleware is not None
                and attempt < total_retries
                and self.retry_middleware.should_retry_response(context, response)
            ):
                self.retry_middleware.wait(attempt)
                continue

            self._record_success(response.elapsed, attempt)
            return response

        raise AssertionError("unreachable")

    def close(self) -> None:
        self.adapter.close()

    def __enter__(self) -> "SyncSession":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


class AsyncSession(SessionBase, AsyncVerbMixin):

    def __init__(
        self,
        config: LjpConfig,
        *,
        logger: Any = None,
        adapter: AsyncTransportAdapter | None = None,
        middlewares: Sequence[AsyncMiddleware] | None = None,
        retry_middleware: AsyncRetryMiddleware | None = None,
    ) -> None:
        super().__init__(config=config, logger=logger)
        self.adapter = adapter or AiohttpTransportAdapter(self.config)
        self.middlewares = list(
            middlewares if middlewares is not None else self._build_default_middlewares()
        )
        if retry_middleware is not None:
            self.retry_middleware: AsyncRetryMiddleware | None = retry_middleware
        elif self.config.middleware.enable_retry_middleware:
            self.retry_middleware = AsyncRetryMiddleware(self.config)
        else:
            self.retry_middleware = None

    def _build_default_middlewares(self) -> list[AsyncMiddleware]:
        chain: list[AsyncMiddleware] = []
        if self.config.middleware.enable_request_middleware:
            chain.append(AsyncRequestMiddleware())
        if self.config.middleware.enable_response_middleware:
            chain.append(AsyncResponseMiddleware())
        return chain

    def use(self, middleware: AsyncMiddleware) -> "AsyncSession":

        self.middlewares.append(middleware)
        return self

    async def get_native_session(self) -> aiohttp.ClientSession:
        if isinstance(self.adapter, AiohttpTransportAdapter):
            return await self.adapter.ensure_session()
        raise TypeError("褰撳墠閫傞厤鍣ㄤ笉鏀寔杩斿洖 aiohttp.ClientSession")

    def _sync_headers_to_native(self) -> None:
        self.adapter.sync_defaults(self.headers, self.cookies)

    def _sync_cookies_to_native(self) -> None:
        self.adapter.sync_defaults(self.headers, self.cookies)

    @staticmethod
    def _map_exception(
        exc: Exception,
        *,
        context: RequestContext,
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
            "寮傛璇锋眰澶辫触",
            trace_id=context.trace_id,
            method=context.method,
            url=context.url,
            category=category,
            retries=retries,
            elapsed=elapsed,
            status_code=status_code,
            original_exception=exc,
        )

    async def _notify_error_middlewares(
        self,
        context: RequestContext,
        error: LjpRequestException,
        middlewares: Sequence[AsyncMiddleware],
    ) -> None:
        for middleware in reversed(middlewares):
            await middleware.on_error(context, error, self)

    async def _send_once(
        self,
        context: RequestContext,
        *,
        attempt: int,
        total_start: float,
    ) -> LjpResponse:

        try:
            adapter_response = await self.adapter.send(context)
        except Exception as exc:
            raise self._map_exception(
                exc,
                context=context,
                retries=attempt,
                elapsed=time.perf_counter() - total_start,
            ) from exc

        self._store_cookies(adapter_response.cookies)
        return self._build_response(
            context=context,
            adapter_response=adapter_response,
            elapsed=time.perf_counter() - total_start,
            retries=attempt,
        )

    def _build_middleware_chain(
        self,
        sender: Callable[[RequestContext], Awaitable[LjpResponse]],
        middlewares: Sequence[AsyncMiddleware],
    ) -> Callable[[RequestContext], Awaitable[LjpResponse]]:

        chain = sender
        for middleware in reversed(middlewares):
            next_handler = chain

            def _make_layer(
                mw: AsyncMiddleware,
                nxt: Callable[[RequestContext], Awaitable[LjpResponse]],
            ) -> Callable[[RequestContext], Awaitable[LjpResponse]]:
                async def _layer(ctx: RequestContext) -> LjpResponse:
                    return await mw.handle(ctx, nxt, self)

                return _layer

            chain = _make_layer(middleware, next_handler)
        return chain

    async def request(
        self,
        method: str,
        url: str,
        *,
        native_session: aiohttp.ClientSession | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        delay = max(0.0, self.config.request.request_delay)
        if delay > 0:
            await asyncio.sleep(delay)
        request_middlewares = kwargs.pop("middlewares", None)
        active_middlewares = (
            list(request_middlewares)
            if request_middlewares is not None
            else list(self.middlewares)
        )

        total_retries = self.config.retry.total if self.retry_middleware else 0
        for attempt in range(total_retries + 1):
            context = self._build_context(
                method,
                url,
                kwargs,
                attempt=attempt,
                native_session=native_session,
            )

            async def _sender(ctx: RequestContext) -> LjpResponse:
                return await self._send_once(
                    ctx,
                    attempt=attempt,
                    total_start=total_start,
                )

            pipeline = self._build_middleware_chain(_sender, active_middlewares)

            try:
                response = await pipeline(context)
            except Exception as exc:
                if isinstance(exc, LjpRequestException):
                    mapped = exc
                else:
                    mapped = self._map_exception(
                        exc,
                        context=context,
                        retries=attempt,
                        elapsed=time.perf_counter() - total_start,
                    )
                    await self._notify_error_middlewares(
                        context,
                        mapped,
                        active_middlewares,
                    )

                if (
                    self.retry_middleware is not None
                    and attempt < total_retries
                    and self.retry_middleware.should_retry_exception(context, mapped)
                ):
                    await self.retry_middleware.wait(attempt)
                    continue

                self._record_failure(mapped.elapsed or 0.0, attempt)
                raise mapped from exc

            if (
                self.retry_middleware is not None
                and attempt < total_retries
                and self.retry_middleware.should_retry_response(context, response)
            ):
                await self.retry_middleware.wait(attempt)
                continue

            self._record_success(response.elapsed, attempt)
            return response

        raise AssertionError("unreachable")

    async def open(self) -> "AsyncSession":
        await self.get_native_session()
        return self

    async def close(self) -> None:
        await self.adapter.close()

    async def __aenter__(self) -> "AsyncSession":
        return await self.open()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


def create_session(
    mode: Literal["sync", "async"] = "sync",
    **options: Any,
) -> SyncSession | AsyncSession:

    logger = options.pop("logger", None)
    middlewares = options.pop("middlewares", None)
    adapter = options.pop("adapter", None)
    config_override = options.pop("config", None)
    base_config = deepcopy(config_override) if config_override else get_request_config()
    config = merge_request_config(base_config, **options)
    if mode == "sync":
        return SyncSession(
            config=config,
            logger=logger,
            adapter=adapter,
            middlewares=middlewares,
        )
    if mode == "async":
        return AsyncSession(
            config=config,
            logger=logger,
            adapter=adapter,
            middlewares=middlewares,
        )
    raise ValueError("mode 蹇呴』鏄?'sync' 鎴?'async'")


__all__ = [
    "AsyncSession",
    "LjpRequestException",
    "LjpResponse",
    "RequestContext",
    "SessionMetrics",
    "SyncSession",
    "create_session",
]


