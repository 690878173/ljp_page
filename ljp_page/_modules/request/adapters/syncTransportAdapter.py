import threading
from abc import ABC, abstractmethod

import requests
from requests.adapters import HTTPAdapter
from ..Config.config import LjpConfig
from .config import AdapterResponse
from ljp_page._modules.request.Config.models import RequestContext


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


class RequestsTransportAdapter(SyncTransportAdapter):
    """requests 适配器，内部维护线程本地 Session。"""

    def __init__(self, config: LjpConfig) -> None:
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
        session.verify = self.config.request.verify_ssl
        session.trust_env = self.config.request.trust_env
        session.headers.update(self.config.request.headers)
        session.cookies.update(self.config.request.cookies)
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