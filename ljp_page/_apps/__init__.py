# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from . import new_pc as new_pc
    from . import pydoll_pc as pydoll_pc

__getattr__, __all__ = bind_lazy_exports(__name__, __file__, mode="submodule")
