# 04-01-20-21-00
"""Playwright 模块基类。"""

from __future__ import annotations

from ljp_page._core.base import AsyncModuleBase


class PlaywrightModuleBase(AsyncModuleBase):
    """浏览器自动化模块基类。"""

    module_name = "playwright"


__all__ = ["PlaywrightModuleBase"]
