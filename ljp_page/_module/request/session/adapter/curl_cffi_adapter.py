"""curl-cffi asynchronous backend adapter."""

from __future__ import annotations

import asyncio
from typing import Mapping

from curl_cffi import requests as curl_requests
from curl_cffi.requests import errors

from ljp_page._core.exceptions import LjpBaseException, NetworkException, TimeoutException

from .model import BaseAdapter
from ..config import SessionConfig
from ..models import RequestArgs, RequestsReponse


class CurlCffiAdapter(BaseAdapter):
    """Owns curl-cffi's async session, including its native cookie jar."""

    is_async = True

    def __init__(self) -> None:
        self._session: curl_requests.AsyncSession | None = None
        self._cookies: dict[str, str] = {}

    @property
    def closed(self) -> bool:
        return self._session is None or bool(getattr(self._session, "closed", getattr(self._session, "_closed", False)))

    def open(self, config: SessionConfig, cookies: Mapping[str, str]) -> None:
        if not self.closed:
            return
        self._session = curl_requests.AsyncSession()
        self._session.headers.clear()  # RequestArgs.headers is the only header source.
        impersonate = config.Request.extra.get("impersonate", config.extra.get("impersonate"))
        if impersonate:
            self._session.impersonate = impersonate
        self._session.cookies.update(self._cookies)

    async def close(self) -> None:
        if self._session is not None:
            self._cookies = self.get_cookies()
            await self._session.close()
        self._session = None

    async def send(self, request: RequestArgs) -> RequestsReponse:
        if self.closed:
            raise RuntimeError("CurlCffiAdapter is not open")
        try:
            response = await self._session.request(
                method=request.method,
                url=request.url,
                params=request.params,
                data=request.data,
                json=request.json_data,
                headers=dict(request.headers),
                cookies=dict(request.cookies) if request.cookies else None,
                timeout=request.timeout,
                allow_redirects=request.allow_redirects,
                verify=request.verify_ssl,
                proxy=request.proxy_url,
                stream=request.stream,
                **dict(request.extra),
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise self.map_exception(exc, request) from exc

        return RequestsReponse(
            request_args=request,
            status_code=response.status_code,
            url=str(response.url),
            headers=dict(response.headers),
            content=response.content,
            encoding=response.encoding,
            cookies=self.get_cookies(),
            history=tuple(str(item.url) for item in response.history),
        )

    def get_cookies(self) -> dict[str, str]:
        if self.closed:
            return dict(self._cookies)
        try:
            return {cookie.name: cookie.value for cookie in self._session.cookies.jar}
        except Exception:
            return dict(self._cookies)

    def set_cookies(self, cookies: Mapping[str, str]) -> None:
        self._cookies = dict(cookies)
        if not self.closed:
            self._session.cookies.clear()
            self._session.cookies.update(self._cookies)

    def update_cookies(self, cookies: Mapping[str, str]) -> None:
        self._cookies.update(cookies)
        if not self.closed:
            self._session.cookies.update(cookies)

    def clear_cookies(self) -> None:
        self._cookies.clear()
        if not self.closed:
            self._session.cookies.clear()

    @staticmethod
    def map_exception(exc: Exception, request: RequestArgs) -> Exception:
        if isinstance(exc, LjpBaseException):
            return exc
        context = {"method": request.method, "url": request.url, "attempt": request.attempt}
        if isinstance(exc, asyncio.TimeoutError) or "timeout" in type(exc).__name__.lower():
            return TimeoutException("HTTP request timed out", timeout=sum(request.timeout), context=context)
        if isinstance(exc, errors.RequestsError):
            return NetworkException("HTTP request failed", url=request.url, context=context)
        return NetworkException("HTTP backend failed", url=request.url, context=context)


__all__ = ["CurlCffiAdapter"]
