# 03-31-20-43-13
"""Response middleware base classes."""

from __future__ import annotations

from ljp_page.config.request_config.session_config import LjpResponse, RequestContext
from ..base import Ljp_AsyncMiddleware, Ljp_SyncMiddleware


class ResponseMiddlewareBase(Ljp_SyncMiddleware):
    """Base class for sync response middleware."""

    name = "response_base"

    @staticmethod
    def attach_trace_id(context: RequestContext, response: LjpResponse) -> LjpResponse:
        response.headers.setdefault("X-Trace-Id", context.trace_id)
        return response


class AsyncResponseMiddlewareBase(Ljp_AsyncMiddleware):
    """Base class for async response middleware."""

    name = "response_base_async"

    @staticmethod
    def attach_trace_id(context: RequestContext, response: LjpResponse) -> LjpResponse:
        response.headers.setdefault("X-Trace-Id", context.trace_id)
        return response
