# 05-19-16-20-00
"""可视化模块。"""

from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .matplotlib import *  # noqa: F403
    from .pyecharts import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
