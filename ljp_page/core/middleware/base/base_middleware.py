# 03-28-16-49-10
"""请求中间件基础协议（同步/异步）。"""

from __future__ import annotations

from abc import ABC
from typing import Any, Awaitable, Callable

from ....config.request_config.session_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)

SyncNextHandler = Callable[[RequestContext], LjpResponse]
AsyncNextHandler = Callable[[RequestContext], Awaitable[LjpResponse]]


class MiddlewareBase(ABC):
    """中间件根基类。"""

    name = "base"


class SyncMiddleware(MiddlewareBase):
    """同步中间件基础协议。"""

    def handle(
        self,
        context: RequestContext,
        next_handler: SyncNextHandler,
        session: Any,
    ) -> LjpResponse:
        """默认同步中间件链式处理实现。"""

        try:
            self.before_request(context, session)
            response = next_handler(context)
            return self.after_response(context, response, session)
        except LjpRequestException as error:
            self.on_error(context, error, session)
            raise

    def before_request(self, context: RequestContext, session: Any) -> None:
        return None

    def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        return response

    def on_error(
        self,
        context: RequestContext,
        error: LjpRequestException,
        session: Any,
    ) -> None:
        return None


class AsyncMiddleware(MiddlewareBase):
    """异步中间件基础协议。"""

    async def handle(
        self,
        context: RequestContext,
        next_handler: AsyncNextHandler,
        session: Any,
    ) -> LjpResponse:
        """默认异步中间件链式处理实现。"""

        try:
            await self.before_request(context, session)
            response = await next_handler(context)
            return await self.after_response(context, response, session)
        except LjpRequestException as error:
            await self.on_error(context, error, session)
            raise

    async def before_request(self, context: RequestContext, session: Any) -> None:
        return None

    async def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        return response

    async def on_error(
        self,
        context: RequestContext,
        error: LjpRequestException,
        session: Any,
    ) -> None:
        return None


__all__ = [
    "AsyncMiddleware",
    "AsyncNextHandler",
    "MiddlewareBase",
    "SyncMiddleware",
    "SyncNextHandler",
]
