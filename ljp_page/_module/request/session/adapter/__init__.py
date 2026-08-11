from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .aio_adapter import AiohttpAdapter
    from .curl_cffi_adapter import CurlCffiAdapter
    from .requests_adapter import RequestsAdapter


from ljp_page._core.utils.lazy_import import bind_lazy_exports

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)

