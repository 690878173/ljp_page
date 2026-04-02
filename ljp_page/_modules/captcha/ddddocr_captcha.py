# 04-01-20-12-00
"""ddddocr 验证码模块实现。"""

from __future__ import annotations

from .base import CaptchaModuleBase
from .config import CaptchaConfig


class DdddOcrCaptcha(CaptchaModuleBase):
    """基于 ddddocr 的验证码识别实现。"""

    module_name = "captcha_ddddocr"

    def __init__(
        self,
        show_ad: bool | None = None,
        config: CaptchaConfig | None = None,
    ) -> None:
        super().__init__()
        cfg = config or CaptchaConfig()
        resolved_show_ad = cfg.show_ad if show_ad is None else show_ad

        import ddddocr

        self.ocr = ddddocr.DdddOcr(show_ad=resolved_show_ad)

    def predict(self, img_bytes: bytes, *args: object, **kwargs: object) -> str:
        return self.ocr.classification(img_bytes)


_default_engine: DdddOcrCaptcha | None = None


def yzm(img_bytes: bytes) -> str:
    """兼容旧函数接口。"""

    global _default_engine
    if _default_engine is None:
        _default_engine = DdddOcrCaptcha(config=CaptchaConfig(show_ad=False))
    return _default_engine.predict(img_bytes)


__all__ = ["DdddOcrCaptcha", "yzm"]
