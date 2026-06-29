from __future__ import annotations

import inspect
from typing import Any, Callable, TYPE_CHECKING

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._core.exceptions import ParseError

if TYPE_CHECKING:
    from ljp_page._module.runtime import LJPExc
from .base import Base_Manager

class Pc_Base_Parser(Ljp_BaseClass_Logger,Base_Manager):
    """封装同步/异步解析函数的统一执行逻辑。"""

    async def init(self):
        pass

    def __init__(self, exc: LJPExc, logger: Any = None) -> None:
        super().__init__()
        self.set_logger(logger)
        self.exc = exc

    async def parse_html(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            handle = self.exc.submit(func, *args, mode="thread", **kwargs)
            return await handle
        except Exception as exc:
            raise ParseError(message="解析出错") from exc


__all__ = ["Pc_Base_Parser"]
