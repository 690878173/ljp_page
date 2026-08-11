"""浏览器上下文管理 —— 从 browser.py 中提取，去掉与 CF 验证的耦合。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ljp_page._core.base import Ljp_BaseClass_Logger

from .script import Script

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page as PlPage
    from .browser import Playwright
    from .page import Ljp_Page


class Ljp_Context(Ljp_BaseClass_Logger):  # noqa: N801
    """Playwright 浏览器上下文封装。"""

    def __init__(self, context: "BrowserContext", browser: "Playwright") -> None:
        super().__init__()
        self.own_context: "BrowserContext" = context
        self.browser: "Playwright" = browser
        self._started = False

    # ── 生命周期 ──

    async def _init(self) -> None:
        config = self.browser.config
        if config and config.init_script:
            await self.own_context.add_init_script(config.init_script)
        if config and config.use_stealth_script:
            await self.own_context.add_init_script(Script.FULL)
        self._started = True

    async def _ensure_started(self) -> None:
        if not self._started:
            await self._init()

    # ── 页面创建 ──

    async def new_page(self, **kwargs: Any) -> "Ljp_Page":
        from .page import Ljp_Page

        await self._ensure_started()
        page: "PlPage" = await self.own_context.new_page()
        return Ljp_Page(page, self)

    # ── CDP ──

    async def new_cdp_session(self, page: "Ljp_Page") -> Any:
        return await self.own_context.new_cdp_session(page.own_page)

    # ── 关闭 ──

    async def close(self) -> None:
        if self.own_context:
            for page in self.own_context.pages:
                await page.close()
            await self.own_context.close()


__all__ = ["Ljp_Context"]
