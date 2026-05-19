# 05-19-16-20-00
"""模块基类导出。"""

from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .module_base import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)

