# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.logger import __all__ as __all__
from ljp_page._core.logger import __getattr__ as __getattr__

if TYPE_CHECKING:
    from ljp_page._core.logger import DEFAULT_LEVEL_ALIASES as DEFAULT_LEVEL_ALIASES
    from ljp_page._core.logger import DEFAULT_LEVEL_NAMES as DEFAULT_LEVEL_NAMES
    from ljp_page._core.logger import LogConfig as LogConfig
    from ljp_page._core.logger import Logger as Logger
    from ljp_page._core.logger import logger as logger
