
from __future__ import annotations

from typing import TYPE_CHECKING

from ljp_page._module.ocr import __all__,__getattr__ as _g

if TYPE_CHECKING:
    from ljp_page._module.ocr import Ocr


def __getattr__(name):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    obj = _g(name)
    globals()[name] = obj
    return obj
