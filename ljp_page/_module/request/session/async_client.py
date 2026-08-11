"""异步会话——基于适配器模式，不硬编码 aiohttp。"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, TYPE_CHECKING

from .base import BaseSession
from .adapter import AiohttpAdapter
from .config import LjpConfig
from .models import LjpResponse


if TYPE_CHECKING:
    from .adapter import CurlCffiAdapter,RequestsAdapter

_logger = logging.getLogger(__name__)


class AsyncSession(BaseSession):
    """可插拔适配器的异步 HTTP 会话。"""

    @staticmethod
    def _default_adapter() -> AiohttpAdapter:
        return AiohttpAdapter()

    def __init__(
        self,
        config: LjpConfig | None = None,
        *,
        adapter: AiohttpAdapter |CurlCffiAdapter|RequestsAdapter| None = None,
    ) -> None:
        super().__init__(config, adapter=adapter)
        self._session_lock = asyncio.Lock()

    # ── 生命周期 ──

    async def ensure_session(self) -> Any:
        if self._session is not None and not self._session.closed:
            return self._session
        async with self._session_lock:
            if self._session is not None and not self._session.closed:
                return self._session
            self._session = self._adapter.create_session(
                headers=self._headers_snapshot,
                cookies=self._cookies_snapshot,
                config=self.config,
            )
            return self._session

    async def get_native_session(self) -> Any:
        return await self.ensure_session()

    async def open(self) -> "AsyncSession":
        await self.ensure_session()
        return self

    @property
    def closed(self) -> bool:
        return self._session is None or self._session.closed

    async def close(self) -> None:
        await self._close_impl()

    async def _close_impl(self) -> None:
        async with self._session_lock:
            await self._adapter.close(self._session)
            self._session = None

    async def __aenter__(self) -> "AsyncSession":
        return await self.open()

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ── 请求 ──

    async def request(
        self,
        method: str,
        url: str,
        *,
        native_session: Any = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        max_retries = max(0, self.config.retry.max_retries)
        delay = max(0.0, self.config.delay)

        for attempt in range(max_retries + 1):
            if attempt > 0 and delay > 0:
                await asyncio.sleep(delay)

            context = self._build_context(
                method, url, kwargs, attempt=attempt, native_session=native_session,
            )
            session = native_session or await self.ensure_session()

            try:
                result = await self._adapter.send(session, context)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                mapped = self._adapter.map_exception(exc, context)
                if attempt >= max_retries or not self._should_retry(exc, mapped):
                    raise mapped
                retry_delay = self._retry_delay(attempt + 1)
                if retry_delay > 0:
                    await asyncio.sleep(retry_delay)
                self._call_retry_callback()
                _logger.warning(
                    "请求重试 [%s %s] attempt=%d/%d",
                    method.upper(), url, attempt + 1, max_retries,
                )
                continue

            self._persist_response_cookies(result.cookies)
            return self._build_response(result, context, time.perf_counter() - total_start, attempt)

        raise RuntimeError("异步请求重试流程异常结束")

    # ── 便捷方法 ──

    async def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url, **kwargs)


__all__ = ["AsyncSession"]
