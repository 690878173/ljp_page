# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils._lazy_import import mapped_module_exports

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

_EXPORT_MAP = {
    "DEFAULT_TYPO_PROBABILITY": "ljp_page._modules.pydoll.constants",
    "TypoType": "ljp_page._modules.pydoll.constants",
    "IFrameContext": "ljp_page._modules.pydoll.interactions.iframe",
    "IFrameContextResolver": "ljp_page._modules.pydoll.interactions.iframe",
    "Keyboard": "ljp_page._modules.pydoll.interactions.keyboard",
    "KeyboardAPI": "ljp_page._modules.pydoll.interactions.keyboard",
    "TimingConfig": "ljp_page._modules.pydoll.interactions.keyboard",
    "TypoConfig": "ljp_page._modules.pydoll.interactions.keyboard",
    "TypoResult": "ljp_page._modules.pydoll.interactions.keyboard",
    "Mouse": "ljp_page._modules.pydoll.interactions.mouse",
    "MouseAPI": "ljp_page._modules.pydoll.interactions.mouse",
    "MouseTimingConfig": "ljp_page._modules.pydoll.interactions.mouse",
    "Scroll": "ljp_page._modules.pydoll.interactions.scroll",
    "ScrollAPI": "ljp_page._modules.pydoll.interactions.scroll",
    "ScrollTimingConfig": "ljp_page._modules.pydoll.interactions.scroll",
}

__getattr__, __all__ = mapped_module_exports(_EXPORT_MAP)
