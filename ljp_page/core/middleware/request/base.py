
"""请求中间件基类。"""

from __future__ import annotations

from ..base import Ljp_SyncMiddleware,Ljp_AsyncMiddleware

from ljp_page.modules.request.config.request_config import RequestContext


class RequestMiddlewareBase(Ljp_SyncMiddleware):
    """同步请求中间件基类。"""

    name = "request_base"

    @staticmethod
    def prepare_context(context: RequestContext) -> None:
        """标准化请求方法并注入 trace_id。"""

        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)


class AsyncRequestMiddlewareBase(Ljp_AsyncMiddleware):
    """异步请求中间件基类。"""

    name = "request_base_async"

    @staticmethod
    def prepare_context(context: RequestContext) -> None:
        """标准化请求方法并注入 trace_id。"""

        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)
