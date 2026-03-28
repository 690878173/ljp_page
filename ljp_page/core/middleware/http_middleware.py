"""03-28-15-07-30 请求中间件系统（同步/异步）。"""

from __future__ import annotations

import asyncio
import time
from abc import ABC
from typing import Any

from ...config.request_config import RequestConfig
from ...config.request_config.session_config import (
    LjpRequestException,
    LjpResponse,
    RequestContext,
)


class MiddlewareBase(ABC):
    """中间件基类。"""

    name = "base"


class SyncMiddleware(MiddlewareBase):
    """同步中间件基类。"""

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
    """异步中间件基类。"""

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


class RequestMiddleware(SyncMiddleware):
    """请求中间件：补充 trace_id、标准化 method。"""

    name = "request"

    def before_request(self, context: RequestContext, session: Any) -> None:
        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)


class AsyncRequestMiddleware(AsyncMiddleware):
    """异步请求中间件：补充 trace_id、标准化 method。"""

    name = "request_async"

    async def before_request(self, context: RequestContext, session: Any) -> None:
        context.method = context.method.upper()
        context.headers.setdefault("X-Trace-Id", context.trace_id)


class ResponseMiddleware(SyncMiddleware):
    """响应中间件：补充统一响应头。"""

    name = "response"

    def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        response.headers.setdefault("X-Trace-Id", context.trace_id)
        return response


class AsyncResponseMiddleware(AsyncMiddleware):
    """异步响应中间件：补充统一响应头。"""

    name = "response_async"

    async def after_response(
        self,
        context: RequestContext,
        response: LjpResponse,
        session: Any,
    ) -> LjpResponse:
        response.headers.setdefault("X-Trace-Id", context.trace_id)
        return response


class LoggingMiddleware(SyncMiddleware):
    """日志中间件：基于数字等级打印请求生命周期。"""

    name = "logging"

    def __init__(self, config: RequestConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger

    def _emit(self, level: int, message: str) -> None:
        # 兼容自定义日志器：优先使用 log(level, message)，否则退化到常见方法名。
        if hasattr(self.logger, "log"):
            try:
                self.logger.log(level, message)
                return
            except TypeError:
                pass
        if level >= 15 and hasattr(self.logger, "error"):
            self.logger.error(message)
            return
        if level >= 10 and hasattr(self.logger, "warning"):
            self.logger.warning(message)
            return
        if hasattr(self.logger, "info"):
            self.logger.info(message)
            return
        print(message)

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
        level = 5 if response.ok else (10 if response.status_code < 500 else 15)
        self._emit(
            level,
            (
                f"响应完成 trace_id={context.trace_id} status={response.status_code} "
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


class AsyncLoggingMiddleware(AsyncMiddleware):
    """异步日志中间件。"""

    name = "logging_async"

    def __init__(self, config: RequestConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger

    def _emit(self, level: int, message: str) -> None:
        if hasattr(self.logger, "log"):
            try:
                self.logger.log(level, message)
                return
            except TypeError:
                pass
        if level >= 15 and hasattr(self.logger, "error"):
            self.logger.error(message)
            return
        if level >= 10 and hasattr(self.logger, "warning"):
            self.logger.warning(message)
            return
        if hasattr(self.logger, "info"):
            self.logger.info(message)
            return
        print(message)

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
        level = 5 if response.ok else (10 if response.status_code < 500 else 15)
        self._emit(
            level,
            (
                f"响应完成 trace_id={context.trace_id} status={response.status_code} "
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


class SyncRetryMiddleware(SyncMiddleware):
    """同步重试中间件。"""

    name = "retry_sync"

    def __init__(self, config: RequestConfig) -> None:
        self.config = config

    def should_retry_response(self, context: RequestContext, response: LjpResponse) -> bool:
        retry = self.config.retry
        return (
            context.method in retry.allowed_methods
            and response.status_code in retry.status_forcelist
        )

    def should_retry_exception(self, context: RequestContext, error: LjpRequestException) -> bool:
        retry = self.config.retry
        return (
            context.method in retry.allowed_methods
            and error.category in retry.retry_on_exceptions
        )

    def wait(self, attempt: int) -> None:
        delay = min(
            self.config.retry.max_backoff,
            self.config.retry.backoff_factor * (2 ** attempt),
        )
        if delay > 0:
            time.sleep(delay)


class AsyncRetryMiddleware(AsyncMiddleware):
    """异步重试中间件。"""

    name = "retry_async"

    def __init__(self, config: RequestConfig) -> None:
        self.config = config

    def should_retry_response(self, context: RequestContext, response: LjpResponse) -> bool:
        retry = self.config.retry
        return (
            context.method in retry.allowed_methods
            and response.status_code in retry.status_forcelist
        )

    def should_retry_exception(self, context: RequestContext, error: LjpRequestException) -> bool:
        retry = self.config.retry
        return (
            context.method in retry.allowed_methods
            and error.category in retry.retry_on_exceptions
        )

    async def wait(self, attempt: int) -> None:
        delay = min(
            self.config.retry.max_backoff,
            self.config.retry.backoff_factor * (2 ** attempt),
        )
        if delay > 0:
            await asyncio.sleep(delay)
