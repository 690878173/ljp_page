# 05-19-16-20-00
from __future__ import annotations

from typing import TYPE_CHECKING

from ljp_page._modules.ocr import __all__ as __all__
from ljp_page._modules.ocr import __getattr__ as __getattr__

if TYPE_CHECKING:
    from ljp_page._modules.ocr import Ocr as Ocr
