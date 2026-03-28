# 03-26-21-03-00
from __future__ import annotations

from concurrent.futures import Future
from typing import Any

from ljp_page.core.base.base_class import Ljp_BaseClass
from ..task import BoundTask, TaskSubmitConfig


class BaseBackend(Ljp_BaseClass):
    """统一后端基类。"""

    mode_name = "base"
    backend_name = "base"

    def submit(self, bound_task: BoundTask, config: TaskSubmitConfig) -> Future[Any]:
        """提交单个任务。"""
        raise NotImplementedError

    def shutdown(self, **_: Any) -> None:
        """关闭后端资源。"""

