# 04-26-10-19-51
"""同步请求会话实现。"""

from __future__ import annotations

import asyncio
import inspect
import time
from copy import deepcopy
from typing import Any, Mapping

import requests

from ljp_page._module.request.session.base import SyncRequestModuleBase
from ljp_page._module.request.session.config import AdapterResponse, LjpConfig, LjpResponse, RequestContext


class SyncSession(SyncRequestModuleBase):
    """基于 requests 的独立同步会话封装。"""

    def __init__(
        self,
        config: LjpConfig | None = None,
        *,
        logger: Any = None,
    ) -> None:
        super().__init__(config=config if config is not None else LjpConfig(), logger=logger)
        self._session: requests.Session | None = None
        self._cookie_store = deepcopy(self.config.request.cookies)

    @property
    def headers(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self.config.request.headers)

    @headers.setter
    def headers(self, values: Mapping[str, str]) -> None:
        with self._state_lock:
            self.config.request.headers = dict(values)
        self._sync_headers_to_native()

    @property
    def cookies(self) -> dict[str, str]:
        with self._state_lock:
            return deepcopy(self._cookie_store)

    @cookies.setter
    def cookies(self, values: Mapping[str, str]) -> None:
        with self._state_lock:
            cookie_values = dict(values)
            self._cookie_store = cookie_values
            self.config.request.cookies = deepcopy(cookie_values)
        self._sync_cookies_to_native()

    @property
    def closed(self) -> bool:
        return self._session is None

    def update_headers(self, values: Mapping[str, str]) -> None:
        """增量更新默认请求头。"""

        with self._state_lock:
            self.config.request.headers.update(dict(values))
        self._sync_headers_to_native()

    def update_cookies(self, values: Mapping[str, str]) -> None:
        """增量更新默认 Cookie。"""

        with self._state_lock:
            self._cookie_store.update(dict(values))
            self.config.request.cookies = deepcopy(self._cookie_store)
        self._sync_cookies_to_native()

    def clear_cookies(self) -> None:
        """清空当前会话维护的 Cookie。"""

        with self._state_lock:
            self._cookie_store.clear()
            self.config.request.cookies.clear()
        self._sync_cookies_to_native()

    def _sync_headers_to_native(self) -> None:
        if self._session is not None:
            self._session.headers.clear()
            self._session.headers.update(self.headers)

    def _sync_cookies_to_native(self) -> None:
        with self._state_lock:
            cookie_snapshot = deepcopy(self._cookie_store)

        if self._session is not None:
            self._session.cookies.clear()
            self._session.cookies.update(cookie_snapshot)

    def _store_cookies(self, cookies: Mapping[str, str]) -> None:
        if not cookies:
            return
        with self._state_lock:
            self._cookie_store.update(dict(cookies))
            self.config.request.cookies = deepcopy(self._cookie_store)
        self._sync_cookies_to_native()

    def ensure_session(self) -> requests.Session:
        if self._session is not None:
            return self._session

        session = requests.Session()
        session.headers.update(self.headers)
        session.cookies.update(self.cookies)
        session.trust_env = self.config.request.trust_env
        self._session = session
        return self._session

    def get_native_session(self) -> requests.Session:
        """返回内部维护的原生 requests 会话。"""

        return self.ensure_session()

    @staticmethod
    def _should_retry(
        retry_config: Any,
        original_error: Exception,
        mapped_error: Exception,
    ) -> bool:
        return (
            retry_config.is_matching_exception(original_error)
            or retry_config.is_matching_exception(mapped_error)
        )

    def _handle_retry_delay(self, attempt: int) -> None:
        wait_time = self.config.retry.calculate_delay(attempt)
        if wait_time > 0:
            time.sleep(wait_time)

    def _call_retry_callback(self) -> None:
        callback = self.config.retry.on_retry
        if callback is None:
            return

        try:
            result = callback(self)
        except TypeError as exc:
            error_msg = str(exc)
            if (
                "takes 1 positional argument but 2 were given" in error_msg
                or "takes 0 positional arguments but 1 was given" in error_msg
            ):
                result = callback()
            else:
                raise

        if inspect.isawaitable(result):
            asyncio.run(result)

    def _send_once(
        self,
        context: RequestContext,
        *,
        native_session: requests.Session | None,
        total_start: float,
    ) -> LjpResponse:
        request_session = self._resolve_request_session(native_session)
        if context.cookies:
            request_session.cookies.update(context.cookies)

        passthrough_kwargs = {
            key: value
            for key, value in context.extra.items()
            if key != "native_session"
        }

        try:
            with request_session.request(
                context.method,
                context.url,
                params=context.params,
                data=context.data,
                json=context.json_data,
                headers=context.headers,
                cookies=context.cookies,
                timeout=context.timeout,
                allow_redirects=context.allow_redirects,
                verify=context.verify_ssl,
                proxies=context.proxies,
                stream=context.stream,
                **passthrough_kwargs,
            ) as response:
                adapter_response = AdapterResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=response.content,
                    encoding=response.encoding,
                    cookies=self._extract_cookies(request_session),
                )
        except Exception as exc:
            raise self._map_exception(exc, context) from exc

        self._store_cookies(adapter_response.cookies)
        return self._build_response(
            context=context,
            adapter_response=adapter_response,
            elapsed=time.perf_counter() - total_start,
            retries=context.attempt,
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        native_session: requests.Session | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        request_kwargs = dict(kwargs)
        base_attempt = int(request_kwargs.pop("retry_attempt", 0))
        max_retries = max(0, self.config.retry.max_retries)
        delay = max(0.0, self.config.request.request_delay)

        for retry_index in range(max_retries + 1):
            if delay > 0:
                time.sleep(delay)

            attempt = base_attempt + retry_index
            context = self._build_context(
                method,
                url,
                request_kwargs,
                attempt=attempt,
                native_session=native_session,
            )

            try:
                return self._send_once(
                    context,
                    native_session=native_session,
                    total_start=total_start,
                )
            except Exception as exc:
                mapped_error = self._map_exception(exc, context)
                if retry_index >= max_retries or not self._should_retry(
                    self.config.retry,
                    exc,
                    mapped_error,
                ):
                    raise mapped_error from exc

                self._handle_retry_delay(retry_index + 1)
                self._call_retry_callback()

        raise RuntimeError("同步请求重试流程异常结束")

    def open(self) -> SyncSession:
        self.ensure_session()
        return self

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> SyncSession:
        return self.open()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


__all__ = ["SyncSession"]
