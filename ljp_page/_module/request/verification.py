from __future__ import annotations

import asyncio
import inspect
import threading
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Mapping

from ljp_page._module.request.session.models import RequestsReponse


@dataclass(slots=True)
class VerificationContext:
    """Backend-neutral context passed to a verification handler."""

    response: RequestsReponse
    verify_attempt: int = 0
    version: int = 0
    extra: dict[str, object] = field(default_factory=dict)

    def __getitem__(self, key: str) -> object:
        if key in {"response", "verify_attempt", "version", "extra"}:
            return getattr(self, key)
        return self.extra[key]

    def get(self, key: str, default: object | None = None) -> object | None:
        if key in {"response", "verify_attempt", "version", "extra"}:
            return getattr(self, key)
        return self.extra.get(key, default)

    def __getattr__(self, key: str) -> object:
        try:
            return self.extra[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class AsyncVerification:
    """Async verification gate that pauses concurrent requests while refreshing state."""

    def __init__(
        self,
        checker: Callable[[RequestsReponse], object] | None,
        handler: Callable[[VerificationContext], object] | None,
        *,
        max_retries: int = 1,
        result_applier: Callable[[object, VerificationContext], object] | None = None,
    ) -> None:
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

    def set_verification(
        self,
        checker: Callable[[RequestsReponse], object],
        handler: Callable[[VerificationContext], object],
        *,
        max_retries: int = 1,
        result_applier: Callable[[object, VerificationContext], object] | None = None,
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
    async def to_await(value: object) -> object:
        if inspect.isawaitable(value):
            return await value
        return value

    async def _need_verification(self, response: RequestsReponse) -> bool:
        if self._checker is None:
            return False
        return bool(await self.to_await(self._checker(response)))

    async def _apply_result(self, result: object, context: VerificationContext) -> None:
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

    async def _handle_verification(self, context: VerificationContext, version: int) -> bool:
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
        send: Callable[[], Awaitable[RequestsReponse] | RequestsReponse],
        *,
        context: Mapping[str, object] | None = None,
        verify_response: bool = True,
        max_retries: int | None = None,
    ) -> RequestsReponse:
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
                continue
            if self._version != version:
                continue
            return response


class SyncVerification:
    """Thread-safe verification gate for :class:`SyncSessionPool`."""

    def __init__(
        self,
        checker: Callable[[RequestsReponse], object] | None,
        handler: Callable[[VerificationContext], object] | None,
        *,
        max_retries: int = 1,
        result_applier: Callable[[object, VerificationContext], object] | None = None,
    ) -> None:
        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))
        self._result_applier = result_applier
        self._condition = threading.Condition(threading.RLock())
        self._door_open = True
        self._active_count = 0
        self._version = 0

    def set_verification(
        self,
        checker: Callable[[RequestsReponse], object],
        handler: Callable[[VerificationContext], object],
        *,
        max_retries: int = 1,
        result_applier: Callable[[object, VerificationContext], object] | None = None,
    ) -> None:
        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))
        if result_applier is not None:
            self._result_applier = result_applier

    def clear_verification(self) -> None:
        self._checker = None
        self._handler = None

    @staticmethod
    def _resolve(value: object) -> object:
        if inspect.isawaitable(value):
            raise TypeError(
                "SyncVerification does not accept awaitable checker, handler, "
                "or result_applier results"
            )
        return value

    def _need_verification(self, response: RequestsReponse) -> bool:
        if self._checker is None:
            return False
        return bool(self._resolve(self._checker(response)))

    def _apply_result(self, result: object, context: VerificationContext) -> None:
        if self._result_applier is not None:
            self._resolve(self._result_applier(result, context))

    def _enter_send(self) -> int:
        with self._condition:
            while not self._door_open:
                self._condition.wait()
            self._active_count += 1
            return self._version

    def _exit_send(self) -> None:
        with self._condition:
            self._active_count -= 1
            if self._active_count <= 0:
                self._active_count = 0
                self._condition.notify_all()

    def _handle_verification(self, context: VerificationContext, version: int) -> bool:
        if self._handler is None:
            return False

        with self._condition:
            while not self._door_open:
                self._condition.wait()
            if self._version != version:
                return False
            self._door_open = False
            while self._active_count:
                self._condition.wait()

        try:
            result = self._resolve(self._handler(context))
            self._apply_result(result, context)
        except BaseException:
            with self._condition:
                self._door_open = True
                self._condition.notify_all()
            raise

        with self._condition:
            self._version += 1
            self._door_open = True
            self._condition.notify_all()
        return True

    def run(
        self,
        send: Callable[[], RequestsReponse],
        *,
        context: Mapping[str, object] | None = None,
        verify_response: bool = True,
        max_retries: int | None = None,
    ) -> RequestsReponse:
        retry_limit = self._max_retries if max_retries is None else max(0, int(max_retries))
        verify_attempt = 0
        while True:
            version = self._enter_send()
            try:
                response = send()
            finally:
                self._exit_send()

            with self._condition:
                if self._version != version:
                    continue

            if not verify_response or not self._need_verification(response):
                return response
            if verify_attempt >= retry_limit:
                return response

            verification_context = VerificationContext(
                response=response,
                verify_attempt=verify_attempt,
                version=version,
                extra=dict(context or {}),
            )
            if self._handle_verification(verification_context, version):
                verify_attempt += 1
                continue
            with self._condition:
                if self._version != version:
                    continue
            return response


__all__ = ["AsyncVerification", "SyncVerification", "VerificationContext"]
