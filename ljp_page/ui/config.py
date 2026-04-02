# 04-01-20-09-00
"""UI 模块配置。"""

from dataclasses import dataclass


@dataclass(slots=True)
class UiRuntimeConfig:
    """UI 运行时基础配置。"""

    app_title: str = "LJP UI"
    default_theme: str = "light"


__all__ = ["UiRuntimeConfig"]
