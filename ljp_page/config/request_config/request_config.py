"""03-28-15-07-30 请求系统全局配置中心。"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, is_dataclass
from threading import RLock
from typing import Any, Mapping

import aiohttp

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
)

DEFAULT_LEVEL_NAMES: dict[int, str] = {
    1: "DEBUG",
    2: "TRACE",
    3: "VERBOSE",
    4: "NOTICE",
    5: "INFO",
    6: "STEP",
    7: "EVENT",
    8: "CHECK",
    9: "RISK",
    10: "WARRIOR",
    11: "WARN_PLUS",
    12: "ALERT",
    13: "ISSUE",
    14: "SEVERE",
    15: "ERROR",
    16: "FATAL",
    17: "PANIC",
    18: "SECURITY",
    19: "EMERGENCY",
    20: "OFF",
}

DEFAULT_LEVEL_ALIASES: dict[str, int] = {
    "debug": 1,
    "trace": 2,
    "verbose": 3,
    "notice": 4,
    "info": 5,
    "step": 6,
    "event": 7,
    "check": 8,
    "risk": 9,
    "warrior": 10,
    "warning": 10,
    "warn": 10,
    "alert": 12,
    "issue": 13,
    "error": 15,
    "fatal": 16,
    "panic": 17,
    "security": 18,
    "emergency": 19,
    "critical": 19,
    "off": 20,
}


@dataclass
class TimeoutConfig:
    """连接与读取超时配置。"""

    connect: float = 10.0
    read: float = 10.0

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


@dataclass
class RetryConfig:
    """重试策略配置。"""

    total: int = 2
    backoff_factor: float = 0.5
    max_backoff: float = 8.0
    status_forcelist: list[int] = field(
        default_factory=lambda: [408, 429, 500, 502, 503, 504]
    )
    allowed_methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
    )
    retry_on_exceptions: list[str] = field(
        default_factory=lambda: ["timeout", "network", "proxy", "ssl"]
    )


@dataclass
class ProxyConfig:
    """代理配置。"""

    http: str | None = None
    https: str | None = None

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


@dataclass
class PoolConfig:
    """连接池配置。"""

    max_connections: int = 100
    max_keepalive_connections: int = 20
    max_connections_per_host: int = 20


@dataclass
class LogConfig:
    """日志等级与输出策略配置。"""

    default_level: int = 5
    enabled_levels: list[int] = field(default_factory=lambda: list(range(1, 20)))
    level_names: dict[int, str] = field(default_factory=lambda: deepcopy(DEFAULT_LEVEL_NAMES))
    aliases: dict[str, int] = field(default_factory=lambda: deepcopy(DEFAULT_LEVEL_ALIASES))
    log_file_path: str | None = None
    output_console: bool = True
    output_file: bool = True


@dataclass
class MiddlewareConfig:
    """内置中间件开关配置。"""

    enable_request_middleware: bool = True
    enable_response_middleware: bool = True
    enable_logging_middleware: bool = True
    enable_retry_middleware: bool = True


@dataclass
class RequestConfig:
    """请求系统统一配置。"""

    base_url: str = ""
    verify_ssl: bool = True
    allow_redirects: bool = True
    stream: bool = False
    request_delay: float = 0.0
    trust_env: bool = True
    headers: dict[str, str] = field(
        default_factory=lambda: {"User-Agent": DEFAULT_USER_AGENT}
    )
    cookies: dict[str, str] = field(default_factory=dict)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    pool: PoolConfig = field(default_factory=PoolConfig)
    log: LogConfig = field(default_factory=LogConfig)
    middleware: MiddlewareConfig = field(default_factory=MiddlewareConfig)


def _ensure_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} 必须是 Mapping，实际为 {type(value).__name__}")
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
            raise KeyError(f"不支持的配置字段: {type(component).__name__}.{key}")
        setattr(merged, key, value)
    return merged


def merge_request_config(base: RequestConfig, **overrides: Any) -> RequestConfig:
    """基于基础配置合并覆盖项。"""

    merged = deepcopy(base)
    for raw_key, value in overrides.items():
        if value is None:
            continue

        key = raw_key
        if key == "delay":
            key = "request_delay"
        if key == "proxies":
            key = "proxy"
        if key == "log_level":
            merged.log.default_level = int(value)
            continue
        if key == "enabled_levels":
            merged.log.enabled_levels = [int(level) for level in value]
            continue

        if not hasattr(merged, key):
            raise KeyError(f"不支持的配置字段: {key}")

        if key == "timeout":
            if isinstance(value, TimeoutConfig):
                merged.timeout = deepcopy(value)
                continue
            if isinstance(value, (int, float)):
                numeric = float(value)
                merged.timeout = TimeoutConfig(connect=numeric, read=numeric)
                continue
            if isinstance(value, tuple) and len(value) == 2:
                merged.timeout = TimeoutConfig(
                    connect=float(value[0]),
                    read=float(value[1]),
                )
                continue

        if key in {"retry", "timeout", "proxy", "pool", "log", "middleware"}:
            setattr(merged, key, _merge_component(getattr(merged, key), value))
            continue

        if key in {"headers", "cookies"}:
            current = deepcopy(getattr(merged, key))
            current.update(dict(_ensure_mapping(key, value)))
            setattr(merged, key, current)
            continue

        setattr(merged, key, value)
    return merged


class RequestConfigManager:
    """线程安全的请求配置管理器。"""

    def __init__(self) -> None:
        self._lock = RLock()
        self._config = RequestConfig()

    def get(self, **overrides: Any) -> RequestConfig:
        """读取配置快照，可附加覆盖项。"""

        with self._lock:
            snapshot = deepcopy(self._config)
        if not overrides:
            return snapshot
        return merge_request_config(snapshot, **overrides)

    def set(self, config: RequestConfig) -> RequestConfig:
        """替换全局配置。"""

        with self._lock:
            self._config = deepcopy(config)
            return deepcopy(self._config)

    def update(self, **updates: Any) -> RequestConfig:
        """合并并更新全局配置。"""

        with self._lock:
            self._config = merge_request_config(self._config, **updates)
            return deepcopy(self._config)

    def reset(self) -> RequestConfig:
        """重置为默认配置。"""

        return self.set(RequestConfig())


_GLOBAL_MANAGER = RequestConfigManager()


def get_request_config(**overrides: Any) -> RequestConfig:
    """读取全局请求配置。"""

    return _GLOBAL_MANAGER.get(**overrides)


def update_request_config(**updates: Any) -> RequestConfig:
    """更新全局请求配置。"""

    return _GLOBAL_MANAGER.update(**updates)


def set_request_config(config: RequestConfig) -> RequestConfig:
    """设置全局请求配置。"""

    return _GLOBAL_MANAGER.set(config)


def reset_request_config() -> RequestConfig:
    """重置全局请求配置。"""

    return _GLOBAL_MANAGER.reset()


__all__ = [
    "DEFAULT_LEVEL_ALIASES",
    "DEFAULT_LEVEL_NAMES",
    "DEFAULT_USER_AGENT",
    "LogConfig",
    "MiddlewareConfig",
    "PoolConfig",
    "ProxyConfig",
    "RequestConfig",
    "RequestConfigManager",
    "RetryConfig",
    "TimeoutConfig",
    "get_request_config",
    "merge_request_config",
    "reset_request_config",
    "set_request_config",
    "update_request_config",
]
