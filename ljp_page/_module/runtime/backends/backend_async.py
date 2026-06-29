from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import Any, Awaitable, cast, TYPE_CHECKING

from ljp_page._module.runtime.backends.ljp_async import Async
from ljp_page._module.runtime.backends.base import BaseBackend
if TYPE_CHECKING:
    from ljp_page._module.runtime.task import BindTask, TaskSubmitConfig


class AsyncBackend(BaseBackend):
    """异步后端。"""

    mode_name = "async"
    backend_name = "async"

    def __init__(
        self,
        runtime: Async | None = None,
        *,
        async_mode: int = 1,
        logger: Any = None,
    ) -> None:
        super().__init__()
        self.runtime = runtime or Async(
            mode=async_mode,
            logger=logger,
        )

    def submit(self, bound_task: BindTask, config: TaskSubmitConfig) -> Future[Any]:
        return self._submit(bound_task, config)

    def _submit(self, bound_task: BindTask, config: TaskSubmitConfig) -> Future[Any]:
        awaitable = bound_task.create_awaitable()
        awaitable = self._wrap_with_semaphores(awaitable, config.semaphores)
        wrapped: Awaitable[Any] = awaitable
        if config.timeout is not None:
            wrapped = asyncio.wait_for(wrapped, timeout=config.timeout)

        try:
            return cast(
                Future[Any],
                self.runtime.submit(
                    wrapped,
                    task_id=config.task_id,
                    await_result=False,
                ),
            )
        except Exception:
            self._close_if_coroutine(wrapped)
            self._close_if_coroutine(awaitable)
            raise

    @classmethod
    def _wrap_with_semaphores(
        cls,
        awaitable: Awaitable[Any],
        semaphores: tuple[asyncio.Semaphore, ...],
    ) -> Awaitable[Any]:
        if not semaphores:
            return awaitable
        return cls._run_with_semaphores(awaitable, semaphores)

    @staticmethod
    async def _run_with_semaphores(
        awaitable: Awaitable[Any],
        semaphores: tuple[asyncio.Semaphore, ...],
    ) -> Any:
        async def _enter(index: int) -> Any:
            if index >= len(semaphores):
                return await awaitable
            async with semaphores[index]:
                return await _enter(index + 1)

        return await _enter(0)

    @staticmethod
    def _close_if_coroutine(obj: Any) -> None:
        """在提交失败时关闭未调度的协程对象。"""
        if asyncio.iscoroutine(obj):
            obj.close()

    def shutdown(self, timeout: float = 5.0, **_: Any) -> None:
        self.runtime.stop(timeout=timeout)
