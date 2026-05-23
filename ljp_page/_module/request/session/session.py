from __future__ import annotations

import asyncio
import time
from copy import deepcopy
from typing import Any, Mapping

import aiohttp

from ljp_page._module.request.session.base import AsyncRequestModuleBase
from ljp_page._module.request.session.config import AdapterResponse, LjpConfig, LjpResponse, RequestContext
from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page.logger import logger
from ljp_page._core.utils.config import SessionPoolConfig
from ljp_page._core.utils.retry import retry,Constants
from ljp_page._core.utils.other import f_mark

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

    @f_mark('检查session状态，有直接返回，没有则创建')
    async def _resolve_request_session(self,native_session: aiohttp.ClientSession | None) -> aiohttp.ClientSession:
        session = native_session or await self.ensure_session()
        if session.closed:
            raise RuntimeError("aiohttp.ClientSession 已关闭，无法继续发起请求")
        return session

    @f_mark('初始化session，创建session')
    async def ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        async with self._get_session_lock():
            if self._session and not self._session.closed:
                return self._session

            connector = aiohttp.TCPConnector(
                limit=self.config.sessionpool.max_session,
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

    @f_mark('外部获取内部维护的session')
    async def get_native_session(self) -> aiohttp.ClientSession:
        """返回内部维护的原生 aiohttp 会话。"""

        return await self.ensure_session()

    @staticmethod
    def _should_retry(retry_config: Any,original_error: Exception,mapped_error: Exception,) -> bool:
        return retry_config.should_retry(original_error, mapped_error)

    @f_mark('实际使用session发送请求')
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

    @f_mark('构建参数，重试机制')
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
        base_attempt = int(request_kwargs.pop(Constants.ATTEMPT, 0))
        max_retries = max(0, self.config.retry.max_retries)
        delay = max(0.0, self.config.request.request_delay)


        @retry(max_retries,delay=delay)
        async def _send(*a, **kw):

            retry_index = kw[Constants.ATTEMPT]

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

        return await _send()

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

class ASession(Ljp_BaseClass_Logger):
    def __init__(self,config: LjpConfig|None=None,ui=None) -> None:
        super().__init__()
        self.logger = logger
        self.config = config if config else LjpConfig(sessionpool=SessionPoolConfig(max_session=1))
        self.session_queue = asyncio.Queue()
        self.init_mask = False


    async def _init(self):
        if not self.init_mask:
            for _ in range(self.config.sessionpool.max_session):
                self.session_queue.put_nowait(AsyncSession(config=self.config, logger=self.logger))
            self.init_mask = True

    async def _get_req_session(self) -> AsyncSession:
        if not self.init_mask:
            await self._init()
        session = await self.session_queue.get()
        await self.session_queue.put(session)
        return session




    async def request(self, method: str, url: str,*,session, **kwargs: Any) -> LjpResponse:
        if session is None:
            session = await self._get_req_session()
        return await session.request(method, url, **kwargs)


    async def get(self, url: str,*,session = None, **kwargs: Any) -> LjpResponse:
        return await self.request("GET", url,session=session, **kwargs)

    async def post(self, url: str,*,session = None, **kwargs: Any) -> LjpResponse:
        return await self.request("POST", url,session=session, **kwargs)

    async def put(self, url: str,*,session = None, **kwargs: Any) -> LjpResponse:
        return await self.request("PUT", url,session=session, **kwargs)

    async def delete(self, url: str,*,session = None, **kwargs: Any) -> LjpResponse:
        return await self.request("DELETE", url,session=session, **kwargs)

    async def close(self) -> None:
        while not self.session_queue.empty():
            session = await self.session_queue.get()
            await session.close()

__all__ = ["AsyncSession","ASession"]
