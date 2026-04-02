# 03-26-21-03-00
from __future__ import annotations

from concurrent.futures import Future
from typing import Any

from .base import BaseBackend
from ..task import BoundTask, TaskSubmitConfig


class ProcessBackend(BaseBackend):
    """进程后端：当前版本仅保留接口。"""

    mode_name = "process"
    backend_name = "process"

    def submit(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        raise NotImplementedError("process 后端预留，但当前版本暂未实现")

