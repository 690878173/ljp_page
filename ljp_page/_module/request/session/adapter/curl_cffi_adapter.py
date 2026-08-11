"""curl_cffi 异步适配器——支持 TLS 指纹伪装。"""

from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from ljp_page._core.exceptions import NetworkException, TimeoutException

from .model import BaseHttpAdapter

if TYPE_CHECKING:
    import curl_cffi
    from ...config import LjpConfig
    from ..models import AdapterResult, RequestContext


class CurlCffiAdapter(BaseHttpAdapter):
    """curl_cffi 异步适配器——支持 TLS 指纹伪装。

    用法::

        config = LjpConfig(extra={"impersonate": "chrome120"})
        session = AsyncSession(config, adapter=CurlCffiAdapter())
        resp = await session.get("https://example.com")

    指纹参数既可通过 ``config.extra`` 设置 session 默认值，
    也可在单次请求中覆盖::

        resp = await session.get(url, impersonate="chrome110")
    """

    _FINGERPRINT_KEYS = frozenset({
        "impersonate", "ja3", "akamai", "extra_fp",
        "http_version", "default_headers",
    })

    def __init__(self) -> None:
        self._cookie_store: dict[str, str] = {}

    # ── 超时 ──

    @staticmethod
    def build_timeout(timeout: tuple[float, float]) -> tuple[float, float]:
        """直接返回 (connect, read)，curl_cffi 原生支持。"""
        return float(timeout[0]), float(timeout[1])

    # ── 创建/关闭 session ──

    def create_session(
        self,
        headers: dict[str, str],
        cookies: dict[str, str],
        config: "LjpConfig",
    ) -> "curl_cffi.requests.AsyncSession":
        from curl_cffi import requests as curl_req

        self._cookie_store = dict(cookies)

        session = curl_req.AsyncSession()
        session.closed = session._closed
        session.headers.update(headers)
        for k, v in cookies.items():
            session.cookies.set(k, v)

        # TLS 指纹 —— session 默认，per-request 可覆盖
        impersonate = config.extra.get("impersonate")
        if impersonate:
            session.impersonate = impersonate

        return session

    async def close(
        self,
        session: "curl_cffi.requests.AsyncSession | None",
    ) -> None:
        if session is not None:
            await session.close()

    # ── 发送 ──

    async def send(
        self,
        session: "curl_cffi.requests.AsyncSession",
        context: "RequestContext",
    ) -> "AdapterResult":
        from ..models import AdapterResult

        request_kwargs: dict[str, Any] = {
            "params": context.params,
            "data": context.data,
            "json": context.json_data,
            "headers": context.headers,
            "cookies": context.cookies or None,
            "timeout": self.build_timeout(context.timeout),
            "allow_redirects": context.allow_redirects,
            "verify": context.verify_ssl,
            "proxy": context.proxy_url,
        }

        # TLS 指纹 —— per-request 覆盖 session 级别
        for key in self._FINGERPRINT_KEYS:
            if key in context.extra:
                request_kwargs[key] = context.extra[key]

        try:
            resp = await session.request(
                context.method,
                context.url,
                **request_kwargs,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise self.map_exception(exc, context) from exc

        return AdapterResult(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            content=resp.content,
            encoding=resp.encoding,
            cookies=self.extract_cookies(session),
        )

    # ── Cookie 提取 ──

    @staticmethod
    def extract_cookies(session: "curl_cffi.requests.AsyncSession") -> dict[str, str]:
        """从 curl_cffi session 中提取所有 cookie。"""
        try:
            jar = session.cookies.jar
            return {c.name: c.value for c in jar}
        except Exception:
            return {}

    # ── Header/Cookie 同步 ──

    @staticmethod
    def update_headers(
        session: "curl_cffi.requests.AsyncSession | None",
        headers: dict[str, str],
    ) -> None:
        if session is not None:
            session.headers.clear()
            session.headers.update(headers)

    def update_cookies(
        self,
        session: "curl_cffi.requests.AsyncSession | None",
        cookies: dict[str, str],
    ) -> None:
        self._cookie_store = dict(cookies)
        if session is not None:
            session.cookies.clear()
            for k, v in cookies.items():
                session.cookies.set(k, v)

    # ── 异常映射 ──

    @staticmethod
    def map_exception(exc: Exception, context: "RequestContext") -> Exception:
        import curl_cffi.requests.errors as curl_errors

        if isinstance(exc, (TimeoutException, NetworkException)):
            return exc

        ctx = {"method": context.method, "url": context.url, "attempt": context.attempt}

        if isinstance(exc, asyncio.TimeoutError):
            return TimeoutException("请求超时", timeout=sum(context.timeout), e=exc, context=ctx)


        if isinstance(exc, curl_errors.RequestsError):
            return NetworkException("请求失败", url=context.url, e=exc, context=ctx)

        return exc


__all__ = ["CurlCffiAdapter"]
