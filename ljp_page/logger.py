# 05-19-16-20-00
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ljp_page._core.logger import *


from ljp_page._core.logger import __all__,__getattr__ as _g
def __getattr__(name):
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    obj = _g(name)
    globals()[name] = obj
    return obj








