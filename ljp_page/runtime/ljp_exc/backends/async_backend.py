# 03-26-21-03-00
from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import Any, Awaitable, Coroutine, cast

from ...ljp_async import Async
from .base import BaseBackend
from ..task import BoundTask, TaskSubmitConfig


class AsyncBackend(BaseBackend):
    """异步后端：复用旧版 Async。"""

    mode_name = "async"
    backend_name = "async"

    def __init__(
        self,
        runtime: Async | None = None,
        *,
        async_mode: int = 1,
        max_concurrent: int = 20,
        max_inner_concurrent: int = 100,
        logger: Any = None,
    ) -> None:
        super().__init__(logger=logger)
        self.runtime = runtime or Async(
            mode=async_mode,
            max_concurrent=max_concurrent,
            max_inner_concurrent=max_inner_concurrent,
            logger=logger,
        )

    def submit(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        if config.layer == "outer":
            return self._submit_outer(bound_task, config)
        if config.layer == "inner":
            return self._submit_inner(bound_task, config)
        raise ValueError(f"async 后端不支持的 layer: {config.layer}")

    def _submit_outer(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        awaitable = bound_task.create_awaitable()
        return cast(
            Future[Any],
            self.runtime.submit(
                awaitable,
                timeout=config.timeout,
                task_id=config.task_id,
                await_result=False,
            ),
        )

    def _submit_inner(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        awaitable = bound_task.create_awaitable()
        wrapped: Awaitable[Any] = self.runtime._wrapped_inner_coro(awaitable)
        if config.timeout is not None:
            wrapped = asyncio.wait_for(wrapped, timeout=config.timeout)

        try:
            return cast(
                Future[Any],
                asyncio.run_coroutine_threadsafe(
                    cast(Coroutine[Any, Any, Any], wrapped),
                    self.runtime.get_event_loop(),
                ),
            )
        except Exception:
            self._close_if_coroutine(wrapped)
            self._close_if_coroutine(awaitable)
            raise

    @staticmethod
    def _close_if_coroutine(obj: Any) -> None:
        """在提交失败时关闭未调度的协程对象。"""
        if asyncio.iscoroutine(obj):
            obj.close()

    def shutdown(self, timeout: float = 5.0, **_: Any) -> None:
        self.runtime.stop(timeout=timeout)
