"""Synchronous public HTTP session."""

from __future__ import annotations

import logging
import time
from types import TracebackType
from typing import Unpack

from . import adapter
from .adapter.model import BaseAdapter
from .base import BaseSession
from .config import SessionConfig
from .models import RequestsReponse
from .types import RequestOptions

_logger = logging.getLogger(__name__)


class SyncSession(BaseSession):
    """A requests-compatible synchronous API backed by a pluggable adapter."""

    @staticmethod
    def _default_adapter() -> BaseAdapter:
        return adapter.RequestsAdapter()

    def __init__(self, config: SessionConfig | None = None, *, adapter: BaseAdapter | None = None) -> None:
        super().__init__(config, adapter=adapter)
        if self.adapter.is_async:
            raise TypeError("SyncSession requires a synchronous adapter")

    @property
    def closed(self) -> bool:
        return self.adapter.closed

    def open(self) -> "SyncSession":
        self.adapter.open(self.config, {})
        return self

    def close(self) -> None:
        self.adapter.close()

    def __enter__(self) -> "SyncSession":
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def request(self, method: str, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        started = time.perf_counter()
        retry_limit = max(0, self.config.Retry.max_retries)

        for attempt in range(retry_limit + 1):
            if attempt and self.config.Request.delay:
                time.sleep(self.config.Request.delay)
            request = self._build_request_args(method, url, kwargs, attempt=attempt)
            self.open()
            try:
                response = self.adapter.send(request)
            except Exception as exc:
                mapped = self.adapter.map_exception(exc, request)
                if attempt >= retry_limit or not self._should_retry(mapped):
                    if mapped is exc:
                        raise
                    raise mapped from exc
                retry_delay = self._retry_delay(attempt + 1)
                if retry_delay:
                    time.sleep(retry_delay)
                self._retry_callback()
                _logger.warning("Retrying %s %s (%d/%d)", request.method, request.url, attempt + 1, retry_limit)
                continue
            return self._complete_response(response, elapsed=time.perf_counter() - started, retries=attempt)

        raise RuntimeError("Request retry loop ended unexpectedly")

    def get(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Unpack[RequestOptions]) -> RequestsReponse:
        return self.request("OPTIONS", url, **kwargs)


__all__ = ["SyncSession"]
