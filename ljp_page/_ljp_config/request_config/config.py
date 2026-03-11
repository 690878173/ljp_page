from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, is_dataclass
from threading import RLock
from typing import Any, Mapping

import aiohttp


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)


@dataclass
class RetryConfig:
    """Retry policy shared by sync and async sessions."""

    total: int = 3
    backoff_factor: float = 0.5
    status_forcelist: list[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
    allowed_methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
    )


@dataclass
class TimeoutConfig:
    """Connection and read timeout values."""

    connect: float = 5.0
    read: float = 10.0

    @property
    def requests_timeout(self) -> tuple[float, float]:
        """Return a ``requests``-compatible timeout tuple."""

        return self.connect, self.read

    @property
    def aiohttp_timeout(self) -> aiohttp.ClientTimeout:
        """Return an ``aiohttp`` timeout object."""

        return aiohttp.ClientTimeout(
            total=self.connect + self.read,
            connect=self.connect,
            sock_connect=self.connect,
            sock_read=self.read,
        )

@dataclass
class ProxyConfig:
    """Proxy configuration for both runtime modes."""

    http: str | None = None
    https: str | None = None

    def as_requests(self) -> dict[str, str] | None:
        """Return ``requests`` proxies."""

        proxies: dict[str, str] = {}
        if self.http:
            proxies["http"] = self.http
        if self.https:
            proxies["https"] = self.https
        return proxies or None

    def for_scheme(self, scheme: str) -> str | None:
        """Return a single proxy URL for the requested scheme."""

        if scheme == "https":
            return self.https or self.http
        return self.http or self.https

@dataclass
class PoolConfig:
    """Connection pool settings."""

    max_connections: int = 100
    max_keepalive_connections: int = 20
    max_connections_per_host: int = 20


@dataclass
class RequestConfig:
    """Runtime-agnostic request configuration."""

    base_url: str = ""
    verify_ssl: bool = True
    allow_redirects: bool = True
    stream: bool = False # 流式响应
    request_delay: float = 0.0 # 请求延迟
    trust_env: bool = False # 读取系统代理
    headers: dict[str, str] = field(
        default_factory=lambda: {"User-Agent": DEFAULT_USER_AGENT}
    )
    cookies: dict[str, str] = field(default_factory=dict)
    retry: RetryConfig = field(default_factory=RetryConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    pool: PoolConfig = field(default_factory=PoolConfig)

_CONFIG_LOCK = RLock()
_GLOBAL_REQUEST_CONFIG = RequestConfig()

def _ensure_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping, got {type(value).__name__}")
    return value


def _merge_component(component: Any, updates: Any) -> Any:
    if updates is None:
        return component
    if is_dataclass(updates):
        return deepcopy(updates)
    mapping = _ensure_mapping(type(component).__name__, updates)
    merged = deepcopy(component)
    for key, value in mapping.items():
        if not hasattr(merged, key):
            raise KeyError(f"Unsupported config field: {type(component).__name__}.{key}")
        setattr(merged, key, value)
    return merged


def merge_request_config(base: RequestConfig, **overrides: Any) -> RequestConfig:
    """Return a cloned config with overrides merged in."""

    merged = deepcopy(base)
    for key, value in overrides.items():
        if value is None:
            continue
        if key == "delay":
            key = "request_delay"
        if key == "proxies":
            key = "proxy"
        if not hasattr(merged, key):
            raise KeyError(f"Unsupported config field: {key}")
        if key == "timeout":
            if isinstance(value, TimeoutConfig):
                setattr(merged, key, deepcopy(value))
                continue
            if isinstance(value, (int, float)):
                numeric = float(value)
                setattr(merged, key, TimeoutConfig(connect=numeric, read=numeric))
                continue
            if isinstance(value, tuple) and len(value) == 2:
                setattr(
                    merged,
                    key,
                    TimeoutConfig(connect=float(value[0]), read=float(value[1])),
                )
                continue
        if key in {"retry", "timeout", "proxy", "pool"}:
            setattr(merged, key, _merge_component(getattr(merged, key), value))
            continue
        if key in {"headers", "cookies"}:
            current = deepcopy(getattr(merged, key))
            current.update(dict(_ensure_mapping(key, value)))
            setattr(merged, key, current)
            continue
        setattr(merged, key, value)
    return merged


def get_request_config(**overrides: Any) -> RequestConfig:
    """Return the current global request config snapshot."""

    with _CONFIG_LOCK:
        config = deepcopy(_GLOBAL_REQUEST_CONFIG)
    if not overrides:
        return config
    return merge_request_config(config, **overrides)


def update_request_config(**updates: Any) -> RequestConfig:
    """Merge updates into the global request config and return the new snapshot."""

    global _GLOBAL_REQUEST_CONFIG
    with _CONFIG_LOCK:
        _GLOBAL_REQUEST_CONFIG = merge_request_config(_GLOBAL_REQUEST_CONFIG, **updates)
        return deepcopy(_GLOBAL_REQUEST_CONFIG)


def set_request_config(config: RequestConfig) -> RequestConfig:
    """Replace the global request config."""

    global _GLOBAL_REQUEST_CONFIG
    with _CONFIG_LOCK:
        _GLOBAL_REQUEST_CONFIG = deepcopy(config)
        return deepcopy(_GLOBAL_REQUEST_CONFIG)


def reset_request_config() -> RequestConfig:
    """Restore the global request config to defaults."""

    return set_request_config(RequestConfig())


__all__ = [
    "DEFAULT_USER_AGENT",
    "PoolConfig",
    "ProxyConfig",
    "RequestConfig",
    "RetryConfig",
    "TimeoutConfig",
    "get_request_config",
    "merge_request_config",
    "reset_request_config",
    "set_request_config",
    "update_request_config",
]

