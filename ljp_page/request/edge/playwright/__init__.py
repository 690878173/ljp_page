from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ljp_page._module.request.brower.playwright import *

from ljp_page._module.request.brower.playwright import __all__,__getattr__ as _g

def __getattr__(name):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    obj = _g(name)
    globals()[name] = obj
    return obj


