"""03-28-17-10-00 基础类：统一日志与异常装饰器。"""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any, Callable, Tuple, Type, Union


class Ljp_BaseClass:
    """基础能力：日志入口统一支持 1-20 等级。"""

    _LEVEL_ALIASES: dict[str, int] = {
        "debug": 1,
        "trace": 2,
        "verbose": 3,
        "notice": 4,
        "info": 5,
        "step": 6,
        "event": 7,
        "check": 8,
        "risk": 9,
        "warrior": 10,
        "warning": 10,
        "warn": 10,
        "alert": 12,
        "issue": 13,
        "error": 15,
        "fatal": 16,
        "panic": 17,
        "security": 18,
        "emergency": 19,
        "critical": 19,
        "off": 20,
    }

    def __init__(self, logger: Any = None):
        self.logger = logger

    @classmethod
    def _normalize_level(cls, level: int | str, fallback: int = 5) -> int:
        if isinstance(level, int):
            return min(20, max(1, level))
        value = cls._LEVEL_ALIASES.get(str(level).strip().lower(), fallback)
        return min(20, max(1, value))

    def _emit_via_method(self, level_code: int, message: str) -> None:
        if self.logger is None:
            print(message)
            return

        # 优先调用支持数字等级的统一接口。
        log_method = getattr(self.logger, "log", None)
        if callable(log_method):
            try:
                log_method(level_code, message)
                return
            except TypeError:
                # 兼容旧 logger.log(message, level) 风格
                log_method(message, level_code)
                return

        if level_code >= 19:
            for method_name in ("critical", "error", "warning", "info", "debug"):
                method = getattr(self.logger, method_name, None)
                if callable(method):
                    method(message)
                    return
            return
        if level_code >= 15:
            for method_name in ("error", "warning", "info", "debug"):
                method = getattr(self.logger, method_name, None)
                if callable(method):
                    method(message)
                    return
            return
        if level_code >= 10:
            for method_name in ("warning", "info", "debug"):
                method = getattr(self.logger, method_name, None)
                if callable(method):
                    method(message)
                    return
            return
        if level_code >= 5:
            for method_name in ("info", "debug"):
                method = getattr(self.logger, method_name, None)
                if callable(method):
                    method(message)
                    return
            return

        debug_method = getattr(self.logger, "debug", None)
        if callable(debug_method):
            debug_method(message)
            return
        print(message)

    def _log(self, level: int | str, message: Any, f_name: str = "") -> None:
        level_code = self._normalize_level(level)
        if level_code == 20:
            return
        formatted_message = f"[{f_name}] {message}" if f_name else str(message)
        try:
            self._emit_via_method(level_code, formatted_message)
        except Exception as exc:
            print(
                f"记录日志失败 level={level_code} error={exc} 原始日志={formatted_message}"
            )

    def log(self, *args: Any, f_name: str = "") -> None:
        """
        统一日志入口，兼容两种调用方式：
        1. log(level, message)
        2. log(message, level)
        """

        if not args:
            return
        if len(args) == 1:
            self._log(5, args[0], f_name=f_name)
            return

        first, second = args[0], args[1]
        if isinstance(first, int):
            self._log(first, second, f_name=f_name)
            return
        if isinstance(first, str) and first.strip().lower() in self._LEVEL_ALIASES:
            self._log(first, second, f_name=f_name)
            return
        self._log(second, first, f_name=f_name)

    def debug(self, message: Any, f_name: str = "") -> None:
        self._log(1, message, f_name)

    def trace(self, message: Any, f_name: str = "") -> None:
        self._log(2, message, f_name)

    def info(self, message: Any, f_name: str = "") -> None:
        self._log(5, message, f_name)

    def warrior(self, message: Any, f_name: str = "") -> None:
        self._log(10, message, f_name)

    def warning(self, message: Any, f_name: str = "") -> None:
        self._log(10, message, f_name)

    def error(self, message: Any, f_name: str = "") -> None:
        self._log(15, message, f_name)

    def critical(self, message: Any, f_name: str = "") -> None:
        self._log(19, message, f_name)

    @staticmethod
    def name(func: Callable[..., Any]) -> str:
        return func.__name__


class Ljp_Decorator:
    @classmethod
    def handle_exceptions(
        cls,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
        handler: Callable[..., Any] | None = None,
        reraise: bool = True,
        default_return: Any = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """通用异常处理装饰器。"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if handler:
                        handler(args[0], exc, func, *args[1:], **kwargs)
                    if reraise:
                        raise
                    return default_return

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if handler:
                        await handler(args[0], exc, func, *args[1:], **kwargs)
                    if reraise:
                        raise
                    return default_return

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator
