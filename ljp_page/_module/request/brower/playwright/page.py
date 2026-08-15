"""页面操作 —— 去掉 CF_Find 继承，CF 验证委托给 CfGuard 组件。"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Literal, TYPE_CHECKING

from playwright.async_api import CDPSession

from ljp_page._core.base import Ljp_BaseClass_Logger
from playwright.async_api import Error, TimeoutError

from .verification import VerificationGate, CfResponseChecker

if TYPE_CHECKING:
    from playwright.async_api import Page as PlPage
    from .context import Ljp_Context


class Ljp_Page(Ljp_BaseClass_Logger):  # noqa: N801
    """Playwright 页面封装。

    CF 验证和 CDP 请求通过组合委托给独立组件，而非继承混入。
    """

    def __init__(self, page: "PlPage", context: "Ljp_Context") -> None:
        super().__init__()
        self.own_page: "PlPage" = page
        self.context: "Ljp_Context" = context

        self._cdp_session: Any = None

        # ── 组合：CF 验证 ──
        self._cf_checker = CfResponseChecker()
        self.verify_gate = VerificationGate()

        # ── 组合 fetch 请求 ──
        from .request import FetchRequest
        self.fetch = FetchRequest(self)

        self.fetch.set_verify_gate(self.verify_gate)

    # ── 属性代理 ──

    @property
    async def title(self) -> str:
        return await self.own_page.title()

    @property
    def frames(self) -> Any:
        return self.own_page.frames

    @property
    async def cookies(self) -> Any:
        return await self.context.own_context.cookies()

    @property
    async def content(self) -> str:
        return await self.own_page.content()

    @property
    def request(self) -> Any:
        return self.own_page.request

    @property
    def url(self) -> str:
        return self.own_page.url

    # ── 导航 ──

    async def goto(self, url: str, *,
                   wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "domcontentloaded",
                   timeout: float | None = 10000, referer: str | None = None) -> None:
        try:
            await self.own_page.goto(url, wait_until=wait_until, timeout=timeout, referer=referer)
        except Error as e:
            self.error(f"Page to {url} 失败: {e}")
            raise

    async def refresh(self, *,
                      wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "load",
                      timeout: float | None = None) -> bool:
        self._cdp_session = None
        try:
            await self.own_page.reload(wait_until=wait_until, timeout=timeout)
            return True
        except Error as error:
            if not self._is_reload_abort(error):
                self.error(f"刷新页面失败: {error}")
                raise
            self.warning(f"刷新被页面跳转中断，继续等待当前页面稳定: {error}")
            try:
                await self.own_page.wait_for_load_state("domcontentloaded", timeout=timeout or 10000)
            except (Error, TimeoutError):
                pass
            return False

    # ── 元素交互 ──

    # 浏览器执行js代码接口
    async def execute_command(self, expression: str, **kwargs: Any) -> Any:
        return await self.own_page.evaluate(expression, **kwargs)

    async def _execute_command(self, command: dict) -> Any:
        """
        发送 CDP 命令。
        参数 command 应为 {'method': str, 'params': dict} 格式，
        其中 method 和 params 中的枚举值会被自动转换为字符串。
        """
        cdp = await self.get_cdp_session()

        # 提取 method 和 params，并转换枚举为字符串
        method = command.get("method")
        params = command.get("params", {})

        # 如果 method 是枚举，取 .value
        if hasattr(method, "value"):
            method = method.value

        # 发送命令
        return await cdp.send(method, params)
    async def click(self, selector: str, timeout: int = 30000) -> None:
        try:
            await self.own_page.click(selector, timeout=timeout)
        except Exception as e:
            self.error(f"Click selector '{selector}' failed: {e}")
            raise

    async def locator(self, selector: str) -> Any:
        return self.own_page.locator(selector)

    async def get_by_text(self, text: str) -> Any:
        return self.own_page.get_by_text(text)

    async def get_by_role(self,role):
        return self.own_page.get_by_role(role)

    # ── CDP ──

    async def get_cdp_session(self, owm: Any = None) -> "CDPSession" :
        if owm:
            return await self.own_page.context.new_cdp_session(owm)
        if self._cdp_session:
            try:
                await self._cdp_session.send("Runtime.evaluate", {"expression": "1"})
                return self._cdp_session
            except Exception:
                pass
        self._cdp_session = await self.own_page.context.new_cdp_session(self.own_page)
        return self._cdp_session

    # ── CF 验证 (委托给 CfGuard) ──

    async def is_cf_challenge(self) -> bool:
        """检测当前页面是否是 CF 验证页（委托 CfResponseChecker）。"""
        from ..fp.fp_cf import CF_Find
        cf_find = CF_Find(host=self)
        return await cf_find.check_fp()

    async def cf(self, time_to_wait_captcha: float = 5, max_retries: int = 3,
                 wait_after_click: float = 30) -> bool:
        """通过 shadow root 遍历点击 Cloudflare Turnstile 复选框。"""
        from ..fp.fp_cf import CF_Find

        time_to_wait_captcha = float(time_to_wait_captcha)
        max_retries = int(max_retries)

        if self.context.browser.config and self.context.browser.config.headless:
            self.warning("当前为无头模式，Cloudflare 验证通过率可能较低。建议设置 headless=False。")

        cf_find = CF_Find(host=self)
        if not await cf_find.check_fp():
            return True

        for retry_index in range(max_retries):
            print(f"执行cf验证:{max_retries - retry_index}")
            if await cf_find._cf(timeout=time_to_wait_captcha):
                return True
        return False

    # ── 生命周期 ──

    async def close(self) -> None:
        if self.own_page:
            await self.own_page.close()

    # ── 静态 ──

    @staticmethod
    def _is_reload_abort(error: Exception) -> bool:
        message = str(error)
        return "net::ERR_ABORTED" in message or "frame was detached" in message


__all__ = ["Ljp_Page"]
