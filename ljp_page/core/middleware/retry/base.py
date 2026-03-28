# 03-28-16-28-21
"""重试中间件基类。"""

from __future__ import annotations

import asyncio
import time

from ....config.request_config import RequestConfig
from ....config.request_config.session_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)
from ..base import AsyncMiddleware, MiddlewareBase, SyncMiddleware


class RetryMiddlewareBase(MiddlewareBase):
    """重试中间件通用基类。"""

    name = "retry_base"

    def __init__(self, config: RequestConfig) -> None:
        self.config = config

    def should_retry_response(self, context: RequestContext, response: LjpResponse) -> bool:
        retry = self.config.retry
        return (
            context.method in retry.allowed_methods
            and response.status_code in retry.status_forcelist
        )

    def should_retry_exception(self, context: RequestContext, error: LjpRequestException) -> bool:
        retry = self.config.retry
        return (
            context.method in retry.allowed_methods
            and error.category in retry.retry_on_exceptions
        )

    def calculate_delay(self, attempt: int) -> float:
        """根据指数退避策略计算等待时长。"""

        return min(
            self.config.retry.max_backoff,
            self.config.retry.backoff_factor * (2**attempt),
        )


class SyncRetryMiddlewareBase(RetryMiddlewareBase, SyncMiddleware):
    """同步重试中间件基类。"""

    name = "retry_base_sync"

    def wait(self, attempt: int) -> None:
        delay = self.calculate_delay(attempt)
        if delay > 0:
            time.sleep(delay)


class AsyncRetryMiddlewareBase(RetryMiddlewareBase, AsyncMiddleware):
    """异步重试中间件基类。"""

    name = "retry_base_async"

    async def wait(self, attempt: int) -> None:
        delay = self.calculate_delay(attempt)
        if delay > 0:
            await asyncio.sleep(delay)
