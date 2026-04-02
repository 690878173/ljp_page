import asyncio
from abc import ABC, abstractmethod

import aiohttp

from ..Config.config import LjpConfig
from .config import AdapterResponse
from ljp_page._modules.request.Config.models import RequestContext





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



class AiohttpTransportAdapter(AsyncTransportAdapter):
    """aiohttp 适配器，内部维护可复用 ClientSession。"""

    def __init__(self, config: LjpConfig) -> None:
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
                ssl=self.config.request.verify_ssl,
            )
            jar = aiohttp.CookieJar(unsafe=True)
            jar.update_cookies(self.config.request.cookies)
            self._session = aiohttp.ClientSession(
                headers=self.config.request.headers,
                cookie_jar=jar,
                connector=connector,
                timeout=self.config.timeout.aiohttp_timeout,
                trust_env=self.config.request.trust_env,
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


