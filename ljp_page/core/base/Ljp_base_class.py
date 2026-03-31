from __future__ import annotations

from typing import Any, Callable

_LOGGER_LEVEL: dict[str, int] = {
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


class Ljp_BaseClass:
    def __init__(self, logger: Any = None):
        self.logger = logger

    @classmethod
    def _normalize_level(cls, level: int | str, fallback: int = 5) -> int:
        if isinstance(level, int):
            return min(20, max(1, level))
        value = _LOGGER_LEVEL.get(str(level).strip().lower(), fallback)
        return min(20, max(1, value))

    def log(self, mes: str,level:int=5, f_name: str = "") -> None:
        """
        统一日志入口
        """
        self._log(level,mes, f_name=f_name)

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
        REVERSE_LEVEL = {v: k for k, v in _LOGGER_LEVEL.items()}
        level_ls = [REVERSE_LEVEL[i] for i in range(level_code,21)]
        for method_name in level_ls:
            method = getattr(self.logger, method_name,None)
            if callable(method):
                method(message)
                return

        debug_method = getattr(self.logger, "debug", None)
        if callable(debug_method):
            debug_method(message)
            return
        print(message)

    def debug(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('debug'), message, f_name)

    def trace(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('trace'), message, f_name)

    def info(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('info'), message, f_name)

    def warrior(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('warrior'), message, f_name)

    def warning(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('warning'), message, f_name)

    def error(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('error'), message, f_name)

    def critical(self, message: Any, f_name: str = "") -> None:
        self._log(_LOGGER_LEVEL.get('critical'), message, f_name)

    @staticmethod
    def name(func: Callable[..., Any]) -> str:
        return func.__name__





































