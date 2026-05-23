from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from .retry.retry import RetryConfig

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

    @property
    def aiohttp_timeout(self) -> aiohttp.ClientTimeout:
        """aiohttp 适配超时。"""
        import aiohttp
        return aiohttp.ClientTimeout(
            total=self.connect + self.read,
            connect=self.connect,
            sock_connect=self.connect,
            sock_read=self.read,
        )

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


