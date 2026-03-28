# 03-28-16-28-21
"""请求中间件基础协议（同步/异步）。"""

from __future__ import annotations

from abc import ABC
from typing import Any

from ....config.request_config.session_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)


class MiddlewareBase(ABC):
    """中间件根基类。"""

    name = "base"


class SyncMiddleware(MiddlewareBase):
    """同步中间件基础协议。"""

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
