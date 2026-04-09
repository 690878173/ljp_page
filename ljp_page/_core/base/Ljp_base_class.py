from __future__ import annotations

from typing import Any, Callable
from ljp_page._core.logger import DEFAULT_LEVEL_ALIASES

class Ljp_BaseClass:
    def __init__(self, logger: Any = None):
        self.logger = logger

    def log(self, mes: str,level:int=5, f_name: str = "") -> None:
        """
        统一日志入口
        """
        self._log(level,mes, f_name=f_name)

    def _log(self, level: int | str, message: Any, f_name: str = "") -> None:
        formatted_message = f"[{f_name}] {message}" if f_name else str(message)
        if self.logger is None:
            print(formatted_message)
            return
        log_method = getattr(self.logger, "log", None)
        if callable(log_method):
            log_method(level, formatted_message)
            return
        print(formatted_message)

    def debug(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('debug'), message, f_name)

    def trace(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('trace'), message, f_name)

    def info(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('info'), message, f_name)

    def warrior(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('warrior'), message, f_name)

    def warning(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('warning'), message, f_name)

    def error(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('error'), message, f_name)

    def critical(self, message: Any, f_name: str = "") -> None:
        self._log(DEFAULT_LEVEL_ALIASES.get('critical'), message, f_name)

    @staticmethod
    def name(func: Callable[..., Any]) -> str:
        return func.__name__





































