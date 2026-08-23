"""aiohttp backend adapter."""

from __future__ import annotations

import asyncio
from typing import Mapping

import aiohttp

from ljp_page._core.exceptions import LjpBaseException, NetworkException, TimeoutException

from .model import BaseAdapter
from ..config import SessionConfig
from ..models import RequestArgs, RequestsReponse


class AiohttpAdapter(BaseAdapter):
    """Owns an aiohttp client and its CookieJar."""

    is_async = True

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._cookies: dict[str, str] = {}

    @property
    def closed(self) -> bool:
        return self._session is None or self._session.closed

    def open(self, config: SessionConfig, cookies: Mapping[str, str]) -> None:

        if not self.closed:
            return
        jar = aiohttp.CookieJar(unsafe=True)
        jar.update_cookies(self._cookies)
        connector = aiohttp.TCPConnector(
            limit=config.SessionPool.max_session,
            limit_per_host=config.SessionPool.max_connections_per_host,
            keepalive_timeout=config.SessionPool.max_keepalive_connections,
        )
        self._session = aiohttp.ClientSession(
            headers={},  # Headers are supplied from RequestArgs for every request.
            cookie_jar=jar,
            connector=connector,
            trust_env=config.Request.trust_env,
        )

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            self._cookies = self.get_cookies()
            await self._session.close()
        self._session = None

    @staticmethod
    def _timeout(value: tuple[float, float]) -> aiohttp.ClientTimeout:
        connect, read = value
        return aiohttp.ClientTimeout(total=connect + read, connect=connect, sock_connect=connect, sock_read=read)

    async def send(self, request: RequestArgs) -> RequestsReponse:

        if self.closed:
            raise RuntimeError("AiohttpAdapter is not open")
        try:
            async with self._session.request(
                method=request.method,
                url=request.url,
                params=request.params,
                data=request.data,
                json=request.json_data,
                headers=dict(request.headers),
                cookies=dict(request.cookies) if request.cookies else None,
                timeout=self._timeout(request.timeout),
                allow_redirects=request.allow_redirects,
                ssl=request.verify_ssl,
                proxy=request.proxy_url,
                **dict(request.extra),
            ) as response:
                return RequestsReponse(
                    request_args=request,
                    status_code=response.status,
                    url=str(response.url),
                    headers=dict(response.headers),
                    content=await response.read(),
                    encoding=response.charset,
                    cookies=self.get_cookies(),
                    history=tuple(str(item.url) for item in response.history),
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise self.map_exception(exc, request) from exc

    def get_cookies(self) -> dict[str, str]:
        if self.closed:
            return dict(self._cookies)
        return {cookie.key: cookie.value for cookie in self._session.cookie_jar}

    def set_cookies(self, cookies: Mapping[str, str]) -> None:
        self._cookies = dict(cookies)
        if not self.closed:
            self._session.cookie_jar.clear()
            self._session.cookie_jar.update_cookies(self._cookies)

    def update_cookies(self, cookies: Mapping[str, str]) -> None:
        self._cookies.update(cookies)
        if not self.closed:
            self._session.cookie_jar.update_cookies(cookies)

    def clear_cookies(self) -> None:
        self._cookies.clear()
        if not self.closed:
            self._session.cookie_jar.clear()

    @staticmethod
    def map_exception(exc: Exception, request: RequestArgs) -> Exception:
        if isinstance(exc, LjpBaseException):
            return exc
        context = {"method": request.method, "url": request.url, "attempt": request.attempt}
        if isinstance(exc, (asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
            return TimeoutException("HTTP request timed out", timeout=sum(request.timeout), context=context)
        if isinstance(exc, aiohttp.ClientError):
            return NetworkException("HTTP request failed", url=request.url, context=context)
        return NetworkException("HTTP backend failed", url=request.url, context=context)


__all__ = ["AiohttpAdapter"]
