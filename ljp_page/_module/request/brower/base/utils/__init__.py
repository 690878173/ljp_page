# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .general import *  # noqa: F403
    from .socks5_proxy_forwarder import *  # noqa: F403
    from .user_agent_parser import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
