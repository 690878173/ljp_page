# 04-01-20-09-00
"""验证码模块配置。"""

from dataclasses import dataclass


@dataclass(slots=True)
class CaptchaConfig:
    """验证码识别配置。"""

    show_ad: bool = False


__all__ = ["CaptchaConfig"]
