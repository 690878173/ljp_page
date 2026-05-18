# 04-26-10-19-51
"""异步请求会话实现。"""

from __future__ import annotations

import asyncio
import time
from copy import deepcopy
from typing import Any, Mapping

import aiohttp

from .base import AsyncRequestModuleBase
from .config import AdapterResponse, LjpConfig, LjpResponse, RequestContext


class AsyncSession(AsyncRequestModuleBase):
    """基于 aiohttp 的独立异步会话封装。"""

    def __init__(
        self,
        config: LjpConfig | None = None,
        *,
        logger: Any = None,
    ) -> None:
        super().__init__(config=config if config is not None else LjpConfig(), logger=logger)
        self._session: aiohttp.ClientSession | None = None
        self._session_lock: asyncio.Lock | None = None
        self._cookie_store = deepcopy(self.config.request.cookies)
        try:
            self._jar = aiohttp.CookieJar(unsafe=True)
        except Exception as  e:
            raise ValueError('不能在同步环境初始化')
        self._jar.update_cookies(self._cookie_store)

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
        return self._session is None or self._session.closed

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
        self._jar.update_cookies(values)
        if self._session and not self._session.closed:
            self._session.cookie_jar.update_cookies(values)

    def clear_cookies(self) -> None:
        """清空当前会话维护的 Cookie。"""

        with self._state_lock:
            self._cookie_store.clear()
            self.config.request.cookies.clear()
        self._sync_cookies_to_native()

    def _get_session_lock(self) -> asyncio.Lock:
        if self._session_lock is None:
            self._session_lock = asyncio.Lock()
        return self._session_lock

    def _sync_headers_to_native(self) -> None:
        if self._session and not self._session.closed:
            self._session.headers.clear()
            self._session.headers.update(self.headers)

    def _sync_cookies_to_native(self) -> None:
        with self._state_lock:
            cookie_snapshot = deepcopy(self._cookie_store)

        self._jar.clear()
        self._jar.update_cookies(cookie_snapshot)

        if self._session and not self._session.closed:
            self._session.cookie_jar.clear()
            self._session.cookie_jar.update_cookies(cookie_snapshot)

    def _store_cookies(self, cookies: Mapping[str, str]) -> None:
        if not cookies:
            return
        with self._state_lock:
            self._cookie_store.update(dict(cookies))
            self.config.request.cookies = deepcopy(self._cookie_store)
        self._sync_cookies_to_native()

    @staticmethod
    def _build_timeout(timeout: tuple[float, float]) -> aiohttp.ClientTimeout:
        connect_timeout, read_timeout = timeout
        return aiohttp.ClientTimeout(
            total=connect_timeout + read_timeout,
            connect=connect_timeout,
            sock_connect=connect_timeout,
            sock_read=read_timeout,
        )

    async def ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        async with self._get_session_lock():
            if self._session and not self._session.closed:
                return self._session

            connector = aiohttp.TCPConnector(
                limit=self.config.sessionpool.max_connections,
                limit_per_host=self.config.sessionpool.max_connections_per_host,
                ssl=self.config.request.verify_ssl,
            )
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                cookie_jar=self._jar,
                connector=connector,
                timeout=self.config.timeout.aiohttp_timeout,
                trust_env=self.config.request.trust_env,
            )
            return self._session

    async def get_native_session(self) -> aiohttp.ClientSession:
        """返回内部维护的原生 aiohttp 会话。"""

        return await self.ensure_session()

    @staticmethod
    def _should_retry(
        retry_config: Any,
        original_error: Exception,
        mapped_error: Exception,
    ) -> bool:
        return retry_config.should_retry(original_error, mapped_error)

    async def _send_once(
        self,
        context: RequestContext,
        *,
        native_session: aiohttp.ClientSession | None,
        total_start: float,
    ) -> LjpResponse:
        request_session = await self._resolve_request_session(native_session)
        if context.cookies:
            request_session.cookie_jar.update_cookies(context.cookies)

        passthrough_kwargs = {
            key: value
            for key, value in context.extra.items()
            if key != "native_session" and key!= 'return_type'
        }
        try:
            async with request_session.request(
                context.method,
                context.url,
                params=context.params,
                data=context.data,
                json=context.json_data,
                headers=context.headers,
                cookies=context.cookies,
                timeout=self._build_timeout(context.timeout),
                allow_redirects=context.allow_redirects,
                ssl=context.verify_ssl,
                proxy=context.proxy_url,

            ) as response:
                content = await response.read()
                adapter_response = AdapterResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    content=content,
                    encoding=response.charset,
                    cookies=self._extract_cookies(request_session),
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise self._map_exception(exc, context) from exc

        self._store_cookies(adapter_response.cookies)
        return self._build_response(
            context=context,
            adapter_response=adapter_response,
            elapsed=time.perf_counter() - total_start,
            retries=context.attempt,
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        native_session: aiohttp.ClientSession | None = None,
        **kwargs: Any,
    ) -> LjpResponse:
        total_start = time.perf_counter()
        request_kwargs = dict(kwargs)
        base_attempt = int(request_kwargs.pop("retry_attempt", 0))
        max_retries = max(0, self.config.retry.max_retries)
        delay = max(0.0, self.config.request.request_delay)
        for retry_index in range(max_retries + 1):
            if delay > 0:
                await asyncio.sleep(delay)

            attempt = base_attempt + retry_index
            context = self._build_context(
                method,
                url,
                request_kwargs,
                attempt=attempt,
                native_session=native_session,
            )

            try:
                return await self._send_once(
                    context,
                    native_session=native_session,
                    total_start=total_start,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                mapped_error = self._map_exception(exc, context)
                if retry_index >= max_retries or not self.config.retry.should_retry(
                    exc,
                    mapped_error
                ):
                    raise mapped_error from exc

                await self.config.retry.handle_delay(retry_index + 1)
                await self.config.retry.call_callback(self)

        raise RuntimeError("异步请求重试流程异常结束")

    async def open(self) -> AsyncSession:
        await self.ensure_session()
        return self

    async def close(self) -> None:
        async with self._get_session_lock():
            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None

    async def __aenter__(self) -> AsyncSession:
        return await self.open()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


__all__ = ["AsyncSession"]
