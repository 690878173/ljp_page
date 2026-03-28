# 03-28-16-28-21
"""请求中间件基类。"""

from __future__ import annotations

from ..base import AsyncMiddleware, SyncMiddleware
from ....config.request_config.session_config import RequestContext


class RequestMiddlewareBase(SyncMiddleware):
    """同步请求中间件基类。"""

    name = "request_base"

    @staticmethod
    def prepare_context(context: RequestContext) -> None:
        """标准化请求方法并注入 trace_id。"""

        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)


class AsyncRequestMiddlewareBase(AsyncMiddleware):
    """异步请求中间件基类。"""

    name = "request_base_async"

    @staticmethod
    def prepare_context(context: RequestContext) -> None:
        """标准化请求方法并注入 trace_id。"""

        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)
