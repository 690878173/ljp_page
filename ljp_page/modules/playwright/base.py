"""03-28-16-00-00 Playwright 模块基类。"""

from __future__ import annotations

from ...core.base import AsyncModuleBase


class PlaywrightModuleBase(AsyncModuleBase):
    """浏览器自动化模块基类。"""

    module_name = "playwright"
