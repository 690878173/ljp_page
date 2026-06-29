
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .ljp_retry import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)