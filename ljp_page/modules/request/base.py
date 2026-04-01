"""03-28-16-00-00 请求模块基类。"""

from __future__ import annotations

from typing import Any

from ...config import LjpConfig
from ...core.base import AsyncModuleBase, ModuleBase, SyncModuleBase


class RequestModuleBase(ModuleBase):
    """请求模块公共基类。"""

    module_name = "request"

    def __init__(self, config: LjpConfig, logger: Any = None) -> None:
        super().__init__(logger=logger)
        self.config = config


class SyncRequestModuleBase(RequestModuleBase, SyncModuleBase):
    """同步请求模块基类。"""


class AsyncRequestModuleBase(RequestModuleBase, AsyncModuleBase):
    """异步请求模块基类。"""
