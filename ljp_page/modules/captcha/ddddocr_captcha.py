"""03-28-16-00-00 ddddocr 验证码模块实现。"""

from __future__ import annotations

from .base import CaptchaModuleBase


class DdddOcrCaptcha(CaptchaModuleBase):
    """基于 ddddocr 的验证码识别实现。"""

    module_name = "captcha_ddddocr"

    def __init__(self, show_ad: bool = False) -> None:
        super().__init__()
        import ddddocr

        self.ocr = ddddocr.DdddOcr(show_ad=show_ad)

    def predict(self, img_bytes: bytes, *args: object, **kwargs: object) -> str:
        return self.ocr.classification(img_bytes)


_default_engine: DdddOcrCaptcha | None = None


def yzm(img_bytes: bytes) -> str:
    """兼容旧函数接口。"""

    global _default_engine
    if _default_engine is None:
        _default_engine = DdddOcrCaptcha(show_ad=False)
    return _default_engine.predict(img_bytes)
