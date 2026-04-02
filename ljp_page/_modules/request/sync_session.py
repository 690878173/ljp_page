from __future__ import annotations

import time
from typing import Any, Callable, Sequence

import requests

from ljp_page._core.exceptions import LjpRequestException
from ljp_page._core.middleware import (
    RequestMiddleware,
    ResponseMiddleware,
    SyncMiddleware,
    SyncRetryMiddleware,
)

from .adapters import RequestsTransportAdapter, SyncTransportAdapter
from .Config.config import LjpConfig
from ljp_page._modules.request.Config.models import LjpResponse, RequestContext
from .base import SyncRequestModuleBase


class SyncSession(SyncRequestModuleBase):
    """同步请求会话。"""

    def __init__(
        self,
        config: LjpConfig,
        *,
        logger: Any = None,
        adapter: SyncTransportAdapter | None = None,
        middlewares: Sequence[SyncMiddleware] | None = None,
        retry_middleware: SyncRetryMiddleware | None = None,
    ) -> None:
        super().__init__(config=config, logger=logger)
        self.adapter = adapter or RequestsTransportAdapter(self.config)
        self.middlewares = list(
            middlewares if middlewares is not None else self._build_default_middlewares()
        )
        if retry_middleware is not None:
            self.retry_middleware: SyncRetryMiddleware | None = retry_middleware
        elif self.config.middleware.enable_retry_middleware:
            self.retry_middleware = SyncRetryMiddleware(self.config)
        else:
            self.retry_middleware = None

    def _build_default_middlewares(self) -> list[SyncMiddleware]:
        chain: list[SyncMiddleware] = []
        if self.config.middleware.enable_request_middleware:
            chain.append(RequestMiddleware())
        if self.config.middleware.enable_response_middleware:
            chain.append(ResponseMiddleware())
        return chain

    def use(self, middleware: SyncMiddleware) -> "SyncSession":
        self.middlewares.append(middleware)
        return self

    def get_native_session(self) -> requests.Session:
        if isinstance(self.adapter, RequestsTransportAdapter):
            return self.adapter.get_native_session()
        raise TypeError("当前适配器不支持返回 requests.Session")

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
        if isinstance(exc, requests.Timeout):
            category = "timeout"
        elif isinstance(exc, requests.exceptions.SSLError):
            category = "ssl"
        elif isinstance(exc, requests.exceptions.ProxyError):
            category = "proxy"
        elif isinstance(exc, requests.RequestException):
            category = "network"
        else:
            category = "unknown"
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return LjpRequestException(
            "同步请求失败",
            trace_id=context.trace_id,
            method=context.method,
            url=context.url,
            category=category,
            retries=retries,
            elapsed=elapsed,
            status_code=status_code,
            original_exception=exc,
        )

    def _notify_error_middlewares(
        self,
        context: RequestContext,
        error: LjpRequestException,
        middlewares: Sequence[SyncMiddleware],
    ) -> None:
        for middleware in reversed(middlewares):
            middleware.on_error(context, error, self)

    def _send_once(
        self,
        context: RequestContext,
        *,
        attempt: int,
        total_start: float,
    ) -> LjpResponse:
        try:
            adapter_response = self.adapter.send(context)
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
        sender: Callable[[RequestContext], LjpResponse],
        middlewares: Sequence[SyncMiddleware],
    ) -> Callable[[RequestContext], LjpResponse]:
        chain = sender
        for middleware in reversed(middlewares):
            next_handler = chain

            def _make_layer(
                mw: SyncMiddleware,
                nxt: Callable[[RequestContext], LjpResponse],
            ) -> Callable[[RequestContext], LjpResponse]:
                def _layer(ctx: RequestContext) -> LjpResponse:
                    return mw.handle(ctx, nxt, self)

                return _layer

            chain = _make_layer(middleware, next_handler)
        return chain

    def request(
        self,
        method: str,
        url: str,
        *,
        native_session: requests.Session | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        delay = max(0.0, self.config.request.request_delay)
        if delay > 0:
            time.sleep(delay)
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

            def _sender(ctx: RequestContext) -> LjpResponse:
                return self._send_once(ctx, attempt=attempt, total_start=total_start)

            pipeline = self._build_middleware_chain(_sender, active_middlewares)

            try:
                response = pipeline(context)
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
                    self._notify_error_middlewares(context, mapped, active_middlewares)

                if (
                    self.retry_middleware is not None
                    and attempt < total_retries
                    and self.retry_middleware.should_retry_exception(context, mapped)
                ):
                    self.retry_middleware.wait(attempt)
                    continue

                self._record_failure(mapped.elapsed or 0.0, attempt)
                raise mapped from exc

            if (
                self.retry_middleware is not None
                and attempt < total_retries
                and self.retry_middleware.should_retry_response(context, response)
            ):
                self.retry_middleware.wait(attempt)
                continue

            self._record_success(response.elapsed, attempt)
            return response

        raise AssertionError("unreachable")

    def close(self) -> None:
        self.adapter.close()

    def __enter__(self) -> "SyncSession":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


__all__ = ["SyncSession"]
