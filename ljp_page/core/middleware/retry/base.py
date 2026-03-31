# 03-28-16-28-21
"""重试中间件基类。"""

from __future__ import annotations

import asyncio
import time

from ljp_page.modules.request.config.request_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)
from ljp_page.config.Ljp_config import LjpConfig
from ..base import AsyncMiddleware, Ljp_MiddlewareBase, SyncMiddleware


class RetryMiddlewareBase(Ljp_MiddlewareBase):
    """重试中间件通用基类。"""

    name = "retry_base"

    def __init__(self, config: LjpConfig) -> None:
        self.config = config

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


