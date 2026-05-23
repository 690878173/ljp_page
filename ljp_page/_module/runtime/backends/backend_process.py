from __future__ import annotations

from concurrent.futures import Future
from typing import Any, TYPE_CHECKING

from .base import BaseBackend
if TYPE_CHECKING:
    from ljp_page._module.runtime.task import BindTask, TaskSubmitConfig


class ProcessBackend(BaseBackend):
    """进程后端：当前版本仅保留接口。"""

    mode_name = "process"
    backend_name = "process"

    def submit(self, bound_task: BindTask, config: TaskSubmitConfig) -> Future[Any]:
        raise NotImplementedError("process 后端预留，但当前版本暂未实现")

