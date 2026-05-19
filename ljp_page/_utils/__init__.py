# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from . import decode as decode
    from . import file as file
    from . import math as math
    from . import sort as sort
    from . import web as web

__getattr__, __all__ = bind_lazy_exports(__name__, __file__, mode="submodule")
