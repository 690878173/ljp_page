# 03-28-16-28-21
"""重试中间件实现。"""

from __future__ import annotations

from .base import AsyncRetryMiddlewareBase, SyncRetryMiddlewareBase


class SyncRetryMiddleware(SyncRetryMiddlewareBase):
    """同步重试中间件。"""

    name = "retry_sync"


class AsyncRetryMiddleware(AsyncRetryMiddlewareBase):
    """异步重试中间件。"""

    name = "retry_async"
