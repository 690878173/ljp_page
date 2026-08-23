# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import make_proxy_getattr

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll import *

__all__ = ["Edge", "EdgeConfig", "ChromiumOptions","Tab"]
__getattr__ = make_proxy_getattr("ljp_page._modules.pydoll.ljp_op.edge", __all__)
