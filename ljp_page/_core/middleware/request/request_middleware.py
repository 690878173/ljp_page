# 03-31-20-43-13
"""Request middleware implementations."""

from __future__ import annotations

from typing import Any

from ljp_page._modules.request.Config.models import RequestContext
from .base import AsyncRequestMiddlewareBase, RequestMiddlewareBase


class RequestMiddleware(RequestMiddlewareBase):
    """Sync request middleware."""

    name = "request"

    def before_request(self, context: RequestContext, session: Any) -> None:
        self.prepare_context(context)


class AsyncRequestMiddleware(AsyncRequestMiddlewareBase):
    """Async request middleware."""

    name = "request_async"

    async def before_request(self, context: RequestContext, session: Any) -> None:
        self.prepare_context(context)
