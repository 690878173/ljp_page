"""aiohttp 异步适配器。"""

from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

import aiohttp

from ljp_page._core.exceptions import NetworkException, TimeoutException
from ljp_page._core.utils.config import TimeoutConfig

from .model import BaseHttpAdapter

if TYPE_CHECKING:
    from ...config import LjpConfig
    from ..models import AdapterResult, RequestContext


class AiohttpAdapter(BaseHttpAdapter):
    """aiohttp 适配器——管理 CookieJar / ClientSession / 异常映射。"""

    def __init__(self) -> None:
        self._jar: aiohttp.CookieJar = None

    # ── CookieJar ──

    def create_cookie_jar(self, cookies: dict[str, str]) -> aiohttp.CookieJar:
        self._jar = aiohttp.CookieJar(unsafe=True)
        self._jar.update_cookies(cookies)
        return self._jar

    # ── 超时 ──

    @staticmethod
    def build_timeout(timeout: tuple[float, float] | TimeoutConfig) -> aiohttp.ClientTimeout:
        if isinstance(timeout, TimeoutConfig):
            connect = timeout.connect
            read = timeout.read
        elif isinstance(timeout, tuple):
            connect, read = timeout
        else:
            raise ValueError("timeout 参数错误")
        return aiohttp.ClientTimeout(
            total=connect + read,
            connect=connect,
            sock_connect=connect,
            sock_read=read,
        )

    # ── 创建/关闭 session ──

    def create_session(
        self,
        headers: dict[str, str],
        cookies: dict[str, str],
        config: "LjpConfig",
    ) -> aiohttp.ClientSession:
        jar = self.create_cookie_jar(cookies)
        connector = aiohttp.TCPConnector(
            limit=config.sessionpool.max_session,
            limit_per_host=config.sessionpool.max_connections_per_host,
            keepalive_timeout=config.sessionpool.max_keepalive_connections,
            ssl=config.verify_ssl,
        )
        return aiohttp.ClientSession(
            headers=headers,
            cookie_jar=jar,
            connector=connector,
            connector_owner=True,
            timeout=self.build_timeout(config.timeout),
            trust_env=config.trust_env,
        )

    async def close(self, session: aiohttp.ClientSession | None) -> None:
        if session is not None and not session.closed:
            await session.close()

    # ── 发送 ──

    async def send(
        self,
        session: aiohttp.ClientSession,
        context: "RequestContext",
    ) -> "AdapterResult":
        from ..models import AdapterResult

        if context.cookies:
            session.cookie_jar.update_cookies(context.cookies)

        try:
            async with session.request(
                context.method,
                context.url,
                params=context.params,
                data=context.data,
                json=context.json_data,
                headers=context.headers,
                timeout=self.build_timeout(context.timeout),
                allow_redirects=context.allow_redirects,
                ssl=context.verify_ssl,
                proxy=context.proxy_url,
            ) as resp:
                content = await resp.read()
                return AdapterResult(
                    status_code=resp.status,
                    headers=dict(resp.headers),
                    content=content,
                    encoding=resp.charset,
                    cookies=self.extract_cookies(session),
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise self.map_exception(exc, context) from exc

    # ── Cookie 提取 ──

    @staticmethod
    def extract_cookies(session: aiohttp.ClientSession) -> dict[str, str]:
        return {
            c.key: c.value
            for c in session.cookie_jar.__iter__()
        }

    # ── Header/Cookie 同步 ──

    @staticmethod
    def update_headers(session: aiohttp.ClientSession | None, headers: dict[str, str]) -> None:
        if session and not session.closed:
            session.headers.clear()
            session.headers.update(headers)

    def update_cookies(
        self,
        session: aiohttp.ClientSession | None,
        cookies: dict[str, str],
    ) -> None:
        if self._jar is not None:
            self._jar.clear()
            self._jar.update_cookies(cookies)
        if session and not session.closed:
            session.cookie_jar.clear()
            session.cookie_jar.update_cookies(cookies)

    # ── 异常映射 ──

    @staticmethod
    def map_exception(exc: Exception, context: "RequestContext") -> Exception:
        if isinstance(exc, (TimeoutException, NetworkException)):
            return exc

        ctx = {"method": context.method, "url": context.url, "attempt": context.attempt}

        if isinstance(exc, asyncio.TimeoutError):
            return TimeoutException("异步请求超时", timeout=sum(context.timeout), e=exc, context=ctx)

        if isinstance(exc, aiohttp.ClientProxyConnectionError):
            return NetworkException("代理连接失败", url=context.url, e=exc, context=ctx)

        if isinstance(exc, aiohttp.ClientSSLError):
            return NetworkException("SSL 连接失败", url=context.url, e=exc, context=ctx)

        status = getattr(exc, "status", None)
        if isinstance(exc, aiohttp.ClientError):
            return NetworkException("异步请求失败", url=context.url, status_code=status, e=exc, context=ctx)

        return exc


__all__ = ["AiohttpAdapter"]
