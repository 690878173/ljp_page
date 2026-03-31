# 03-28-16-49-10
"""请求中间件基础协议（同步/异步）。"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict

from ljp_page.modules.request.config.request_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)
_STR_BASE = 'base'

@dataclass
class Ljp_MiddlewareContext:
    input: Any
    output: Any
    state: Dict[str, Any] = field(default_factory=dict)



SyncNextHandler = Callable[[RequestContext], LjpResponse]
AsyncNextHandler = Callable[[RequestContext], Awaitable[LjpResponse]]


class Ljp_MiddlewareBase(ABC):
    """中间件根基类。"""

    name = _STR_BASE


class Ljp_SyncMiddleware(Ljp_MiddlewareBase):

    def handle(self,
               ctx:Ljp_MiddlewareContext,
               next_handler):
        try:
            ctx = self.before(ctx)
            response = next_handler(ctx)
            return self.after(ctx, response)
        except Exception as error:
            self.on_error(ctx, error)
            raise

    def before(self, ctx: Ljp_MiddlewareContext):
        return ctx

    def after(self, ctx, response):
        return response

    def on_error(self, ctx, error):
        return None


class Ljp_AsyncMiddleware(Ljp_MiddlewareBase):

    async def handle(
            self,
            ctx,
            next_handler: AsyncNextHandler,
    ):
        try:
            await self.before(ctx)
            response = await next_handler(ctx)
            return await self.after(ctx, response)
        except Exception as error:
            await self.on_error(ctx, error)
            raise

    async def before(self, ctx):
        return ctx

    async def after(self, ctx, response):
        return response

    async def on_error(self, ctx, error):
        return None
__all__ = [
    "AsyncNextHandler",
    "Ljp_MiddlewareBase",
    "SyncNextHandler",
    "Ljp_SyncMiddleware",
    "Ljp_MiddlewareContext",
]
