"""03-28-15-07-30 请求适配器：隔离 requests 与 aiohttp。"""

from __future__ import annotations

import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import aiohttp
import requests
from requests.adapters import HTTPAdapter

from ...config.request_config import RequestConfig
from ...config.request_config.session_config import RequestContext


@dataclass(frozen=True)
class AdapterResponse:
    """适配器统一响应结构。"""

    status_code: int
    headers: dict[str, str]
    content: bytes
    encoding: str | None
    cookies: dict[str, str]


class SyncTransportAdapter(ABC):
    """同步传输适配器接口。"""

    @abstractmethod
    def sync_defaults(self, headers: dict[str, str], cookies: dict[str, str]) -> None:
        """同步默认请求头与 Cookie。"""

    @abstractmethod
    def send(self, context: RequestContext) -> AdapterResponse:
        """发送同步请求。"""

    @abstractmethod
    def close(self) -> None:
        """释放资源。"""


class AsyncTransportAdapter(ABC):
    """异步传输适配器接口。"""

    @abstractmethod
    def sync_defaults(self, headers: dict[str, str], cookies: dict[str, str]) -> None:
        """同步默认请求头与 Cookie。"""

    @abstractmethod
    async def send(self, context: RequestContext) -> AdapterResponse:
        """发送异步请求。"""

    @abstractmethod
    async def close(self) -> None:
        """释放资源。"""


class RequestsTransportAdapter(SyncTransportAdapter):
    """requests 适配器，内部维护线程本地 Session。"""

    def __init__(self, config: RequestConfig) -> None:
        self.config = config
        self._thread_local = threading.local()
        self._native_sessions: list[requests.Session] = []
        self._lock = threading.RLock()

    def _new_native_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=self.config.pool.max_connections,
            pool_maxsize=self.config.pool.max_keepalive_connections,
            max_retries=0,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.verify = self.config.verify_ssl
        session.trust_env = self.config.trust_env
        session.headers.update(self.config.headers)
        session.cookies.update(self.config.cookies)
        proxies = self.config.proxy.as_requests()
        if proxies:
            session.proxies.update(proxies)
        with self._lock:
            self._native_sessions.append(session)
        return session

    def get_native_session(self) -> requests.Session:
        native = getattr(self._thread_local, "session", None)
        if native is None:
            native = self._new_native_session()
            self._thread_local.session = native
        return native

    def sync_defaults(self, headers: dict[str, str], cookies: dict[str, str]) -> None:
        with self._lock:
            sessions = list(self._native_sessions)
        for session in sessions:
            session.headers.clear()
            session.headers.update(headers)
            session.cookies.update(cookies)

    def send(self, context: RequestContext) -> AdapterResponse:
        native = context.extra.get("native_session") or self.get_native_session()
        native.cookies.update(context.cookies)
        passthrough_kwargs = {
            key: value
            for key, value in context.extra.items()
            if key != "native_session"
        }
        response = native.request(
            context.method,
            context.url,
            params=context.params,
            data=context.data,
            json=context.json_data,
            headers=context.headers,
            cookies=context.cookies,
            timeout=context.timeout,
            allow_redirects=context.allow_redirects,
            stream=context.stream,
            verify=context.verify_ssl,
            proxies=context.proxies,
            **passthrough_kwargs,
        )
        return AdapterResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            encoding=response.encoding,
            cookies=native.cookies.get_dict(),
        )

    def close(self) -> None:
        with self._lock:
            sessions = list(self._native_sessions)
            self._native_sessions.clear()
        for session in sessions:
            session.close()
        if hasattr(self._thread_local, "session"):
            del self._thread_local.session


class AiohttpTransportAdapter(AsyncTransportAdapter):
    """aiohttp 适配器，内部维护可复用 ClientSession。"""

    def __init__(self, config: RequestConfig) -> None:
        self.config = config
        self._session: aiohttp.ClientSession | None = None
        self._session_lock: asyncio.Lock | None = None

    def _get_session_lock(self) -> asyncio.Lock:
        if self._session_lock is None:
            self._session_lock = asyncio.Lock()
        return self._session_lock

    async def ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session
        async with self._get_session_lock():
            if self._session and not self._session.closed:
                return self._session
            connector = aiohttp.TCPConnector(
                limit=self.config.pool.max_connections,
                limit_per_host=self.config.pool.max_connections_per_host,
                ssl=self.config.verify_ssl,
            )
            jar = aiohttp.CookieJar(unsafe=True)
            jar.update_cookies(self.config.cookies)
            self._session = aiohttp.ClientSession(
                headers=self.config.headers,
                cookie_jar=jar,
                connector=connector,
                timeout=self.config.timeout.aiohttp_timeout,
                trust_env=self.config.trust_env,
            )
            return self._session

    def sync_defaults(self, headers: dict[str, str], cookies: dict[str, str]) -> None:
        if self._session and not self._session.closed:
            self._session.headers.clear()
            self._session.headers.update(headers)
            self._session.cookie_jar.update_cookies(cookies)

    async def send(self, context: RequestContext) -> AdapterResponse:
        native = context.extra.get("native_session") or await self.ensure_session()
        native.cookie_jar.update_cookies(context.cookies)
        passthrough_kwargs = {
            key: value
            for key, value in context.extra.items()
            if key != "native_session"
        }
        async with native.request(
            context.method,
            context.url,
            params=context.params,
            data=context.data,
            json=context.json_data,
            headers=context.headers,
            cookies=context.cookies,
            timeout=aiohttp.ClientTimeout(
                total=context.timeout[0] + context.timeout[1],
                connect=context.timeout[0],
                sock_connect=context.timeout[0],
                sock_read=context.timeout[1],
            ),
            allow_redirects=context.allow_redirects,
            ssl=context.verify_ssl,
            proxy=context.proxy_url,
            **passthrough_kwargs,
        ) as response:
            content = await response.read()
            cookies = {cookie.key: cookie.value for cookie in native.cookie_jar}
            return AdapterResponse(
                status_code=response.status,
                headers=dict(response.headers),
                content=content,
                encoding=response.charset,
                cookies=cookies,
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
