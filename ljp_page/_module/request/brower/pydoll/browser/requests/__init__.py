# 05-19-16-20-00
"""浏览器 fetch API 请求模块导出。"""

from typing import TYPE_CHECKING

from ljp_page._core.utils._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .har_recorder import *  # noqa: F403
    from .request import *  # noqa: F403
    from .response import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
