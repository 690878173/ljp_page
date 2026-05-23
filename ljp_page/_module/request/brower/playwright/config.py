from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

_DEFAULT_BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",  # 关闭 webdriver 自动化特征
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-position=0,0",
    "--ignore-certificate-errors",
    "--ignore-ssl-errors",
]

_CONTEXT_KEYS = {
    "viewport",
    "no_viewport",
    "user_agent",
    "locale",
    "timezone_id",
    "ignore_https_errors",
    "java_script_enabled",
    "color_scheme",
    "device_scale_factor",
    "is_mobile",
    "has_touch",
}

_CUSTOM_KEYS = {
    "user_data_dir",
    "init_script",
    "use_stealth_script",
}


@dataclass
class BrowserLaunchConfig:
    """Playwright 浏览器启动配置。

    user_data_dir 不为空时会使用持久化上下文，这对 Cloudflare 这类依赖 cookie、
    profile 与环境评分的验证更接近真实浏览器。
    """

    executable_path: Path | str | None = None
    channel: str | None = "msedge"
    args: Sequence[str] | None = field(default_factory=lambda: list(_DEFAULT_BROWSER_ARGS))
    # 去掉 --enable-automation，避免浏览器顶部显示“正受到自动化测试软件控制”。
    ignore_default_args: bool | Sequence[str] | None = field(
        default_factory=lambda: ["--enable-automation"]
    )
    handle_sigint: bool | None = True
    handle_sigterm: bool | None = True
    handle_sighup: bool | None = True
    timeout: float | None = 30000
    env: dict[str, str | float | bool] | None = None
    headless: bool | None = False
    proxy: dict[str, Any] | None = None
    downloads_path: Path | str | None = None
    slow_mo: float | None = 0
    traces_dir: Path | str | None = None
    chromium_sandbox: bool | None = None
    firefox_user_prefs: dict[str, Any] | None = None

    # 持久化浏览器数据目录；设置后使用 launch_persistent_context。
    user_data_dir: Path | str | None = None

    # 浏览器上下文参数。
    viewport: dict[str, int] | None = None
    no_viewport: bool | None = True
    user_agent: str | None = None
    locale: str | None = "zh-CN"
    timezone_id: str | None = "Asia/Shanghai"
    ignore_https_errors: bool | None = True
    java_script_enabled: bool | None = True
    color_scheme: str | None = None
    device_scale_factor: float | None = None
    is_mobile: bool | None = None
    has_touch: bool | None = None

    # Cloudflare 场景默认不注入指纹脚本，避免过度伪装造成二次风控。
    init_script: str | None = None
    use_stealth_script: bool | None = False

    def to_dict(self) -> dict[str, Any]:
        """转换为 launch / launch_persistent_context 可接收的启动参数。"""
        skip_keys = _CONTEXT_KEYS | _CUSTOM_KEYS
        return {
            key: value
            for key, value in self.__dict__.items()
            if value is not None and key not in skip_keys
        }

    def to_context_dict(self) -> dict[str, Any]:
        """转换为 new_context / launch_persistent_context 可接收的上下文参数。"""
        return {
            key: value
            for key, value in self.__dict__.items()
            if value is not None and key in _CONTEXT_KEYS
        }


__all__ = ["BrowserLaunchConfig"]
