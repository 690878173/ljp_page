from __future__ import annotations
import asyncio
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping,Callable, Awaitable, TypeVar, Generic

from ljp_page._core.utils.other import f_mark
from ljp_page._module.request.session.config import LjpResponse

if TYPE_CHECKING:
    from ljp_page._module.request.session.session import ASession, AsyncSession

T = TypeVar("T")



@f_mark('考虑移除，仅使用下面的通用上下文')
@dataclass(slots=True)
class SessionVerificationContext:
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
class VerificationContext:
    """验证上下文，仅内部使用。"""

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


class AsyncVerification:
    '''
    拦截请求，检查是否需要验证 -> 需要验证 -> 其他请求等待，

    执行请求完放行，同时只有一个请求执行验证，验证完所有请求重新请求
    '''
    def __init__(
            self,
            checker: Any,
            handler: Any,
            *,
            max_retries: int = 1,
            result_applier: Any = None,
    ):
        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))
        self._result_applier = result_applier

        self._lock = asyncio.Lock()

        self._door_ev = asyncio.Event()
        self._door_ev.set()

        self._active_count = 0
        self._no_active_ev = asyncio.Event()
        self._no_active_ev.set()
        self._version = 0

    def set_verification(self,checker,handler,*,max_retries: int = 1,result_applier: Any = None):
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
    async def to_await(value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    async def _need_verification(self, response: Any) -> bool:
        if self._checker is None:
            return False
        return bool(await self.to_await(self._checker(response)))

    async def _apply_result(self, result: Any, context: Any) -> None:
        if self._result_applier is None:
            return
        await self.to_await(self._result_applier(result, context))

    async def _enter_send(self) -> int:
        """进入实际请求；验证开始后新请求会在这里等待。"""

        await self._door_ev.wait()
        self._active_count += 1
        self._no_active_ev.clear()
        return self._version

    def _exit_send(self) -> None:
        """离开实际请求；最后一个请求结束后通知验证流程可以刷新状态。"""

        self._active_count -= 1
        if self._active_count <= 0:
            self._active_count = 0
            self._no_active_ev.set()

    async def _handle_verification(self, context: Any, version: int) -> None|bool:
        if self._handler is None:
            return False

        await self._door_ev.wait()
        if self._version != version:
            return False

        async with self._lock:

            if self._version != version:
                return False

            # 验证期间暂停后续请求，防止多个任务同时刷新同一份状态。
            self._door_ev.clear()
            try:
                # 等待已经进入 send() 的并发请求结束，再允许 handler 刷新页面或更新状态。
                await self._no_active_ev.wait()
                result = await self.to_await(self._handler(context))
                await self._apply_result(result, context)
                self._version += 1
                return True
            finally:
                self._door_ev.set()


    async def run(
        self,
        send: Callable[[], Awaitable[T] | T],
        *,
        context: Mapping[str, Any] | None = None,
        verify_response: bool = True,
        max_retries: int | None = None,
    ) -> T:
        """包装一个实际请求任务，并在命中验证后自动重发当前请求。"""

        if max_retries is None:
            retry_limit = self._max_retries
        else:
            retry_limit = max(0, int(max_retries))

        verify_attempt = 0
        while True:
            version = await self._enter_send()
            try:
                response = await self.to_await(send())
            finally:
                self._exit_send()

            if self._version != version:
                continue

            if not verify_response or not await self._need_verification(response):
                return response

            if verify_attempt >= retry_limit:
                return response

            verify_context = VerificationContext(
                response=response,
                verify_attempt=verify_attempt,
                version=version,
                extra=dict(context or {}),
            )

            ver_ok = await self._handle_verification(verify_context, version)
            if ver_ok:
                verify_attempt += 1





















__all__ = ["SessionVerificationContext", "VerificationContext", "AsyncVerification"]
