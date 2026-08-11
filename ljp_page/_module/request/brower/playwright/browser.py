"""Playwright 浏览器管理 —— 负责浏览器/上下文/页面的生命周期。

重构要点：
- 消除了对 ..verification 的反向依赖
- Ljp_Context / Ljp_Page 职责拆分到独立模块
- CF 验证通过 VerificationGate + CfResponseChecker 组合委托
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ljp_page._core.base import Ljp_BaseClass_Logger
from playwright.async_api import async_playwright

from .config import BrowserLaunchConfig
from .context import Ljp_Context
from .page import Ljp_Page

__all__ = ["Playwright", "Ljp_Context", "Ljp_Page"]


class Playwright(Ljp_BaseClass_Logger):
    """Playwright 浏览器管理器。

    管理浏览器启动、上下文创建和 UA 获取。
    Ljp_Context / Ljp_Page 拆分到独立模块。
    """

    def __init__(self, config: BrowserLaunchConfig | None = None,
                 *, playwright: Any = None) -> None:
        super().__init__()
        self.own = playwright
        self.config = config
        self.browser: Any = None
        self.context: Ljp_Context | None = None
        self._ua: str | None = None

    # ── 启动 ──

    async def start(self) -> None:
        if not self.own:
            self.own = await async_playwright().start()
        if not self.config:
            self.config = BrowserLaunchConfig()

        context_options = self.config.to_context_dict()
        if self.config.user_data_dir:
            user_data_dir = Path(self.config.user_data_dir).resolve()
            user_data_dir.mkdir(parents=True, exist_ok=True)
            ctx = await self.own.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                **self.config.to_dict(),
                **context_options,
            )
            self.browser = ctx.browser
        else:
            self.browser = await self.own.chromium.launch(**self.config.to_dict())
            ctx = await self.browser.new_context(**context_options)

        self.context = Ljp_Context(ctx, self)
        self._ua = await self._resolve_ua()

    async def _resolve_ua(self) -> str:
        if self.config and self.config.user_agent:
            return self.config.user_agent
        temp_page = await self.context.own_context.new_page()  # type: ignore[union-attr]
        try:
            return await temp_page.evaluate("navigator.userAgent")
        finally:
            await temp_page.close()

    # ── UA ──

    @property
    async def ua(self) -> str:
        if not self._ua:
            raise RuntimeError("请先启动浏览器 start()")
        return self._ua

    # ── 页面 / 上下文 ──

    async def new_page(self, **kwargs: Any) -> Ljp_Page:
        if self.context is None:
            raise RuntimeError("请先启动浏览器 start()")
        return await self.context.new_page(**kwargs)

    async def new_pages(self, num: int, **kwargs: Any) -> list[Ljp_Page]:
        return [await self.new_page(**kwargs) for _ in range(num)]

    async def new_context(self, **kwargs: Any) -> Ljp_Context:
        if self.browser is None:
            raise RuntimeError("请先启动浏览器 start()")
        ctx = await self.browser.new_context(**kwargs)
        return Ljp_Context(ctx, self)

    async def new_browser(self, config: BrowserLaunchConfig | None = None,
                          playwright: Any = None) -> "Playwright":
        return Playwright(config=config, playwright=playwright or self.own)

    # ── 关闭 ──

    async def close(self) -> None:
        try:
            if self.context:
                await self.context.close()
            if self.browser and self.config and not self.config.user_data_dir:
                await self.browser.close()
            if self.own:
                await self.own.stop()
        except Exception as e:
            self.error(f"关闭playwright失败: {e}")
        finally:
            self.browser = None
            self.context = None
            self.own = None
