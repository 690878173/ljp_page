"""requests 同步适配器。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import requests

from ljp_page._core.exceptions import NetworkException, TimeoutException

from .model import BaseHttpAdapter

if TYPE_CHECKING:
    from ...config import LjpConfig
    from ..models import AdapterResult, RequestContext


class RequestsAdapter(BaseHttpAdapter):
    """requests 适配器——管理 Session / 异常映射。"""

    # ── 创建/关闭 session ──

    @staticmethod
    def create_session(
        headers: dict[str, str],
        cookies: dict[str, str],
        config: "LjpConfig",
    ) -> requests.Session:
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)
        session.trust_env = config.trust_env
        session.verify = config.verify_ssl
        proxies = config.proxy.as_requests()
        if proxies:
            session.proxies.update(proxies)
        return session

    @staticmethod
    def close(session: requests.Session | None) -> None:
        if session is not None:
            session.close()

    # ── 发送 ──

    @staticmethod
    def send(
        session: requests.Session,
        context: "RequestContext",
    ) -> "AdapterResult":
        from ..models import AdapterResult

        if context.cookies:
            session.cookies.update(context.cookies)

        passthrough = {
            k: v for k, v in context.extra.items()
            if k != "native_session"
        }

        try:
            resp = session.request(
                context.method,
                context.url,
                params=context.params,
                data=context.data,
                json=context.json_data,
                headers=context.headers,
                timeout=context.timeout,
                allow_redirects=context.allow_redirects,
                verify=context.verify_ssl,
                proxies=context.proxies,
                stream=context.stream,
                **passthrough,
            )
        except Exception as exc:
            raise RequestsAdapter.map_exception(exc, context) from exc

        return AdapterResult(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            content=resp.content,
            encoding=resp.encoding,
            cookies=RequestsAdapter.extract_cookies(session),
        )

    # ── Cookie 提取 ──

    @staticmethod
    def extract_cookies(session: requests.Session) -> dict[str, str]:
        return session.cookies.get_dict()

    # ── Header/Cookie 同步 ──

    @staticmethod
    def update_headers(session: requests.Session | None, headers: dict[str, str]) -> None:
        if session is not None:
            session.headers.clear()
            session.headers.update(headers)

    @staticmethod
    def update_cookies(session: requests.Session | None, cookies: dict[str, str]) -> None:
        if session is not None:
            session.cookies.clear()
            session.cookies.update(cookies)

    # ── 异常映射 ──

    @staticmethod
    def map_exception(exc: Exception, context: "RequestContext") -> Exception:
        if isinstance(exc, (TimeoutException, NetworkException)):
            return exc

        ctx = {"method": context.method, "url": context.url, "attempt": context.attempt}

        if isinstance(exc, requests.Timeout):
            return TimeoutException("同步请求超时", timeout=sum(context.timeout), e=exc, context=ctx)

        if isinstance(exc, requests.exceptions.ProxyError):
            return NetworkException("代理连接失败", url=context.url, e=exc, context=ctx)

        if isinstance(exc, requests.exceptions.SSLError):
            return NetworkException("SSL 连接失败", url=context.url, e=exc, context=ctx)

        status = getattr(getattr(exc, "response", None), "status_code", None)
        if isinstance(exc, requests.RequestException):
            return NetworkException("同步请求失败", url=context.url, status_code=status, e=exc, context=ctx)

        return exc


__all__ = ["RequestsAdapter"]
