# 03-28-16-28-21
"""响应中间件基类。"""

from __future__ import annotations

from ljp_page.modules.request.config.request_config import LjpResponse, RequestContext
from ..base import Ljp_AsyncMiddleware, Ljp_SyncMiddleware


class ResponseMiddlewareBase(Ljp_SyncMiddleware):
    """同步响应中间件基类。"""

    name = "response_base"

    @staticmethod
    def attach_trace_id(context: RequestContext, response: LjpResponse) -> LjpResponse:
        """统一补充 trace_id 响应头。"""

        response.headers.setdefault("X-Trace-Id", context.trace_id)
        return response


class AsyncResponseMiddlewareBase(Ljp_AsyncMiddleware):
    """异步响应中间件基类。"""

    name = "response_base_async"

    @staticmethod
    def attach_trace_id(context: RequestContext, response: LjpResponse) -> LjpResponse:
        """统一补充 trace_id 响应头。"""

        response.headers.setdefault("X-Trace-Id", context.trace_id)
        return response
