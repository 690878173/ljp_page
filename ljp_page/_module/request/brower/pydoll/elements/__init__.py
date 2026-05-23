# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from . import mixins as mixins
    from . import utils as utils
    from . import web_element as web_element

__getattr__, __all__ = bind_lazy_exports(__name__, __file__, mode="submodule")
