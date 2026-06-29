# 05-24-22-09-57
from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping

from ljp_page._module.request.session.config import LjpResponse

if TYPE_CHECKING:
    from ljp_page._module.request.session.session import ASession, AsyncSession


@dataclass(slots=True)
class VerificationContext:
    """响应验证上下文，供外部验证函数读取请求信息并更新会话状态。"""

    owner: "ASession"
    session: "AsyncSession"
    response: LjpResponse
    method: str
    url: str
    request_kwargs: dict[str, Any] = field(default_factory=dict)
    verify_attempt: int = 0
    version: int = 0


@dataclass(slots=True)
class GateVerificationContext:
    """通用验证上下文，避免每个请求点重复编写三参 context_factory。"""

    response: Any
    verify_attempt: int = 0
    version: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        if key in {"response", "verify_attempt", "version", "extra"}:
            return getattr(self, key)
        return self.extra[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key in {"response", "verify_attempt", "version", "extra"}:
            return getattr(self, key)
        return self.extra.get(key, default)

    def __getattr__(self, key: str) -> Any:
        try:
            return self.extra[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class AsyncVerificationGate:
    """通用异步验证门闸，适用于 aiohttp、Playwright/CDP 等任意请求来源。"""

    def __init__(
        self,
        checker: Any = None,
        handler: Any = None,
        *,
        max_retries: int = 1,
        result_applier: Any = None,
    ) -> None:
        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))
        self._result_applier = result_applier
        self._lock = asyncio.Lock()
        self._ready = asyncio.Event()
        self._ready.set()
        self._active_count = 0
        self._active_idle = asyncio.Event()
        self._active_idle.set()
        self._version = 0

    def set_verification(
        self,
        checker: Any,
        handler: Any,
        *,
        max_retries: int = 1,
        result_applier: Any = None,
    ) -> None:
        """注册验证逻辑，checker 判断响应，handler 执行验证。"""

        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))
        if result_applier is not None:
            self._result_applier = result_applier

    def clear_verification(self) -> None:
        """清空验证逻辑，后续请求只执行原始发送函数。"""

        self._checker = None
        self._handler = None

    @staticmethod
    async def _await_if_needed(value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    async def wait(self) -> int:
        """请求发送前调用；若正在验证，则等待验证完成。"""

        await self._ready.wait()
        return self._version

    async def _need_verification(self, response: Any) -> bool:
        if self._checker is None:
            return False
        return bool(await self._await_if_needed(self._checker(response)))

    async def _apply_result(self, result: Any, context: Any) -> None:
        if self._result_applier is None:
            return
        await self._await_if_needed(self._result_applier(result, context))

    async def _enter_send(self) -> int:
        """进入实际请求；验证开始后新请求会在这里等待。"""

        await self._ready.wait()
        self._active_count += 1
        self._active_idle.clear()
        return self._version

    def _exit_send(self) -> None:
        """离开实际请求；最后一个请求结束后通知验证流程可以刷新状态。"""

        self._active_count -= 1
        if self._active_count <= 0:
            self._active_count = 0
            self._active_idle.set()

    async def _handle_verification(self, context: Any, version: int) -> None:
        if self._handler is None:
            return

        await self._ready.wait()
        if self._version != version:
            return

        async with self._lock:
            if self._version != version:
                return

            # 验证期间暂停后续请求，防止多个任务同时刷新同一份状态。
            self._ready.clear()
            try:
                # 等待已经进入 send() 的并发请求结束，再允许 handler 刷新页面或更新状态。
                await self._active_idle.wait()
                result = await self._await_if_needed(self._handler(context))
                await self._apply_result(result, context)
                self._version += 1
            finally:
                self._ready.set()

    async def run(
        self,
        send: Any,
        *,
        context: Mapping[str, Any] | None = None,
        context_factory: Any = None,
        verify_response: bool = True,
        max_retries: int | None = None,
    ) -> Any:
        """包装一个实际请求任务，并在命中验证后自动重发当前请求。"""

        if max_retries is None:
            retry_limit = self._max_retries
        else:
            retry_limit = max(0, int(max_retries))

        verify_attempt = 0
        while True:
            version = await self._enter_send()
            try:
                response = await self._await_if_needed(send())
            finally:
                self._exit_send()

            if not verify_response or not await self._need_verification(response):
                return response

            if verify_attempt >= retry_limit:
                return response

            if context_factory is None:
                verify_context = GateVerificationContext(
                    response=response,
                    verify_attempt=verify_attempt,
                    version=version,
                    extra=dict(context or {}),
                )
            else:
                verify_context = context_factory(response, verify_attempt, version)
            await self._handle_verification(verify_context, version)
            verify_attempt += 1


__all__ = ["VerificationContext", "GateVerificationContext", "AsyncVerificationGate"]
