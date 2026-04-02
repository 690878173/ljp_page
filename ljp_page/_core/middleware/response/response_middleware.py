# 03-31-20-43-13
"""Response middleware implementations."""

from __future__ import annotations

from typing import Any

from ljp_page._modules.request.Config.models import LjpResponse, RequestContext
from .base import AsyncResponseMiddlewareBase, ResponseMiddlewareBase


class ResponseMiddleware(ResponseMiddlewareBase):
    """Sync response middleware."""

    name = "response"

    def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        return self.attach_trace_id(context, response)


class AsyncResponseMiddleware(AsyncResponseMiddlewareBase):
    """Async response middleware."""

    name = "response_async"

    async def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        return self.attach_trace_id(context, response)
