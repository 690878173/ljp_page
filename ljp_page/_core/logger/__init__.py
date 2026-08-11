from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .ljp_logger import *  # noqa: F403
    from .ts import *

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)

