# 05-19-17-20-00
"""new_pc 解析执行组件。"""

from __future__ import annotations

import inspect
from typing import Any, Callable

from ljp_page._core._base_class import Ljp_BaseClass
from ljp_page._core._exceptions import ParseError
from ljp_page._module.runtime import LJPExc


class PcParser(Ljp_BaseClass):
    """封装同步/异步解析函数的统一执行逻辑。"""

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
            raise ParseError(e=exc, message="解析出错")


__all__ = ["PcParser"]
