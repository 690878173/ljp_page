# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import make_submodule_getattr

if TYPE_CHECKING:
    from . import config as config
    from . import exc as exc
    from . import exceptions as exceptions
    from . import file as file
    from . import logger as logger
    from . import ocr as ocr
    from . import page_install as page_install
    from . import pc as pc
    from . import sjfx as sjfx
    from . import threadpool as threadpool

__all__ = [
    "config",
    "exc",
    "exceptions",
    "file",
    "logger",
    "ocr",
    "page_install",
    "pc",
    "sjfx",
    "threadpool",
]

__getattr__ = make_submodule_getattr(__name__, __all__)
