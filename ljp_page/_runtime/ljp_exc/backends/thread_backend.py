# 03-26-21-03-00
from __future__ import annotations

from concurrent.futures import Future
from typing import Any, cast

from ...threadpool import ThreadPool
from .base import BaseBackend
from ..task import BoundTask, TaskSubmitConfig


class ThreadBackend(BaseBackend):
    """线程后端：复用旧版 ThreadPool。"""

    mode_name = "thread"
    backend_name = "thread"

    def __init__(
        self,
        pool: ThreadPool | None = None,
        *,
        max_workers: int | None = None,
        thread_name_prefix: str = "LjpExcThreadPool",
        logger: Any = None,
    ) -> None:
        super().__init__(logger=logger)
        self.pool = pool or ThreadPool(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            logger=logger,
        )

    def submit(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        if bound_task.is_async_target():
            raise TypeError("thread 模式只支持普通函数")

        return cast(
            Future[Any],
            self.pool.submit(
                bound_task.target,
                *bound_task.args,
                task_id=config.task_id,
                **bound_task.kwargs,
            ),
        )

    def shutdown(self, wait: bool = True, cancel_futures: bool = False, **_: Any) -> None:
        self.pool.shutdown(wait=wait, cancel_futures=cancel_futures)

