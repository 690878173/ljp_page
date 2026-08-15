# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .iframe import IFrameContext as IFrameContext
    from .iframe import IFrameContextResolver as IFrameContextResolver
    from .keyboard import Keyboard as Keyboard
    from .keyboard import KeyboardAPI as KeyboardAPI
    from .keyboard import TimingConfig as TimingConfig
    from .keyboard import TypoConfig as TypoConfig
    from .keyboard import TypoResult as TypoResult
    from .mouse import Mouse as Mouse
    from .mouse import MouseAPI as MouseAPI
    from .mouse import MouseTimingConfig as MouseTimingConfig
    from .scroll import Scroll as Scroll
    from .scroll import ScrollAPI as ScrollAPI
    from .scroll import ScrollTimingConfig as ScrollTimingConfig

__getattr__, __all__ = bind_lazy_exports(__name__,__file__)
