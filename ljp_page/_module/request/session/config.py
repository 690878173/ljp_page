"""New nested configuration model for the adapter-based session API."""

from __future__ import annotations

from dataclasses import dataclass, field

from ljp_page._core.utils.config import ProxyConfig, SessionPoolConfig, TimeoutConfig
from ljp_page._core.utils.retry import RetryConfig

from ..config import USER_AGENTS


@dataclass
class RequestsConfig:
    """Request defaults used by :class:`BaseSession1`."""

    headers: dict[str, str] = field(default_factory=lambda: {"User-Agent": USER_AGENTS[-1]})
    cookies: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    allow_redirects: bool = True
    stream: bool = False
    delay: float = 0.0
    trust_env: bool = True
    base_url: str = ""
    extra: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.headers = dict(self.headers)
        self.cookies = dict(self.cookies)
        self.delay = max(0.0, float(self.delay))


@dataclass
class SessionConfig:
    """The new session configuration contract.

    The four original sections remain explicit so business code never needs to
    know which backend is serving a request.
    """

    Request: RequestsConfig = field(default_factory=RequestsConfig)
    Timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    Retry: RetryConfig = field(default_factory=RetryConfig)
    Proxy: ProxyConfig = field(default_factory=ProxyConfig)
    SessionPool: SessionPoolConfig = field(default_factory=SessionPoolConfig)
    extra: dict[str, object] = field(default_factory=dict)


__all__ = ["RequestsConfig", "SessionConfig","RetryConfig", "ProxyConfig", "SessionPoolConfig", "TimeoutConfig"]
