# 04-01-20-21-00
"""验证码模块基类。"""

from __future__ import annotations

from typing import Any

from ljp_page._core.base import ModuleBase


class CaptchaModuleBase(ModuleBase):
    """验证码模块基类。"""

    module_name = "captcha"

    def predict(self, img_bytes: bytes, *args: Any, **kwargs: Any) -> str:
        """识别验证码。"""
        raise NotImplementedError("predict 必须由子类实现")


__all__ = ["CaptchaModuleBase"]
