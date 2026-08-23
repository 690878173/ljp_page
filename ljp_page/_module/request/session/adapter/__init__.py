"""HTTP backend adapters."""

from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .aio_adapter import *  # noqa: F403
    from .curl_cffi_adapter import *  # noqa: F403
    from .model import *  # noqa: F403
    from .requests_adapter import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
