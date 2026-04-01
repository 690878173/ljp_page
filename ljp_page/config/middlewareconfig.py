# 03-31-20-21-05
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MiddlewareConfig:
    """请求中间件开关配置。"""

    enable_request_middleware: bool = True
    enable_response_middleware: bool = True
    enable_retry_middleware: bool = True
    extra: dict[str, Any] = field(default_factory=dict)
