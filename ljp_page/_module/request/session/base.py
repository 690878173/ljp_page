from __future__ import annotations

import asyncio
import threading
import uuid
from abc import abstractmethod, ABC
from copy import deepcopy
from typing import Any, Mapping
from urllib.parse import urlparse

import aiohttp
import requests

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._core.constants.request import Request_str
from ljp_page._core.utils.config import TimeoutConfig
from ljp_page._core.exceptions import NetworkException, TimeoutException
from ljp_page._core.logger import Logger

from .config import AdapterResponse, LjpConfig, LjpResponse, RequestContext



class RequestModuleBase(Ljp_BaseClass_Logger,ABC):
    def __init__(self, config: LjpConfig, logger: Logger = None):
        super().__init__()
        self.config = config
        self.logger = logger

        self._state_lock = threading.RLock()

    @property
    def headers(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self.config.request.headers)

    @headers.setter
    def headers(self, headers: dict[str, str]):
        with self._state_lock:
            self.config.request.headers = headers

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
        raise TypeError(f"不支持的 timeout 类型: {type(timeout).__name__}")

    def _resolve_url(self, url: str) -> str:
        return url

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
        custom_headers = request_kwargs.pop(Request_str.headers, None) or {}
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
            status=adapter_response.status_code,
            headers=dict(adapter_response.headers),
            encoding=adapter_response.encoding,
            content=adapter_response.content,
            elapsed=elapsed,
            retries=retries,
            request=context,
        )


class AsyncRequestModuleBase(RequestModuleBase,ABC):


    @staticmethod
    def _extract_cookies(session: aiohttp.ClientSession) -> dict[str, str]:
        return {
            cookie.key: cookie.value
            for cookie in session.cookie_jar.__iter__()
        }

    @staticmethod
    def _map_exception(exc: Exception, context: RequestContext) -> Exception:
        if isinstance(exc, (TimeoutException, NetworkException)):
            return exc

        common_context = {
            "method": context.method,
            "url": context.url,
            "attempt": context.attempt,
        }

        if isinstance(exc, asyncio.TimeoutError):
            return TimeoutException(
                "异步请求超时",
                timeout=sum(context.timeout),
                e=exc,
                context=common_context,
            )

        if isinstance(exc, aiohttp.ClientProxyConnectionError):
            return NetworkException(
                "代理连接失败",
                url=context.url,
                e=exc,
                context=common_context,
            )

        if isinstance(exc, aiohttp.ClientSSLError):
            return NetworkException(
                "SSL 连接失败",
                url=context.url,
                e=exc,
                context=common_context,
            )

        status_code = getattr(exc, "status", None)
        if isinstance(exc, aiohttp.ClientError):
            return NetworkException(
                "异步请求失败",
                url=context.url,
                status_code=status_code,
                e=exc,
                context=common_context,
            )
        return exc

    @abstractmethod
    async def request(self, method: str, url: str, **kwargs: Any) -> LjpResponse:
        pass

    async def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url, **kwargs)


class SyncRequestModuleBase(RequestModuleBase):
    def _resolve_request_session(
        self,
        native_session: requests.Session | None,
    ) -> requests.Session:
        return native_session or self.ensure_session()

    def ensure_session(self) -> requests.Session:
        raise NotImplementedError()

    @staticmethod
    def _extract_cookies(session: requests.Session) -> dict[str, str]:
        return session.cookies.get_dict()

    def _map_exception(self, exc: Exception, context: RequestContext) -> Exception:
        if isinstance(exc, (TimeoutException, NetworkException)):
            return exc

        common_context = {
            "method": context.method,
            "url": context.url,
            "attempt": context.attempt,
        }

        if isinstance(exc, requests.Timeout):
            return TimeoutException(
                "同步请求超时",
                timeout=sum(context.timeout),
                e=exc,
                context=common_context,
            )

        if isinstance(exc, requests.exceptions.ProxyError):
            return NetworkException(
                "代理连接失败",
                url=context.url,
                e=exc,
                context=common_context,
            )

        if isinstance(exc, requests.exceptions.SSLError):
            return NetworkException(
                "SSL 连接失败",
                url=context.url,
                e=exc,
                context=common_context,
            )

        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if isinstance(exc, requests.RequestException):
            return NetworkException(
                "同步请求失败",
                url=context.url,
                status_code=status_code,
                e=exc,
                context=common_context,
            )

        return exc

    def request(self, method: str, url: str, **kwargs: Any) -> LjpResponse:
        raise NotImplementedError()

    def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("DELETE", url, **kwargs)


__all__ = ["RequestModuleBase", "AsyncRequestModuleBase", "SyncRequestModuleBase"]


