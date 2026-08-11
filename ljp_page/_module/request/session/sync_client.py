"""同步会话——基于适配器模式，不硬编码 requests。"""

from __future__ import annotations

import logging
import time
from typing import Any

from .adapter import RequestsAdapter
from .base import BaseSession
from .config import LjpConfig
from .models import LjpResponse

_logger = logging.getLogger(__name__)


class SyncSession(BaseSession):
    """可插拔适配器的同步 HTTP 会话。"""

    @staticmethod
    def _default_adapter() -> RequestsAdapter:
        return RequestsAdapter()

    def __init__(
        self,
        config: LjpConfig | None = None,
        *,
        adapter: RequestsAdapter | None = None,
    ) -> None:
        super().__init__(config, adapter=adapter)

    # ── 生命周期 ──

    def ensure_session(self) -> Any:
        if self._session is not None:
            return self._session
        self._session = self._adapter.create_session(
            headers=self._headers_snapshot,
            cookies=self._cookies_snapshot,
            config=self.config,
        )
        return self._session

    def get_native_session(self) -> Any:
        return self.ensure_session()

    def open(self) -> "SyncSession":
        self.ensure_session()
        return self

    @property
    def closed(self) -> bool:
        return self._session is None

    def close(self) -> None:
        self._close_impl()

    def _close_impl(self) -> None:
        self._adapter.close(self._session)
        self._session = None

    def __enter__(self) -> "SyncSession":
        return self.open()

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    # ── 请求 ──

    def request(
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
                time.sleep(delay)

            context = self._build_context(
                method, url, kwargs, attempt=attempt, native_session=native_session,
            )
            session = native_session or self.ensure_session()

            try:
                result = self._adapter.send(session, context)
            except Exception as exc:
                mapped = self._adapter.map_exception(exc, context)
                if attempt >= max_retries or not self._should_retry(exc, mapped):
                    raise mapped from exc
                retry_delay = self._retry_delay(attempt + 1)
                if retry_delay > 0:
                    time.sleep(retry_delay)
                self._call_retry_callback()
                _logger.warning(
                    "请求重试 [%s %s] attempt=%d/%d",
                    method.upper(), url, attempt + 1, max_retries,
                )
                continue

            self._persist_response_cookies(result.cookies)
            return self._build_response(result, context, time.perf_counter() - total_start, attempt)

        raise RuntimeError("同步请求重试流程异常结束")

    # ── 便捷方法 ──

    def get(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> LjpResponse:
        return self.request("DELETE", url, **kwargs)


__all__ = ["SyncSession"]
