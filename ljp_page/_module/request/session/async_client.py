"""Asynchronous public HTTP session."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from types import TracebackType
from typing import Unpack

from . import adapter
from .adapter.model import BaseAdapter
from .base import BaseSession
from .config import SessionConfig
from .models import RequestArgs, RequestsReponse
from .types import RequestOptions

_logger = logging.getLogger(__name__)


class AsyncSession(BaseSession):
    """An async requests-style API backed by aiohttp or curl-cffi adapters."""

    @staticmethod
    def _default_adapter() -> BaseAdapter:
        return adapter.AiohttpAdapter()

    def __init__(self, config: SessionConfig | None = None, *, adapter: BaseAdapter | None = None) -> None:
        super().__init__(config, adapter=adapter)
        self._session_lock = asyncio.Lock()

    @property
    def closed(self) -> bool:
        return self.adapter.closed

    async def open(self) -> "AsyncSession":
        if not self.adapter.closed:
            return self
        async with self._session_lock:
            if self.adapter.closed:
                opened = self.adapter.open(self.config, {})
                if inspect.isawaitable(opened):
                    await opened
        return self

    async def close(self) -> None:
        async with self._session_lock:
            closing = self.adapter.close()
            if inspect.isawaitable(closing):
                await closing

    async def __aenter__(self) -> "AsyncSession":
        return await self.open()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def _send(self, request: RequestArgs) -> RequestsReponse:
        if self.adapter.is_async:
            return await self.adapter.send(request)
        return await asyncio.to_thread(self.adapter.send, request)

    async def request(self, method: str, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        started = time.perf_counter()
        retry_limit = max(0, self.config.Retry.max_retries)

        for attempt in range(retry_limit + 1):
            if attempt and self.config.Request.delay:
                await asyncio.sleep(self.config.Request.delay)
            request = self._build_request_args(method, url, kwargs, attempt=attempt)
            await self.open()
            try:
                response = await self._send(request)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                mapped = self.adapter.map_exception(exc, request)
                if attempt >= retry_limit or not self._should_retry(mapped):
                    if mapped is exc:
                        raise
                    raise mapped from exc
                retry_delay = self._retry_delay(attempt + 1)
                if retry_delay:
                    await asyncio.sleep(retry_delay)
                callback_result = self._retry_callback()
                if inspect.isawaitable(callback_result):
                    await callback_result
                _logger.warning("Retrying %s %s (%d/%d)", request.method, request.url, attempt + 1, retry_limit)
                continue
            return self._complete_response(response, elapsed=time.perf_counter() - started, retries=attempt)

        raise RuntimeError("Request retry loop ended unexpectedly")

    async def get(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("DELETE", url, **kwargs)

    async def head(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return await self.request("OPTIONS", url, **kwargs)


__all__ = ["AsyncSession"]
