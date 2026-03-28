"""03-28-16-00-00 验证码模块基类。"""

from __future__ import annotations

from typing import Any

from ...core.base import ModuleBase


class CaptchaModuleBase(ModuleBase):
    """验证码模块基类。"""

    module_name = "captcha"

    def predict(self, img_bytes: bytes, *args: Any, **kwargs: Any) -> str:
        """识别验证码。"""

        raise NotImplementedError("predict 必须由子类实现")
