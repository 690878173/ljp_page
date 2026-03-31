
"""响应中间件实现。"""

from __future__ import annotations

from typing import Any

from ljp_page.modules.request.config.request_config import LjpResponse, RequestContext
from .base import AsyncResponseMiddlewareBase, ResponseMiddlewareBase


class ResponseMiddleware(ResponseMiddlewareBase):
    """同步响应中间件。"""

    name = "response"

    def after(
        self,
        context: RequestContext,
        response: LjpResponse,
    ) -> LjpResponse:
        return self.attach_trace_id(context, response)


class AsyncResponseMiddleware(AsyncResponseMiddlewareBase):
    """异步响应中间件。"""

    name = "response_async"

    async def after(
        self,
        context: RequestContext,
        response: LjpResponse,
    ) -> LjpResponse:
        return self.attach_trace_id(context, response)
