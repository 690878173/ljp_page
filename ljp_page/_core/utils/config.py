from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, Mapping
from urllib.parse import urlparse

from .retry.ljp_retry import RetryConfig

if TYPE_CHECKING:
    import aiohttp

@dataclass
class TimeoutConfig:
    """连接与读取超时配置。"""

    connect: float = 20.0
    read: float = 10.0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def requests_timeout(self) -> tuple[float, float]:
        """requests 适配超时。"""

        return self.connect, self.read


    def get_aiohttp_timeout(self, timeout: tuple[float,float] | None = None) -> aiohttp.ClientTimeout:
        """aiohttp 适配超时。"""
        import aiohttp
        if timeout is None:
            connect,read = self.connect, self.read
        else:
            connect,read = timeout
        return aiohttp.ClientTimeout(
            total=connect + read,
            connect=connect,
            sock_connect=connect,
            sock_read=read,
        )

    def resolve(self,timeout: Any) -> tuple[float, float]:
        if timeout is None:
            return self.connect, self.read
        if isinstance(timeout, TimeoutConfig):
            return timeout.connect, timeout.read
        if isinstance(timeout, (int, float)):
            numeric = float(timeout)
            return numeric, numeric
        if isinstance(timeout, tuple) and len(timeout) == 2:
            return float(timeout[0]), float(timeout[1])
        raise TypeError(f"不支持的 timeout 类型: {type(timeout).__name__}")

@dataclass
class SessionPoolConfig:
    """连接池配置。"""

    max_session: int = 10
    max_keepalive_connections: int = 20
    max_connections_per_host: int = 20
    extra: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProxyConfig:
    """代理配置。"""

    http: str | None = None
    https: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_requests(self) -> dict[str, str] | None:
        """转换为 requests 代理字典。"""

        proxies: dict[str, str] = {}
        if self.http:
            proxies["http"] = self.http
        if self.https:
            proxies["https"] = self.https
        return proxies or None

    def for_scheme(self, scheme: str) -> str | None:
        """根据协议获取代理地址。"""

        if scheme == "https":
            return self.https or self.http
        return self.http or self.https

    def resolve(self,
        url: str,
        proxy: str | None,
        proxies: Mapping[str, str] | None,)-> tuple[dict[str, str] | None, str | None]:
        scheme = urlparse(url).scheme or "http"
        if proxy:
            return {scheme: proxy}, proxy
        if proxies:
            proxy_dict = dict(proxies)
            return proxy_dict, proxy_dict.get(scheme)
        proxy_dict = self.as_requests()
        return proxy_dict, self.for_scheme(scheme)


