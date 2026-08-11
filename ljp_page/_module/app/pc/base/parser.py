"""HTML 解析器 —— 统一同步 / 异步解析调用。"""

from __future__ import annotations

import inspect
from typing import Any, Callable

from ljp_page._core.exceptions import ParseError
from ljp_page._module.runtime import LJPExc


class HtmlParser:
    """封装解析函数的统一执行逻辑。

    自动检测函数是同步还是异步，同步函数投递到线程池执行。
    """

    def __init__(self, exc: LJPExc) -> None:
        self.exc = exc

    async def init(self) -> None:
        pass

    async def parse(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """执行解析函数。

        参数:
            func: 解析函数（同步或异步均可）。
            *args/**kwargs: 透传给 func 的参数。
        返回:
            func 的返回值。
        异常:
            ParseError: 解析过程中任何异常均包装为此类型。
        """
        try:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            handle = self.exc.submit(func, *args, mode="thread", **kwargs)
            return await handle
        except Exception as exc:
            raise ParseError(message="解析出错") from exc
