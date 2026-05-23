"""业务模块层。"""

from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from . import jslib as jslib
    from . import request as request

__getattr__, __all__ = bind_lazy_exports(__name__, __file__, mode="submodule")
