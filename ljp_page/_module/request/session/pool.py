"""会话池——管理多个 AsyncSession 实例，支持轮询调度与验证拦截。"""

from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from typing import Any, Mapping

from ljp_page._core.utils.config import SessionPoolConfig
from ljp_page._module.request.verification import AsyncVerification

from .async_client import AsyncSession
from .config import LjpConfig
from .models import LjpResponse

_logger = logging.getLogger(__name__)


class SessionPool:
    """异步会话池——轮询分配 + 验证拦截。"""

    def __init__(
        self,
        config: LjpConfig | None = None,
        *,
        verification: Any = None,
        adapter: Any = None,
    ) -> None:
        self.config = config or LjpConfig(sessionpool=SessionPoolConfig(max_session=1))
        self._adapter = adapter
        self.verification = verification or AsyncVerification(
            result_applier=self.apply_verification_result,
            checker=None,
            handler=None,
        )
        self._sessions: list[AsyncSession] = []
        self._queue: asyncio.Queue[AsyncSession] = asyncio.Queue()
        self._init_lock = asyncio.Lock()
        self._initialized = False

    # ── Headers / Cookies 广播 ──

    def _broadcast(self, attr: str, *args: Any) -> None:
        for s in self._sessions:
            getattr(s, attr)(*args)

    @property
    def headers(self) -> dict[str, str]:
        return deepcopy(self.config.headers)

    @headers.setter
    def headers(self, values: Mapping[str, str]) -> None:
        self.config.headers = dict(values)
        self._broadcast("headers", values)

    @property
    def cookies(self) -> dict[str, str]:
        return deepcopy(self.config.cookies)

    @cookies.setter
    def cookies(self, values: Mapping[str, str]) -> None:
        self.config.cookies = dict(values)
        self._broadcast("cookies", values)

    def update_headers(self, values: Mapping[str, str]) -> None:
        self.config.headers.update(dict(values))
        self._broadcast("update_headers", values)

    def update_cookies(self, values: Mapping[str, str]) -> None:
        self.config.cookies.update(dict(values))
        self._broadcast("update_cookies", values)

    def clear_cookies(self) -> None:
        self.config.cookies.clear()
        self._broadcast("clear_cookies")

    def apply_verification_result(self, result: Any, context: Any = None) -> None:
        if not isinstance(result, Mapping):
            return
        if headers := result.get("headers"):
            self.update_headers(headers)
        if cookies := result.get("cookies"):
            self.update_cookies(cookies)

    # ── 初始化 ──

    async def _ensure_init(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            for _ in range(self.config.sessionpool.max_session):
                s = AsyncSession(config=self.config, adapter=self._adapter)
                await s.ensure_session()
                self._sessions.append(s)
                self._queue.put_nowait(s)
            self._initialized = True

    # ── 请求 ──

    async def request(
        self,
        method: str,
        url: str,
        *,
        session: AsyncSession | None = None,
        verify_response: bool = True,
        verify_max_retries: int | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        if not self._initialized:
            await self._ensure_init()

        async def _send() -> LjpResponse:
            s = session or await self._queue.get()
            try:
                return await s.request(method, url, **kwargs)
            finally:
                if session is None:
                    await self._release(s)

        return await self.verification.run(
            _send,
            verify_response=verify_response,
            max_retries=verify_max_retries,
        )

    async def _release(self, s: AsyncSession) -> None:
        if not s.closed:
            await self._queue.put(s)

    # ── 便捷方法 ──

    async def get(self, url: str, *, session: AsyncSession | None = None, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url, session=session, **kwargs)

    async def post(self, url: str, *, session: AsyncSession | None = None, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url, session=session, **kwargs)

    async def put(self, url: str, *, session: AsyncSession | None = None, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url, session=session, **kwargs)

    async def delete(self, url: str, *, session: AsyncSession | None = None, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url, session=session, **kwargs)

    # ── 生命周期 ──

    async def close(self) -> None:
        for s in self._sessions:
            await s.close()
        self._sessions.clear()
        while not self._queue.empty():
            self._queue.get_nowait()
        self._initialized = False

    async def __aenter__(self) -> "SessionPool":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


__all__ = ["SessionPool"]
