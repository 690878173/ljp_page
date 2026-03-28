# 03-28-16-28-21
"""日志中间件基类。"""

from __future__ import annotations

from typing import Any

from ....config.request_config import RequestConfig
from ....config.request_config.session_config import LjpResponse
from ..base import AsyncMiddleware, MiddlewareBase, SyncMiddleware


class LoggingMiddlewareBase(MiddlewareBase):
    """日志中间件通用基类，统一处理等级与输出适配。"""

    name = "logging_base"

    def __init__(self, config: RequestConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger
        self.enabled_levels = {int(level) for level in self.config.log.enabled_levels}

    @staticmethod
    def response_level(response: LjpResponse) -> int:
        """根据响应状态码计算日志等级。"""

        if response.ok:
            return 5
        if response.status_code < 500:
            return 10
        return 15

    def _emit(self, level: int, message: str) -> None:
        if level == 20:
            return
        if self.enabled_levels and level not in self.enabled_levels:
            return

        if hasattr(self.logger, "log"):
            try:
                self.logger.log(level, message)
                return
            except TypeError:
                pass

        if level >= 15 and hasattr(self.logger, "error"):
            self.logger.error(message)
            return

        if level >= 10:
            for attr in ("warrior", "warning", "warn"):
                if hasattr(self.logger, attr):
                    getattr(self.logger, attr)(message)
                    return

        if level >= 5 and hasattr(self.logger, "info"):
            self.logger.info(message)
            return

        if hasattr(self.logger, "debug"):
            self.logger.debug(message)
            return

        print(message)


class SyncLoggingMiddlewareBase(LoggingMiddlewareBase, SyncMiddleware):
    """同步日志中间件基类。"""

    name = "logging_base_sync"


class AsyncLoggingMiddlewareBase(LoggingMiddlewareBase, AsyncMiddleware):
    """异步日志中间件基类。"""

    name = "logging_base_async"
