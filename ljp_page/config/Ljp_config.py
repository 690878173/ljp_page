# 03-31-21-24-00
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .log_config import LogConfig
from .middlewareconfig import MiddlewareConfig
from .poolconfig import PoolConfig
from .proxyconfig import ProxyConfig
from .requestconfig import RequestConfig
from .retryconfig import RetryConfig
from .timeoutconfig import TimeoutConfig


@dataclass
class LjpConfig:
    """主配置：统一收拢请求链路的全部子配置。"""

    request: RequestConfig = field(default_factory=RequestConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    pool: PoolConfig = field(default_factory=PoolConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    log: LogConfig = field(default_factory=LogConfig)
    middleware: MiddlewareConfig = field(default_factory=MiddlewareConfig)
    extra: dict[str, Any] = field(default_factory=dict)
