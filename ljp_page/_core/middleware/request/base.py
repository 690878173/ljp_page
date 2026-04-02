# 03-31-20-43-13
"""Request middleware base classes."""

from __future__ import annotations

from ljp_page._modules.request.Config.models import RequestContext
from ..base import Ljp_AsyncMiddleware, Ljp_SyncMiddleware


class RequestMiddlewareBase(Ljp_SyncMiddleware):
    """Base class for sync request middleware."""

    name = "request_base"

    @staticmethod
    def prepare_context(context: RequestContext) -> None:
        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)


class AsyncRequestMiddlewareBase(Ljp_AsyncMiddleware):
    """Base class for async request middleware."""

    name = "request_base_async"

    @staticmethod
    def prepare_context(context: RequestContext) -> None:
        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)
