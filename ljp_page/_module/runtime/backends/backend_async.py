from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import Any, Awaitable, cast, TYPE_CHECKING

from ljp_page._module.runtime.backends.ljp_async import Async
from ljp_page._module.runtime.backends.base import BaseBackend
if TYPE_CHECKING:
    from ljp_page._module.tools.bind import BindTask
    from ljp_page._module.runtime.task import TaskSubmitConfig

__all__ = ["AsyncBackend"]

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
        original = bound_task.create_awaitable()
        sem_wrapped = self._wrap_with_semaphores(original, config.semaphores)
        wrapped: Awaitable[Any] = sem_wrapped
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
            self._close_if_coroutine(original)
            if sem_wrapped is not original:
                self._close_if_coroutine(sem_wrapped)
            if wrapped is not original and wrapped is not sem_wrapped:
                self._close_if_coroutine(wrapped)
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
        # 使用显式迭代替代递归，避免信号量数量大时栈溢出。
        # acquired 列表保证 acquire 中途异常时只释放已获取的信号量。
        async def _run() -> Any:
            acquired: list[asyncio.Semaphore] = []
            try:
                for sem in semaphores:
                    await sem.acquire()
                    acquired.append(sem)
                return await awaitable
            finally:
                for sem in reversed(acquired):
                    sem.release()

        return await _run()

    @staticmethod
    def _close_if_coroutine(obj: Any) -> None:
        """在提交失败时关闭未调度的协程对象。"""
        if asyncio.iscoroutine(obj):
            obj.close()

    def shutdown(self, timeout: float = 5.0, **_: Any) -> None:
        self.runtime.stop(timeout=timeout)
