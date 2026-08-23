"""Adapter-independent session policy and request argument construction."""

from __future__ import annotations

import abc
import inspect
import logging
import threading
from copy import deepcopy
from typing import Mapping, cast
from urllib.parse import urljoin, urlparse

from .adapter.model import BaseAdapter
from .config import SessionConfig
from .models import RequestArgs, RequestsReponse
from .types import CookieMap, HeaderMap, JsonValue, QueryParams, RequestData

_logger = logging.getLogger(__name__)


class BaseSession(abc.ABC):
    """Public session policy layer.

    This class intentionally knows neither a native session type nor a native
    response type. Network I/O, response construction and cookie storage are
    exclusively adapter responsibilities.
    """

    def __init__(self, config: SessionConfig | None = None, *, adapter: BaseAdapter | None = None) -> None:
        self.config = config or SessionConfig()
        self._state_lock = threading.RLock()
        self._adapter = adapter or self._default_adapter()
        self._adapter.set_cookies(self.config.Request.cookies)

    @staticmethod
    @abc.abstractmethod
    def _default_adapter() -> BaseAdapter:
        """Return the backend used when one is not explicitly supplied."""

    @property
    def adapter(self) -> BaseAdapter:
        """The adapter capability boundary; its native session stays private."""

        return self._adapter

    @property
    def headers(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self.config.Request.headers)

    @headers.setter
    def headers(self, values: HeaderMap) -> None:
        with self._state_lock:
            self.config.Request.headers = dict(values)

    def update_headers(self, values: HeaderMap) -> None:
        with self._state_lock:
            self.config.Request.headers = self._merge_headers(self.config.Request.headers, values)

    @property
    def cookies(self) -> dict[str, str]:
        return self._adapter.get_cookies()

    @cookies.setter
    def cookies(self, values: CookieMap) -> None:
        self._adapter.set_cookies(values)

    def update_cookies(self, values: CookieMap) -> None:
        self._adapter.update_cookies(values)

    def clear_cookies(self) -> None:
        self._adapter.clear_cookies()

    @staticmethod
    def _merge_headers(base: HeaderMap, override: HeaderMap | None) -> dict[str, str]:
        """Merge headers using requests' case-insensitive key semantics."""

        merged = dict(base)
        for key, value in (override or {}).items():
            for existing in tuple(merged):
                if existing.lower() == key.lower():
                    del merged[existing]
            merged[str(key)] = str(value)
        return merged

    def _resolve_url(self, url: str) -> str:
        if self.config.Request.base_url and not urlparse(url).scheme:
            return urljoin(self.config.Request.base_url.rstrip("/") + "/", url)
        return url

    def _build_request_args(
        self, method: str, url: str, kwargs: Mapping[str, object], *, attempt: int
    ) -> RequestArgs:
        values = dict(kwargs)
        if "json" in values and "json_data" in values:
            raise TypeError("json and json_data cannot be used together")

        request_headers = values.pop("headers", None)
        request_cookies = values.pop("cookies", None)
        timeout = self.config.Timeout.resolve(values.pop("timeout", None))
        proxy = values.pop("proxy", None)
        proxies = values.pop("proxies", None)
        resolved_proxies, proxy_url = self.config.Proxy.resolve(self._resolve_url(url), proxy, proxies)

        return RequestArgs(
            method=method,
            url=self._resolve_url(url),
            headers=self._merge_headers(self.headers, cast(HeaderMap | None, request_headers)),
            timeout=timeout,
            allow_redirects=bool(values.pop("allow_redirects", self.config.Request.allow_redirects)),
            stream=bool(values.pop("stream", self.config.Request.stream)),
            verify_ssl=bool(values.pop("verify_ssl", self.config.Request.verify_ssl)),
            params=cast(QueryParams | None, values.pop("params", None)),
            data=cast(RequestData | None, values.pop("data", None)),
            json_data=cast(JsonValue | None, values.pop("json", values.pop("json_data", None))),
            cookies=cast(CookieMap | None, request_cookies),
            proxies=cast(Mapping[str, str] | None, resolved_proxies),
            proxy_url=proxy_url,
            extra=values,
            attempt=attempt,
        )

    def _should_retry(self, exc: Exception) -> bool:
        return self.config.Retry.is_matching_exception(exc)

    def _retry_delay(self, attempt: int) -> float:
        return self.config.Retry.get_delay(attempt)

    def _retry_callback(self) -> object | None:
        callback = self.config.Retry.on_retry
        if callback is None:
            return None
        try:
            return callback(self) if inspect.signature(callback).parameters else callback()
        except Exception:
            _logger.exception("Retry callback failed")
            return None

    @staticmethod
    def _complete_response(response: RequestsReponse, *, elapsed: float, retries: int) -> RequestsReponse:
        """Attach orchestration metadata without constructing a response object."""

        response.elapsed = elapsed
        response.retries = retries
        return response


__all__ = ["BaseSession"]
