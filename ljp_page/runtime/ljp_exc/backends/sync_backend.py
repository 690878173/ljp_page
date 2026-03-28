# 03-26-21-03-00
from __future__ import annotations

from concurrent.futures import Future
from typing import Any

from .base import BaseBackend
from ..task import BoundTask, TaskSubmitConfig


class SyncBackend(BaseBackend):
    """同步后端：在当前线程立即执行。"""

    mode_name = "sync"
    backend_name = "sync"

    def submit(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        future: Future[Any] = Future()
        future.set_running_or_notify_cancel()

        try:
            result = bound_task.call()
        except BaseException as exc:
            future.set_exception(exc)
        else:
            future.set_result(result)

        return future

