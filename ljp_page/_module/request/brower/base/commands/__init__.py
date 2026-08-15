

from ljp_page._core.utils.lazy_import import bind_lazy_exports

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dom_commands import *
    from .input_commands import *
    from .page_commands import *
    from .runtime_commands import *




__getattr__, __all__ = bind_lazy_exports(__name__,__file__)