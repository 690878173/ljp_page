# 04-01-21-10-00
"""请求模块配置管理器与合并逻辑。"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import is_dataclass, dataclass, field
from threading import RLock
from typing import Any, Mapping

from ljp_page._core.config import TimeoutConfig, RetryConfig, PoolConfig, ProxyConfig
from ljp_page._core.logger import LogConfig

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
)

_COMPONENT_FIELDS = {
    "request",
    "timeout",
    "retry",
    "pool",
    "proxy",
    "log",
    "middleware",
}

@dataclass
class MiddlewareConfig:
    """中间件开关配置。"""

    enable_request_middleware: bool = True
    enable_response_middleware: bool = True
    enable_retry_middleware: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestConfig:
    """请求行为配置。"""

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
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LjpConfig:
    """请求模块主配置。"""

    request: RequestConfig = field(default_factory=RequestConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    pool: PoolConfig = field(default_factory=PoolConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    log: LogConfig = field(default_factory=LogConfig)
    extra: dict[str, Any] = field(default_factory=dict)

def _ensure_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be Mapping, got {type(value).__name__}")
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
            raise KeyError(f"unsupported config field: {type(component).__name__}.{key}")
        setattr(merged, key, value)
    return merged

def merge_request_config(base: LjpConfig, **overrides: Any) -> LjpConfig:
    """基于 LjpConfig 合并覆盖项，返回新配置。"""

    merged = deepcopy(base)
    for key, value in overrides.items():
        if value is None:
            continue

        if key in _COMPONENT_FIELDS:
            setattr(merged, key, _merge_component(getattr(merged, key), value))
            continue

        if key == "extra":
            merged.extra.update(dict(_ensure_mapping("extra", value)))
            continue

        raise KeyError(
            "unsupported config field: "
            f"{key}, use one of {_COMPONENT_FIELDS | {'extra'}}"
        )

    return merged

class RequestConfigManager:
    """线程安全的请求全局配置管理器。"""

    def __init__(self) -> None:
        self._lock = RLock()
        self._config = LjpConfig()

    def get(self, **overrides: Any) -> LjpConfig:
        with self._lock:
            snapshot = deepcopy(self._config)
        if not overrides:
            return snapshot
        return merge_request_config(snapshot, **overrides)

    def set(self, config: LjpConfig) -> LjpConfig:
        with self._lock:
            self._config = deepcopy(config)
            return deepcopy(self._config)

    def update(self, **updates: Any) -> LjpConfig:
        with self._lock:
            self._config = merge_request_config(self._config, **updates)
            return deepcopy(self._config)

    def reset(self) -> LjpConfig:
        return self.set(LjpConfig())


_GLOBAL_MANAGER = RequestConfigManager()


def get_request_config(**overrides: Any) -> LjpConfig:
    return _GLOBAL_MANAGER.get(**overrides)


def update_request_config(**updates: Any) -> LjpConfig:
    return _GLOBAL_MANAGER.update(**updates)


def set_request_config(config: LjpConfig) -> LjpConfig:
    return _GLOBAL_MANAGER.set(config)


def reset_request_config() -> LjpConfig:
    return _GLOBAL_MANAGER.reset()


__all__ = [
    "DEFAULT_USER_AGENT",
    "RequestConfigManager",
    "get_request_config",
    "merge_request_config",
    "reset_request_config",
    "set_request_config",
    "update_request_config",
    'RequestConfig',
    "MiddlewareConfig",
    'LjpConfig'
]
