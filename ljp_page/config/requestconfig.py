from dataclasses import dataclass, field
from typing import Any

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
)

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
    extra: dict[str, Any] = field(default_factory=dict)