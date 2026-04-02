# 03-31-20-43-13
"""Retry middleware base classes."""

from __future__ import annotations

import asyncio
import time

from ljp_page._modules.request.Config.config import LjpConfig
from ljp_page._modules.request.Config.models import LjpRequestException, LjpResponse, RequestContext
from ..base import AsyncMiddleware, Ljp_MiddlewareBase, SyncMiddleware


class RetryMiddlewareBase(Ljp_MiddlewareBase):
    """Shared retry policy base class."""

    name = "retry_base"

    def __init__(self, config: LjpConfig) -> None:
        self.config = config

    def calculate_delay(self, attempt: int) -> float:
        return min(
            self.config.retry.max_backoff,
            self.config.retry.backoff_factor * (2**attempt),
        )

    def should_retry_exception(
        self,
        context: RequestContext,
        error: LjpRequestException,
    ) -> bool:
        category = str(getattr(error, "category", "unknown")).lower()
        if category in {item.lower() for item in self.config.retry.ignore_exceptions}:
            return False
        targets = {item.lower() for item in self.config.retry.retry_on_exceptions}
        return not targets or category in targets

    def should_retry_response(
        self,
        context: RequestContext,
        response: LjpResponse,
    ) -> bool:
        retry_on_status = self.config.retry.extra.get(
            "retry_on_status",
            [429, 500, 502, 503, 504],
        )
        return response.status_code in set(retry_on_status)


class SyncRetryMiddlewareBase(RetryMiddlewareBase, SyncMiddleware):
    """Base class for sync retry middleware."""

    name = "retry_base_sync"

    def wait(self, attempt: int) -> None:
        delay = self.calculate_delay(attempt)
        if delay > 0:
            time.sleep(delay)


class AsyncRetryMiddlewareBase(RetryMiddlewareBase, AsyncMiddleware):
    """Base class for async retry middleware."""

    name = "retry_base_async"

    async def wait(self, attempt: int) -> None:
        delay = self.calculate_delay(attempt)
        if delay > 0:
            await asyncio.sleep(delay)
