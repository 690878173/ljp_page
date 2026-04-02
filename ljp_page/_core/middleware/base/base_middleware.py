# 03-31-20-21-05
"""请求中间件基础协议（同步/异步）。"""

from __future__ import annotations

from abc import ABC
from typing import Any, Awaitable, Callable

from ljp_page._modules.request.Config.models import LjpRequestException, LjpResponse, RequestContext

SyncNextHandler = Callable[[RequestContext], LjpResponse]
AsyncNextHandler = Callable[[RequestContext], Awaitable[LjpResponse]]


class Ljp_MiddlewareBase(ABC):
    """中间件根基类。"""

    name = "base"


class SyncMiddleware(Ljp_MiddlewareBase):
    """同步中间件基类。"""

    def handle(
        self,
        context: RequestContext,
        next_handler: SyncNextHandler,
        session: Any,
    ) -> LjpResponse:
        try:
            self.before_request(context, session)
            response = next_handler(context)
            return self.after_response(context, response, session)
        except Exception as error:
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
        error: Exception | LjpRequestException,
        session: Any,
    ) -> None:
        return None


class AsyncMiddleware(Ljp_MiddlewareBase):
    """异步中间件基类。"""

    async def handle(
        self,
        context: RequestContext,
        next_handler: AsyncNextHandler,
        session: Any,
    ) -> LjpResponse:
        try:
            await self.before_request(context, session)
            response = await next_handler(context)
            return await self.after_response(context, response, session)
        except Exception as error:
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
        error: Exception | LjpRequestException,
        session: Any,
    ) -> None:
        return None


# 兼容别名
Ljp_SyncMiddleware = SyncMiddleware
Ljp_AsyncMiddleware = AsyncMiddleware

__all__ = [
    "AsyncMiddleware",
    "AsyncNextHandler",
    "Ljp_AsyncMiddleware",
    "Ljp_MiddlewareBase",
    "Ljp_SyncMiddleware",
    "SyncMiddleware",
    "SyncNextHandler",
]
