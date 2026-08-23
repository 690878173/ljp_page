# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils._lazy_import import make_proxy_getattr

if TYPE_CHECKING:
    from network.types import CookieParam as CookieParam

__all__ = ["CookieParam"]
__getattr__ = make_proxy_getattr("ljp_page._modules.pydoll.protocol.network.types", __all__)
