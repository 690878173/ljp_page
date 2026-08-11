"""会话配置——扁平化设计。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ljp_page._core.utils.config import ProxyConfig, SessionPoolConfig, TimeoutConfig
from ljp_page._core.utils.retry import RetryConfig

from ..config import USER_AGENTS


@dataclass
class LjpConfig:
    """请求会话统一配置。"""

    # ── 请求默认值 ──
    headers: dict[str, str] = field(
        default_factory=lambda: {"User-Agent": USER_AGENTS[-1]},
    )
    cookies: dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    allow_redirects: bool = True
    stream: bool = False
    delay: float = 0.0
    trust_env: bool = True
    base_url: str = ""

    # ── 子配置 ──
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    sessionpool: SessionPoolConfig = field(default_factory=SessionPoolConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)

    # ── 扩展 ──
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.delay = max(0.0, self.delay)


__all__ = ["LjpConfig"]
