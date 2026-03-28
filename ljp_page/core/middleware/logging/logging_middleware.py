# 03-28-16-28-21
"""日志中间件实现。"""

from __future__ import annotations

from typing import Any

from ....config.request_config.session_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)
from .base import AsyncLoggingMiddlewareBase, SyncLoggingMiddlewareBase


class LoggingMiddleware(SyncLoggingMiddlewareBase):
    """同步日志中间件。"""

    name = "logging"

    def before_request(self, context: RequestContext, session: Any) -> None:
        self._emit(
            5,
            (
                f"开始请求 trace_id={context.trace_id} "
                f"{context.method} {context.url} "
                f"attempt={context.attempt + 1} payload={context.safe_payload()}"
            ),
        )

    def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        self._emit(
            self.response_level(response),
            (
                f"请求完成 trace_id={context.trace_id} status={response.status_code} "
                f"elapsed={response.elapsed:.4f}s retries={response.retries}"
            ),
        )
        return response

    def on_error(
        self,
        context: RequestContext,
        error: LjpRequestException,
        session: Any,
    ) -> None:
        self._emit(
            15,
            (
                f"请求失败 trace_id={context.trace_id} method={context.method} "
                f"url={context.url} category={error.category} retries={error.retries}"
            ),
        )


class AsyncLoggingMiddleware(AsyncLoggingMiddlewareBase):
    """异步日志中间件。"""

    name = "logging_async"

    async def before_request(self, context: RequestContext, session: Any) -> None:
        self._emit(
            5,
            (
                f"开始请求 trace_id={context.trace_id} "
                f"{context.method} {context.url} "
                f"attempt={context.attempt + 1} payload={context.safe_payload()}"
            ),
        )

    async def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        self._emit(
            self.response_level(response),
            (
                f"请求完成 trace_id={context.trace_id} status={response.status_code} "
                f"elapsed={response.elapsed:.4f}s retries={response.retries}"
            ),
        )
        return response

    async def on_error(
        self,
        context: RequestContext,
        error: LjpRequestException,
        session: Any,
    ) -> None:
        self._emit(
            15,
            (
                f"请求失败 trace_id={context.trace_id} method={context.method} "
                f"url={context.url} category={error.category} retries={error.retries}"
            ),
        )
