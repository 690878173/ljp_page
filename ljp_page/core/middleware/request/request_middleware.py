# 03-28-16-28-21
"""请求中间件实现。"""

from __future__ import annotations

from typing import Any

from ....config.request_config.session_config import RequestContext
from .base import AsyncRequestMiddlewareBase, RequestMiddlewareBase


class RequestMiddleware(RequestMiddlewareBase):
    """同步请求中间件。"""

    name = "request"

    def before_request(self, context: RequestContext, session: Any) -> None:
        self.prepare_context(context)


class AsyncRequestMiddleware(AsyncRequestMiddlewareBase):
    """异步请求中间件。"""

    name = "request_async"

    async def before_request(self, context: RequestContext, session: Any) -> None:
        self.prepare_context(context)
