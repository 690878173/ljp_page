from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProxyConfig:
    """代理配置。"""

    http: str | None = None
    https: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_requests(self) -> dict[str, str] | None:
        """返回 requests 代理字典。"""

        proxies: dict[str, str] = {}
        if self.http:
            proxies["http"] = self.http
        if self.https:
            proxies["https"] = self.https
        return proxies or None

    def for_scheme(self, scheme: str) -> str | None:
        """根据协议返回对应代理。"""

        if scheme == "https":
            return self.https or self.http
        return self.http or self.https