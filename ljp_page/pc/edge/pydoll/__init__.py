# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .edge import ChromiumOptions as ChromiumOptions
    from .edge import Edge as Edge
    from .edge import EdgeConfig as EdgeConfig
    from .type import CookieParam as CookieParam

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
