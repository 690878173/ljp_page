from __future__ import annotations

from typing import Any

from .logger import logger


class Ljp_BaseClass_Logger:
    def __init__(self):
        self.logger = logger

    def set_logger(self, log: Any) -> None:
        self.logger = log

    def log(self, mes: str, level: str = "info", f_name: str = "") -> None:
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
        self._log("debug", message, f_name)

    def trace(self, message: Any, f_name: str = "") -> None:
        self._log("trace", message, f_name)

    def info(self, message: Any, f_name: str = "") -> None:
        self._log("info", message, f_name)

    def print(self, message: Any, f_name: str = "") -> None:
        self._log("print", message, f_name)

    def warrior(self, message: Any, f_name: str = "") -> None:
        self._log("warrior", message, f_name)

    def warning(self, message: Any, f_name: str = "") -> None:
        self._log("warning", message, f_name)

    def error(self, message: Any, f_name: str = "") -> None:
        self._log("error", message, f_name)

    def critical(self, message: Any, f_name: str = "") -> None:
        self._log("critical", message, f_name)

    def __str__(self) -> str:
        # 获取 完整模块名 + 类名
        full_class_name = f"{self.__module__}.{self.__class__.__name__}"
        return f"<{full_class_name}>"

__all__ = ['Ljp_BaseClass_Logger']































