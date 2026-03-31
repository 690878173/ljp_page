from dataclasses import dataclass, field
from typing import Any

import aiohttp


@dataclass
class TimeoutConfig:
    """连接与读取超时配置。"""

    connect: float = 10.0
    read: float = 10.0
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def requests_timeout(self) -> tuple[float, float]:
        """返回 requests 使用的超时元组。"""

        return self.connect, self.read

    @property
    def aiohttp_timeout(self) -> aiohttp.ClientTimeout:
        """返回 aiohttp 使用的超时对象。"""

        return aiohttp.ClientTimeout(
            total=self.connect + self.read,
            connect=self.connect,
            sock_connect=self.connect,
            sock_read=self.read,
        )