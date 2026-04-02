"""03-28-16-00-00 模块级通用基类。"""

from __future__ import annotations

from typing import Any

from ljp_page._core.base.Ljp_base_class import Ljp_BaseClass


class ModuleBase(Ljp_BaseClass):
    """模块基础能力：日志与模块名管理。"""

    module_name = "module"

    def __init__(self, logger: Any = None) -> None:
        super().__init__(logger=logger)

    @classmethod
    def get_module_name(cls) -> str:
        return cls.module_name


class SyncModuleBase(ModuleBase):
    """同步模块基类。"""

    module_mode = "sync"


class AsyncModuleBase(ModuleBase):
    """异步模块基类。"""

    module_mode = "async"
