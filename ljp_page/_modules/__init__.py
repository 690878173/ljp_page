# 05-19-16-20-00
"""业务模块层。"""

from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from . import file as file
    from . import jslib as jslib
    from . import ocr as ocr
    from . import playwright as playwright
    from . import pydoll as pydoll
    from . import request as request

__getattr__, __all__ = bind_lazy_exports(__name__, __file__, mode="submodule")
