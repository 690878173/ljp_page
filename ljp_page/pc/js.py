# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._modules.jslib import __all__ as __all__
from ljp_page._modules.jslib import __getattr__ as __getattr__

if TYPE_CHECKING:
    from ljp_page._modules.jslib import Js as Js
    from ljp_page._modules.jslib import JsRuntimeConfig as JsRuntimeConfig
