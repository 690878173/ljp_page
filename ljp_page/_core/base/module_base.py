"""03-28-16-00-00 模块级通用基类。"""

from __future__ import annotations

from typing import Any

from ljp_page._core.other import deprecated_class

from ljp_page._core._base_class import Ljp_BaseClass

@deprecated_class("ModuleBase 已废弃，请直接继承 Ljp_BaseClass，不要再使用")
class ModuleBase(Ljp_BaseClass):
    """模块基础能力：日志与模块名管理。"""

    module_name = "module"

    def __init__(self, logger: Any = None) -> None:
        super().__init__()
        self.logger = logger

    @classmethod
    def get_module_name(cls) -> str:
        return cls.module_name

@deprecated_class("已废弃")
class SyncModuleBase(ModuleBase):
    """同步模块基类。"""

    module_mode = "sync"

@deprecated_class("已废弃")
class AsyncModuleBase(ModuleBase):
    """异步模块基类。"""

    module_mode = "async"
