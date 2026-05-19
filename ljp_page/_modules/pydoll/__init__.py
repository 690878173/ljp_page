# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from . import browser as browser
    from . import commands as commands
    from . import connection as connection
    from . import elements as elements
    from . import extractor as extractor
    from . import interactions as interactions
    from . import protocol as protocol
    from . import utils as utils

__getattr__, __all__ = bind_lazy_exports(__name__, __file__, mode="submodule")
