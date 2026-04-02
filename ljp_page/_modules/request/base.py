
from __future__ import annotations

import uuid
from typing import Any, Mapping
import threading
from copy import deepcopy
from urllib.parse import urlparse, urljoin

from ljp_page._modules.logger import Logger
from ljp_page._core.base import AsyncModuleBase, ModuleBase, SyncModuleBase
from ljp_page._core.config import TimeoutConfig
from ljp_page._modules.request.Config.models import LjpResponse, SessionMetrics
from .Config.config import merge_request_config, LjpConfig
from ljp_page._modules.request.Config.models import RequestContext
from .adapters import AdapterResponse

class RequestModuleBase(ModuleBase):
    """请求模块公共基类。"""

    module_name = "request"

    def __init__(self, config: LjpConfig, logger: Any = None) -> None:
        super().__init__(logger=logger)
        self.config = config
        self.metrics = SessionMetrics()
        self._state_lock = threading.RLock()
        self._cookie_store = deepcopy(self.config.request.cookies)
        self.logger = logger or Logger(self.config.log)
        if isinstance(self.logger, Logger):
            self.logger.set_enabled_levels(self.config.log.enabled_levels)
            self.logger.set_default_level(self.config.log.default_level)

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
        raise TypeError(f"不支持的 timeout 类型: {type(timeout).__name__}")

    def _resolve_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        if not self.config.request.base_url:
            raise ValueError("相对路径请求需要配置 base_url")
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


class SyncRequestModuleBase(RequestModuleBase, SyncModuleBase):
    """同步请求模块基类。"""
    def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("DELETE", url, **kwargs)


class AsyncRequestModuleBase(RequestModuleBase, AsyncModuleBase):
    """异步请求模块基类。"""

    async def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url, **kwargs)


