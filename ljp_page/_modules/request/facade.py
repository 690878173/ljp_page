from __future__ import annotations

import aiohttp
import requests
from copy import deepcopy
from typing import Any, Literal

from .Config.config import get_request_config, merge_request_config, LjpConfig
from .Config.models import LjpResponse,LjpRequestException
from .async_session import AsyncSession
from .sync_session import SyncSession

class Requests:
    """对外统一请求入口。"""

    def __init__(self, config: LjpConfig | None = None, logger: Any = None):
        self.logger = logger
        if config is None:
            self.config = get_request_config()
        elif isinstance(config, LjpConfig):
            self.config = config
        else:
            raise TypeError("config must be LjpConfig")
        self._sync_wrapper: SyncSession | None = None
        self._async_wrapper: AsyncSession | None = None

    def _build_sync_wrapper(self, **overrides: Any) -> SyncSession:
        merged = merge_request_config(self.config, **overrides) if overrides else self.config
        wrapper = create_session(
            "sync",
            config=merged,
            logger=self.logger,
        )
        self._sync_wrapper = wrapper
        return wrapper

    def _build_async_wrapper(self, **overrides: Any) -> AsyncSession:
        merged = merge_request_config(self.config, **overrides) if overrides else self.config
        wrapper = create_session(
            "async",
            config=merged,
            logger=self.logger,
        )
        self._async_wrapper = wrapper
        return wrapper

    @staticmethod
    def _normalize_return_type(return_type: str | None, read_content: bool) -> str:
        if read_content:
            return "content"
        return return_type or "response"

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
    def _build_overrides(
        *,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        verify_ssl: bool | None = None,
        max_connections: int | None = None,
        max_connections_per_host: int | None = None,
    ) -> dict[str, Any]:
        overrides: dict[str, Any] = {}
        request_override: dict[str, Any] = {}

        if cookies is not None:
            request_override["cookies"] = cookies
        if headers is not None:
            request_override["headers"] = headers
        if verify_ssl is not None:
            request_override["verify_ssl"] = verify_ssl

        if request_override:
            overrides["request"] = request_override

        if max_connections is not None and max_connections_per_host is not None:
            overrides["pool"] = {
                "max_connections": max_connections,
                "max_connections_per_host": max_connections_per_host,
            }

        return overrides

    @staticmethod
    def _split_sync_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, str]:
        session = kwargs.pop("session", None)
        if args and isinstance(args[0], (requests.Session, SyncSession)):
            if len(args) < 2:
                raise ValueError("缺少 URL 参数")
            kwargs.pop("url", None)
            return args[0], args[1]
        if args:
            kwargs.pop("url", None)
            return session, args[0]
        if "url" not in kwargs:
            raise ValueError("缺少 URL 参数")
        return session, kwargs.pop("url")

    @staticmethod
    def _split_async_args(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, str]:
        session = kwargs.pop("session", None)
        if args and isinstance(args[0], (aiohttp.ClientSession, AsyncSession)):
            if len(args) < 2:
                raise ValueError("缺少 URL 参数")
            kwargs.pop("url", None)
            return args[0], args[1]
        if args:
            kwargs.pop("url", None)
            return session, args[0]
        if "url" not in kwargs:
            raise ValueError("缺少 URL 参数")
        return session, kwargs.pop("url")

    def create_session(
        self,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        wrapper: bool = False,
    ) -> requests.Session | SyncSession:
        overrides = self._build_overrides(cookies=cookies, headers=headers)
        runtime = self._build_sync_wrapper(**overrides)
        return runtime if wrapper else runtime.get_native_session()

    async def async_create_session(
        self,
        limit: int = 0,
        limit_per_host: int = 100,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        verify_ssl: bool | None = None,
        wrapper: bool = False,
    ) -> aiohttp.ClientSession | AsyncSession:
        max_connections = limit if limit > 0 else limit_per_host
        pool_max = max_connections if (max_connections > 0 or limit_per_host > 0) else None
        pool_per_host = limit_per_host if (max_connections > 0 or limit_per_host > 0) else None
        overrides = self._build_overrides(
            cookies=cookies,
            headers=headers,
            verify_ssl=verify_ssl,
            max_connections=pool_max,
            max_connections_per_host=pool_per_host,
        )

        runtime = self._build_async_wrapper(**overrides)
        await runtime.open()
        return runtime if wrapper else await runtime.get_native_session()

    def _run_sync(self, method: str, session: Any, url: str, **kwargs: Any) -> LjpResponse:
        if isinstance(session, SyncSession):
            return session.request(method, url, **kwargs)
        runtime = self._sync_wrapper or self._build_sync_wrapper()
        if isinstance(session, requests.Session):
            return runtime.request(method, url, native_session=session, **kwargs)
        return runtime.request(method, url, **kwargs)

    async def _run_async(self, method: str, session: Any, url: str, **kwargs: Any) -> LjpResponse:
        if isinstance(session, AsyncSession):
            return await session.request(method, url, **kwargs)
        runtime = self._async_wrapper or self._build_async_wrapper()
        if isinstance(session, aiohttp.ClientSession):
            return await runtime.request(method, url, native_session=session, **kwargs)
        return await runtime.request(method, url, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_sync_args(args, kwargs)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        kwargs.pop("res_encoding", None)
        response = self._run_sync("GET", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    def post(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_sync_args(args, kwargs)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        kwargs.pop("res_encoding", None)
        response = self._run_sync("POST", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    async def async_get(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_async_args(args, kwargs)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        kwargs.pop("res_encoding", None)
        response = await self._run_async("GET", session, url, **kwargs)
        return self._unwrap_response(response, return_type)

    async def async_post(self, *args: Any, **kwargs: Any) -> Any:
        session, url = self._split_async_args(args, kwargs)
        return_type = self._normalize_return_type(
            kwargs.pop("return_type", None),
            kwargs.pop("read_content", False),
        )
        kwargs.pop("res_encoding", None)
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
        raise TypeError(f"不支持的 session 类型: {type(session).__name__}")

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
        raise TypeError(f"不支持的 session 类型: {type(session).__name__}")

    @staticmethod
    def get_headers(session: Any) -> dict[str, str]:
        if isinstance(session, (SyncSession, AsyncSession)):
            return session.headers
        if isinstance(session, (requests.Session, aiohttp.ClientSession)):
            return dict(session.headers)
        raise TypeError(f"不支持的 session 类型: {type(session).__name__}")


def create_session(
    mode: Literal["sync", "async"] = "sync",
    **options: Any,
) -> SyncSession | AsyncSession:
    """创建同步或异步会话。"""

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
    raise ValueError("mode 必须是 'sync' 或 'async'")
def async_create_session(
    **options: Any,
) -> SyncSession | AsyncSession:
    """创建同步或异步会话。"""
    return create_session(mode='async',**options)

def sync_create_session(
    **options: Any,
) -> SyncSession | AsyncSession:
    """创建同步或异步会话。"""
    return create_session(mode='sync',**options)
__all__ = [
    "AsyncSession",
    "LjpRequestException",
    "LjpResponse",
    "Requests",
    "SyncSession",
    "create_session",
    'async_create_session',
    "sync_create_session",
]


