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

@dataclass
class SessionMetrics:
    """单个会话实例上的聚合指标。"""

    request_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    total_elapsed: float = 0.0

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
