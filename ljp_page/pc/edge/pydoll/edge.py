# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import make_proxy_getattr

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.ljp_op.edge import ChromiumOptions as ChromiumOptions
    from ljp_page._modules.pydoll.ljp_op.edge import Edge as Edge
    from ljp_page._modules.pydoll.ljp_op.edge import EdgeConfig as EdgeConfig

__all__ = ["Edge", "EdgeConfig", "ChromiumOptions"]
__getattr__ = make_proxy_getattr("ljp_page._modules.pydoll.ljp_op.edge", __all__)
