# 03-31-21-24-00
"""请求模块全局配置管理（仅保留 LjpConfig 新用法）。"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import is_dataclass
from threading import RLock
from typing import Any, Mapping

from ..Ljp_config import LjpConfig
from ..log_config import LogConfig
from ..middlewareconfig import MiddlewareConfig
from ..poolconfig import PoolConfig
from ..proxyconfig import ProxyConfig
from ..requestconfig import DEFAULT_USER_AGENT
from ..retryconfig import RetryConfig
from ..timeoutconfig import TimeoutConfig

DEFAULT_LEVEL_NAMES: dict[int, str] = {
    1: "debug",
    2: "trace",
    3: "verbose",
    4: "notice",
    5: "info",
    6: "step",
    7: "event",
    8: "check",
    9: "risk",
    10: "warning",
    11: "warn_plus",
    12: "alert",
    13: "issue",
    14: "error_minor",
    15: "error",
    16: "fatal",
    17: "panic",
    18: "security",
    19: "critical",
    20: "off",
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
    "warning": 10,
    "warn": 10,
    "warrior": 10,
    "alert": 12,
    "issue": 13,
    "error": 15,
    "fatal": 16,
    "panic": 17,
    "security": 18,
    "critical": 19,
    "off": 20,
}

_COMPONENT_FIELDS = {
    "request",
    "timeout",
    "retry",
    "pool",
    "proxy",
    "log",
    "middleware",
}


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
    "DEFAULT_LEVEL_ALIASES",
    "DEFAULT_LEVEL_NAMES",
    "DEFAULT_USER_AGENT",
    "LjpConfig",
    "LogConfig",
    "MiddlewareConfig",
    "PoolConfig",
    "ProxyConfig",
    "RequestConfigManager",
    "RetryConfig",
    "TimeoutConfig",
    "get_request_config",
    "merge_request_config",
    "reset_request_config",
    "set_request_config",
    "update_request_config",
]
