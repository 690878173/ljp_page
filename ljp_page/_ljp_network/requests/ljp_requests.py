"""Public request facade and backwards-compatible wrapper APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import aiohttp
import requests
from lxml import etree

from ..._ljp_config.request_config.request_config import get_request_config
from .req import (
    AsyncSession,
    LjpRequestException,
    LjpResponse,
    SessionHooks,
    SyncSession,
    create_session,
)


@dataclass
class RequestsConfig:
    """Compatibility config used by the legacy Requests facade."""

    proxy_list: list[str] | None = None
    max_retries: int = 3
    timeout: float = 10.0
    cookies: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    delay: float = 0.0
    verify_ssl: bool = True
    allow_redirects: bool = True
    base_url: str = ""


class Requests:
    """Legacy facade that delegates to the new unified session runtime."""

    Config = RequestsConfig

    def __init__(self, config: RequestsConfig | None = None, logger: Any = None):
        self.logger = logger
        self.config = config or self.Config()
        self._sync_wrapper: SyncSession | None = None
        self._async_wrapper: AsyncSession | None = None

    def _compat_options(self) -> dict[str, Any]:
        proxy = None
        if self.config.proxy_list:
            first_proxy = self.config.proxy_list[0]
            proxy = {"http": first_proxy, "https": first_proxy}
        return {
            "base_url": self.config.base_url,
            "verify_ssl": self.config.verify_ssl,
            "allow_redirects": self.config.allow_redirects,
            "headers": self.config.headers,
            "cookies": self.config.cookies,
            "request_delay": self.config.delay,
            "retry": {"total": self.config.max_retries},
            "timeout": {"connect": self.config.timeout, "read": self.config.timeout},
            "proxy": proxy,
        }

    def _build_sync_wrapper(self, **overrides: Any) -> SyncSession:
        wrapper = create_session(
            "sync",
            config=get_request_config(**self._compat_options()),
            logger=self.logger,
            **overrides,
        )
        self._sync_wrapper = wrapper
        return wrapper

    def _build_async_wrapper(self, **overrides: Any) -> AsyncSession:
        wrapper = create_session(
            "async",
            config=get_request_config(**self._compat_options()),
            logger=self.logger,
            **overrides,
        )
        self._async_wrapper = wrapper
        return wrapper

    @staticmethod
    def _normalize_return_type(
        return_type: str | None,
        read_content: bool,
    ) -> str:
        if read_content:
            return "content"
        return return_type or "text"

    @staticmethod
    def _unwrap_response(response: LjpResponse, return_type: str) -> Any:
        if return_type == "response":
            return response
        if return_type == "json":
            return response.json()
        if return_type == "content":
            return response.binary
        return response.text

    @staticmethod
    def _split_sync_args(*args: Any, **kwargs: Any) -> tuple[Any, str]:
        session = kwargs.pop("session", None)
        if args and isinstance(args[0], (requests.Session, SyncSession)):
            if len(args) < 2:
                raise ValueError("Missing URL argument")
            return args[0], args[1]
        if args:
            return session, args[0]
        if "url" not in kwargs:
            raise ValueError("Missing URL argument")
        return session, kwargs.pop("url")

    @staticmethod
    def _split_async_args(*args: Any, **kwargs: Any) -> tuple[Any, str]:
        session = kwargs.pop("session", None)
        if args and isinstance(args[0], (aiohttp.ClientSession, AsyncSession)):
            if len(args) < 2:
                raise ValueError("Missing URL argument")
            return args[0], args[1]
        if args:
            return session, args[0]
        if "url" not in kwargs:
            raise ValueError("Missing URL argument")
        return session, kwargs.pop("url")

    def create_session(
        self,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        wrapper: bool = False,
    ) -> requests.Session | SyncSession:
        runtime = self._build_sync_wrapper(
            cookies=cookies or {},
            headers=headers or {},
        )
        return runtime if wrapper else runtime.get_native_session()

    async def async_create_session(
        self,
        limit: int = 0,
        limit_per_host: int = 100,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        verify_ssl: bool = True,
        wrapper: bool = False,
    ) -> aiohttp.ClientSession | AsyncSession:
        runtime = self._build_async_wrapper(
            cookies=cookies or {},
            headers=headers or {},
            verify_ssl=verify_ssl,
            pool={
                "max_connections": limit or limit_per_host,
                "max_connections_per_host": limit_per_host,
            },
        )
        await runtime.open()
        return runtime if wrapper else await runtime.get_native_session()

    def _run_sync(self, method: str, session: Any, url: str, **kwargs: Any) -> LjpResponse:
        if isinstance(session, SyncSession):
            return session.request(method, url, **kwargs)
        runtime = self._sync_wrapper or self._build_sync_wrapper()
        if isinstance(session, requests.Session):
            return runtime.request(method, url, native_session=session, **kwargs)
        return runtime.request(method, url, **kwargs)

    async def _run_async(
        self,
        method: str,
        session: Any,
        url: str,
        **kwargs: Any,
    ) -> LjpResponse:
        if isinstance(session, AsyncSession):
            return await session.request(method, url, **kwargs)
        runtime = self._async_wrapper or self._build_async_wrapper()
        if isinstance(session, aiohttp.ClientSession):
            return await runtime.request(method, url, native_session=session, **kwargs)
        return await runtime.request(method, url, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_sync_args(*args, **kwargs)
        kwargs.pop("res_encoding", None)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        response = self._run_sync("GET", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_sync_args(*args, **kwargs)
        kwargs.pop("res_encoding", None)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        response = self._run_sync("POST", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    async def async_get(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_async_args(*args, **kwargs)
        kwargs.pop("res_encoding", None)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        response = await self._run_async("GET", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    async def async_post(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_async_args(*args, **kwargs)
        kwargs.pop("res_encoding", None)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        response = await self._run_async("POST", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    @staticmethod
    def get_cookies(session: Any) -> dict[str, str]:
        if isinstance(session, SyncSession):
            return session.cookies
        if isinstance(session, AsyncSession):
            return session.cookies
        if isinstance(session, requests.Session):
            return session.cookies.get_dict()
        if isinstance(session, aiohttp.ClientSession):
            return {cookie.key: cookie.value for cookie in session.cookie_jar}
        raise TypeError(f"Unsupported session type: {type(session).__name__}")

    @staticmethod
    def update_cookies(session: Any, cookies: dict[str, str]) -> None:
        if isinstance(session, (SyncSession, AsyncSession)):
            session.update_cookies(cookies)
            return
        if isinstance(session, requests.Session):
            session.cookies.update(cookies)
            return
        if isinstance(session, aiohttp.ClientSession):
            session.cookie_jar.update_cookies(cookies)
            return
        raise TypeError(f"Unsupported session type: {type(session).__name__}")

    @staticmethod
    def get_headers(session: Any) -> dict[str, str]:
        if isinstance(session, (SyncSession, AsyncSession)):
            return session.headers
        if isinstance(session, (requests.Session, aiohttp.ClientSession)):
            return dict(session.headers)
        raise TypeError(f"Unsupported session type: {type(session).__name__}")


TBSession = SyncSession
YBSession = AsyncSession
TBRequests = SyncSession
YBRequests = AsyncSession


class Html:
    """Small HTML helper collection retained for backwards compatibility."""

    @staticmethod
    def html_drop_script(html_content: str) -> str:
        html_content = html_content.replace("<script", "<!-- <script")
        html_content = html_content.replace("</script>", "</script> -->")
        return html_content

    @staticmethod
    def save_file(html_content: str, path: str = "test.html") -> None:
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(Html.html_drop_script(html_content))

    @staticmethod
    def strip(text: str) -> str:
        return (
            text.strip()
            .replace("\xa0", "")
            .replace("\r", "")
            .replace("\n", "")
            .replace("\t", "")
        )

    @staticmethod
    def ls_strip(values: list[str]) -> str:
        return "\n".join(
            Html.strip(item)
            for item in values
            if item is not None and isinstance(item, str) and Html.strip(item)
        )

    @staticmethod
    def str_to_html(res: str) -> Any:
        return etree.HTML(res)

    @staticmethod
    def drop_xml(html_str: str) -> Any:
        html = html_str.replace('<?xml version="1.0" encoding="UTF-8" ?>', "")
        return Html.str_to_html(html)

    @staticmethod
    def xpath_ls(html: Any, xpath: str) -> str:
        return "\n".join(html.xpath(xpath))


__all__ = [
    "AsyncSession",
    "Html",
    "LjpRequestException",
    "LjpResponse",
    "Requests",
    "SessionHooks",
    "SyncSession",
    "TBRequests",
    "TBSession",
    "YBRequests",
    "YBSession",
    "create_session",
]
