from __future__ import annotations

from concurrent.futures import Future
from typing import Any, TYPE_CHECKING

__all__ = ['BaseBackend']

if TYPE_CHECKING:
    from ljp_page._module.tools.bind import BindTask
    from ljp_page._module.runtime.task import TaskSubmitConfig


class BaseBackend:
    """统一后端基类。"""

    mode_name = "base"
    backend_name = "base"

    def submit(self, bound_task: BindTask, config: TaskSubmitConfig) -> Future[Any]:
        """提交单个任务。"""
        raise NotImplementedError

    def shutdown(self, **_: Any) -> None:
        """关闭后端资源。"""

