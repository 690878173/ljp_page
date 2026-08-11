from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .config import Config as Config
    from .controller import LifecycleController as LifecycleController
    from .enums import PipelineMode as PipelineMode
    from .executor import BasePc as BasePc
    from .file_manager import FileManager as FileManager
    from .models import (
        P1Item as P1Item,
        P1Result as P1Result,
        P2Item as P2Item,
        P2Result as P2Result,
        P3Item as P3Item,
    )
    from .parser import HtmlParser as HtmlParser
    from .request import BaseRequest as BaseRequest, RequestManager as RequestManager
    from .scheduler import PipelineScheduler as PipelineScheduler

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
