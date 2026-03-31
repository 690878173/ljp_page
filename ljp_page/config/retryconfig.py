from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetryConfig:
    """重试策略配置。"""

    total: int = 2
    backoff_factor: float = 0.5
    max_backoff: float = 8.0

    retry_on_exceptions: list[str] = field(
        default_factory=lambda: ["timeout", "network", "proxy", "ssl"]
    )
    ignore_exceptions: list[str] = field(default_factory=lambda: [])

    extra: dict[str, Any] = field(default_factory=dict)