# 04-01-20-16-00
"""异步请求会话实现。"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Sequence

import aiohttp

from ljp_page._core.exceptions import LjpRequestException
from ljp_page._core.middleware import (
    AsyncMiddleware,
    AsyncRequestMiddleware,
    AsyncResponseMiddleware,
    AsyncRetryMiddleware,
)

from .adapters import AiohttpTransportAdapter, AsyncTransportAdapter
from .Config.config import LjpConfig
from ljp_page._modules.request.Config.models import LjpResponse, RequestContext
from .base import AsyncRequestModuleBase


class AsyncSession(AsyncRequestModuleBase):
    """异步请求会话。"""

    def __init__(
        self,
        config: LjpConfig,
        *,
        logger: Any = None,
        adapter: AsyncTransportAdapter | None = None,
        middlewares: Sequence[AsyncMiddleware] | None = None,
        retry_middleware: AsyncRetryMiddleware | None = None,
    ) -> None:
        super().__init__(config=config, logger=logger)
        self.adapter = adapter or AiohttpTransportAdapter(self.config)
        self.middlewares = list(
            middlewares if middlewares is not None else self._build_default_middlewares()
        )
        if retry_middleware is not None:
            self.retry_middleware: AsyncRetryMiddleware | None = retry_middleware
        elif self.config.middleware.enable_retry_middleware:
            self.retry_middleware = AsyncRetryMiddleware(self.config)
        else:
            self.retry_middleware = None

    def _build_default_middlewares(self) -> list[AsyncMiddleware]:
        chain: list[AsyncMiddleware] = []
        if self.config.middleware.enable_request_middleware:
            chain.append(AsyncRequestMiddleware())
        if self.config.middleware.enable_response_middleware:
            chain.append(AsyncResponseMiddleware())
        return chain

    def use(self, middleware: AsyncMiddleware) -> "AsyncSession":
        self.middlewares.append(middleware)
        return self

    async def get_native_session(self) -> aiohttp.ClientSession:
        if isinstance(self.adapter, AiohttpTransportAdapter):
            return await self.adapter.ensure_session()
        raise TypeError("当前适配器不支持返回 aiohttp.ClientSession")

    def _sync_headers_to_native(self) -> None:
        self.adapter.sync_defaults(self.headers, self.cookies)

    def _sync_cookies_to_native(self) -> None:
        self.adapter.sync_defaults(self.headers, self.cookies)

    @staticmethod
    def _map_exception(
        exc: Exception,
        *,
        context: RequestContext,
        retries: int,
        elapsed: float,
    ) -> LjpRequestException:
        if isinstance(exc, asyncio.TimeoutError):
            category = "timeout"
        elif isinstance(exc, aiohttp.ClientSSLError):
            category = "ssl"
        elif isinstance(exc, aiohttp.ClientProxyConnectionError):
            category = "proxy"
        elif isinstance(exc, aiohttp.ClientError):
            category = "network"
        else:
            category = "unknown"
        status_code = getattr(exc, "status", None)
        return LjpRequestException(
            "异步请求失败",
            trace_id=context.trace_id,
            method=context.method,
            url=context.url,
            category=category,
            retries=retries,
            elapsed=elapsed,
            status_code=status_code,
            original_exception=exc,
        )

    async def _notify_error_middlewares(
        self,
        context: RequestContext,
        error: LjpRequestException,
        middlewares: Sequence[AsyncMiddleware],
    ) -> None:
        for middleware in reversed(middlewares):
            await middleware.on_error(context, error, self)

    async def _send_once(
        self,
        context: RequestContext,
        *,
        attempt: int,
        total_start: float,
    ) -> LjpResponse:
        try:
            adapter_response = await self.adapter.send(context)
        except Exception as exc:
            raise self._map_exception(
                exc,
                context=context,
                retries=attempt,
                elapsed=time.perf_counter() - total_start,
            ) from exc

        self._store_cookies(adapter_response.cookies)
        return self._build_response(
            context=context,
            adapter_response=adapter_response,
            elapsed=time.perf_counter() - total_start,
            retries=attempt,
        )

    def _build_middleware_chain(
        self,
        sender: Callable[[RequestContext], Awaitable[LjpResponse]],
        middlewares: Sequence[AsyncMiddleware],
    ) -> Callable[[RequestContext], Awaitable[LjpResponse]]:
        chain = sender
        for middleware in reversed(middlewares):
            next_handler = chain

            def _make_layer(
                mw: AsyncMiddleware,
                nxt: Callable[[RequestContext], Awaitable[LjpResponse]],
            ) -> Callable[[RequestContext], Awaitable[LjpResponse]]:
                async def _layer(ctx: RequestContext) -> LjpResponse:
                    return await mw.handle(ctx, nxt, self)

                return _layer

            chain = _make_layer(middleware, next_handler)
        return chain

    async def request(
        self,
        method: str,
        url: str,
        *,
        native_session: aiohttp.ClientSession | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        delay = max(0.0, self.config.request.request_delay)
        if delay > 0:
            await asyncio.sleep(delay)
        request_middlewares = kwargs.pop("middlewares", None)
        active_middlewares = (
            list(request_middlewares)
            if request_middlewares is not None
            else list(self.middlewares)
        )

        total_retries = self.config.retry.total if self.retry_middleware else 0
        for attempt in range(total_retries + 1):
            context = self._build_context(
                method,
                url,
                kwargs,
                attempt=attempt,
                native_session=native_session,
            )

            async def _sender(ctx: RequestContext) -> LjpResponse:
                return await self._send_once(
                    ctx,
                    attempt=attempt,
                    total_start=total_start,
                )

            pipeline = self._build_middleware_chain(_sender, active_middlewares)

            try:
                response = await pipeline(context)
            except Exception as exc:
                if isinstance(exc, LjpRequestException):
                    mapped = exc
                else:
                    mapped = self._map_exception(
                        exc,
                        context=context,
                        retries=attempt,
                        elapsed=time.perf_counter() - total_start,
                    )
                    await self._notify_error_middlewares(
                        context,
                        mapped,
                        active_middlewares,
                    )

                if (
                    self.retry_middleware is not None
                    and attempt < total_retries
                    and self.retry_middleware.should_retry_exception(context, mapped)
                ):
                    await self.retry_middleware.wait(attempt)
                    continue

                self._record_failure(mapped.elapsed or 0.0, attempt)
                raise mapped from exc

            if (
                self.retry_middleware is not None
                and attempt < total_retries
                and self.retry_middleware.should_retry_response(context, response)
            ):
                await self.retry_middleware.wait(attempt)
                continue

            self._record_success(response.elapsed, attempt)
            return response

        raise AssertionError("unreachable")

    async def open(self) -> "AsyncSession":
        await self.get_native_session()
        return self

    async def close(self) -> None:
        await self.adapter.close()

    async def __aenter__(self) -> "AsyncSession":
        return await self.open()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


__all__ = ["AsyncSession"]
