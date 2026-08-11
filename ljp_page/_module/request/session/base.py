"""BaseSession —— 适配器无关的会话基类。

管理 config / headers / cookies / snapshot / 重试判定，不依赖具体 HTTP 库。
子类只需实现 session 生命周期和 request 的 I/O 差异。
"""

from __future__ import annotations

import abc
import inspect
import logging
import threading
import uuid as _uuid
from copy import deepcopy
from typing import Any, Mapping

from .config import LjpConfig
from .models import AdapterResult, LjpResponse, RequestContext, split_kwargs

_logger = logging.getLogger(__name__)


class BaseSession(abc.ABC):
    """适配器无关的会话基类。"""

    def __init__(
        self,
        config: LjpConfig | None = None,
        *,
        adapter: Any = None,
    ) -> None:
        self.config = config or LjpConfig()
        self._state_lock = threading.RLock()
        self._adapter = adapter or self._default_adapter()
        self._session: Any = None
        self._headers_snapshot: dict[str, str] = {}
        self._cookies_snapshot: dict[str, str] = {}
        self._refresh_snapshots()

    # ═══════════════════════════════════════════════════
    # 子类必须覆写
    # ═══════════════════════════════════════════════════

    @staticmethod
    @abc.abstractmethod
    def _default_adapter() -> Any:
        ...

    @abc.abstractmethod
    def ensure_session(self) -> Any:
        ...

    @abc.abstractmethod
    def _close_impl(self) -> None:
        ...

    # ═══════════════════════════════════════════════════
    # Snapshot
    # ═══════════════════════════════════════════════════

    def _refresh_snapshots(self) -> None:
        with self._state_lock:
            self._headers_snapshot = deepcopy(self.config.headers)
            self._cookies_snapshot = deepcopy(self.config.cookies)

    # ═══════════════════════════════════════════════════
    # Headers & Cookies —— 统一变更入口
    # ═══════════════════════════════════════════════════

    def _on_state_changed(self, key: str) -> None:
        """headers/cookies 变更后的统一同步：刷新快照 → 推到原生 session。"""
        self._refresh_snapshots()
        if self._session is not None:
            snapshot = getattr(self, f"_{key}_snapshot")
            getattr(self._adapter, f"update_{key}")(self._session, snapshot)

    @property
    def headers(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self.config.headers)

    @headers.setter
    def headers(self, values: Mapping[str, str]) -> None:
        with self._state_lock:
            self.config.headers = dict(values)
        self._on_state_changed("headers")

    def update_headers(self, values: Mapping[str, str]) -> None:
        with self._state_lock:
            self.config.headers.update(dict(values))
        self._on_state_changed("headers")

    @property
    def cookies(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self.config.cookies)

    @cookies.setter
    def cookies(self, values: Mapping[str, str]) -> None:
        with self._state_lock:
            self.config.cookies = dict(values)
        self._on_state_changed("cookies")

    def update_cookies(self, values: Mapping[str, str]) -> None:
        with self._state_lock:
            self.config.cookies.update(dict(values))
        self._on_state_changed("cookies")

    def clear_cookies(self) -> None:
        with self._state_lock:
            self.config.cookies.clear()
        self._on_state_changed("cookies")

    # ═══════════════════════════════════════════════════
    # 请求上下文构建
    # ═══════════════════════════════════════════════════

    def _merge_into(self, config_key: str, known: dict[str, Any]) -> dict[str, str]:
        """深拷贝 config 值并与 kwargs 中的同名键合并。"""
        merged = deepcopy(getattr(self.config, config_key))
        custom = known.get(config_key) or {}
        merged.update(custom)
        return merged

    def _build_context(
        self,
        method: str,
        url: str,
        kwargs: Mapping[str, Any],
        *,
        attempt: int,
        native_session: Any = None,
    ) -> RequestContext:
        kws = dict(kwargs)
        known, _passthrough = split_kwargs(kws)

        timeout = self.config.timeout.resolve(known.get("timeout"))
        proxy = known.get("proxy")
        proxies = known.get("proxies")
        resolved_proxies, proxy_url = self.config.proxy.resolve(url, proxy, proxies)

        extra = dict(kws)
        if native_session is not None:
            extra["native_session"] = native_session

        return RequestContext(
            method=method.upper(),
            url=url,
            headers=self._merge_into("headers", known),
            cookies=self._merge_into("cookies", known),
            timeout=timeout,
            allow_redirects=bool(known.get("allow_redirects", self.config.allow_redirects)),
            stream=bool(known.get("stream", self.config.stream)),
            verify_ssl=bool(known.get("verify_ssl", self.config.verify_ssl)),
            proxy_url=proxy_url,
            proxies=resolved_proxies,
            params=known.get("params"),
            data=known.get("data"),
            json_data=known.get("json_data"),
            extra=extra,
            attempt=attempt,
        )

    # ═══════════════════════════════════════════════════
    # 响应构建
    # ═══════════════════════════════════════════════════

    @staticmethod
    def _build_response(
        result: AdapterResult,
        context: RequestContext,
        elapsed: float,
        retries: int,
    ) -> LjpResponse:
        return LjpResponse(
            status_code=result.status_code,
            headers=result.headers,
            encoding=result.encoding,
            content=result.content,
            elapsed=elapsed,
            retries=retries,
            request=context,
        )

    # ═══════════════════════════════════════════════════
    # 重试
    # ═══════════════════════════════════════════════════

    def _should_retry(self, original: Exception, mapped: Exception) -> bool:
        rc = self.config.retry
        return rc.is_matching_exception(original) or rc.is_matching_exception(mapped)

    def _retry_delay(self, attempt: int) -> float:
        return self.config.retry.get_delay(attempt)

    def _call_retry_callback(self) -> None:
        callback = self.config.retry.on_retry
        if callback is None:
            return
        try:
            sig = inspect.signature(callback)
            callback(self) if sig.parameters else callback()
        except Exception:
            _logger.exception("重试回调执行失败")

    # ═══════════════════════════════════════════════════
    # Cookie 持久化
    # ═══════════════════════════════════════════════════

    def _persist_response_cookies(self, cookies: Mapping[str, str]) -> None:
        if cookies:
            self.update_cookies(cookies)


__all__ = ["BaseSession"]
