# 04-01-20-09-00
"""Playwright 模块配置。"""

from dataclasses import dataclass, field

_DEFAULT_BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-position=0,0",
    "--ignore-certificate-errors",
    "--ignore-ssl-errors",
    "--disable-blink-features=AutomationControlled",
]
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass(slots=True)
class PlaywrightConfig:
    """Playwright 运行时配置。"""

    headless: bool = True
    args: list[str] = field(default_factory=lambda: list(_DEFAULT_BROWSER_ARGS))
    user_agent: str = _DEFAULT_USER_AGENT
    proxy: dict[str, str] | None = None
    viewport: dict[str, int] = field(
        default_factory=lambda: {"width": 1920, "height": 1080}
    )


__all__ = ["PlaywrightConfig"]
