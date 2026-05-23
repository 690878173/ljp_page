from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Literal, Optional
from ljp_page._core.base import Ljp_BaseClass_Logger
from ..fp.fp_cf import CF_Find
from ..request import Request_need,Request

from .config import BrowserLaunchConfig
from .script import Script


from playwright.async_api import BrowserContext, Error, Page, TimeoutError, async_playwright


class Playwright(Ljp_BaseClass_Logger):

    def __init__(self, config = None, *, playwright=None):
        super().__init__()
        self.playwright = playwright
        self.config: BrowserLaunchConfig = config
        self.browser = None
        self.context = None

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.config:
            self.config = BrowserLaunchConfig()

        context_options = self.config.to_context_dict()
        if self.config.user_data_dir:
            user_data_dir = Path(self.config.user_data_dir).resolve()
            user_data_dir.mkdir(parents=True, exist_ok=True)
            context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                **self.config.to_dict(),
                **context_options,
            )
            self.browser = context.browser
        else:
            self.browser = await self.playwright.chromium.launch(**self.config.to_dict())
            context = await self.browser.new_context(**context_options)
        self.context = Ljp_Context(context, self)

    @property
    async def ua(self) -> str:
        """
        获取当前浏览器的真实 User-Agent
        自动创建临时页面获取，用完关闭
        """
        if not self.browser:
            raise RuntimeError("请先启动浏览器 start()")

        # 临时创建上下文 + 页面拿UA
        context = await self.browser.new_context()
        page = await context.new_page()

        # 获取UA
        ua = await page.evaluate("navigator.userAgent")

        # 清理临时资源
        await page.close()
        await context.close()

        return ua

    async def new_page(self, **kwargs) -> Ljp_Page:
        return await self.context.new_page(**kwargs)

    async def new_context(self, **kwargs):
        context = await self.browser.new_context(**kwargs)
        return Ljp_Context(context, self)

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser and not self.config.user_data_dir:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.error(f"关闭playwright失败: {e}")
        finally:
            self.browser = None
            self.context = None
            self.playwright = None

class Ljp_Context(Ljp_BaseClass_Logger):  # noqa: N801
    def __init__(self, context: BrowserContext, browser: Playwright):
        super().__init__()
        self.context = context
        self.browser = browser
        self.start = False

    async def init_(self):
        config = self.browser.config
        if config and config.init_script:
            await self.context.add_init_script(config.init_script)
        if config and config.use_stealth_script:
            await self.context.add_init_script(Script.FULL)
        self.start = True

    async def new_page(self, **kwargs):
        if not self.start:
            await self.init_()
        page = await self.context.new_page()
        return Ljp_Page(page, self)

    async def new_cdp_session(self, page: "Ljp_Page"):
        return await self.context.new_cdp_session(page.page)

    async def close(self):
        if self.context:
            await self.context.close()

class Ljp_Page(Ljp_BaseClass_Logger, CF_Find,Request_need):  # noqa: N801

    def __init__(self, page: Page, context: Ljp_Context):
        super().__init__()
        self.page = page
        self.context = context

        self._cdp_session = None

    @property
    def request(self):
        return self.page.request

    async def execute_command(self, expression, **kwargs):
        return await self.page.evaluate(expression,**kwargs)


    async def goto(
        self,
        url: str,
        wait_until: Optional[Literal["commit", "domcontentloaded", "load", "networkidle"]] = None,
        timeout: float | None = None,
        referer=None,
    ):
        """通用跳转方法，带重试和错误处理"""
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=timeout, referer=referer)
        except Error as e:
            self.error(f"Page to {url} 失败: {e}")
            raise

    @staticmethod
    def _is_reload_abort(error: Exception) -> bool:
        """判断刷新是否被页面自身跳转打断。"""
        message = str(error)
        return "net::ERR_ABORTED" in message or "frame was detached" in message

    async def refresh(
        self,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "load",
        timeout: float | None = None,
    ) -> bool:
        """刷新页面；站点跳转导致的 reload 中断不视为致命错误。"""
        self._cdp_session = None
        try:
            await self.page.reload(wait_until=wait_until, timeout=timeout)
            return True
        except Error as error:
            if not self._is_reload_abort(error):
                self.error(f"刷新页面失败: {error}")
                raise

            self.warning(f"刷新被页面跳转中断，继续等待当前页面稳定: {error}")
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=timeout or 10000)
            except (Error, TimeoutError):
                pass
            return False
    @property
    async def cookie(self):
        cookies = await self.context.context.cookies()
        return cookies

    @property
    def url(self):
        return self.page.url

    async def _title(self) -> str:
        return await self.page.title()

    @property
    async def title(self):
        return await self._title()

    @property
    async def frames(self):
        return self.page.frames

    async def content(self):
        return await self.page.content()

    async def click(self, selector: str, timeout: int = 30000):
        """点击元素"""
        try:
            await self.page.click(selector, timeout=timeout)
        except Exception as e:
            self.error(f"Click selector '{selector}' failed: {e}")
            raise

    async def get_cdp_session(self,owm=None):
        if owm:
            cdp_session = await self.page.context.new_cdp_session(owm)
            return cdp_session

        if not self._cdp_session:
            self._cdp_session = await self.page.context.new_cdp_session(self.page)
        else:
            try:
                await self._cdp_session.send("Runtime.evaluate", {"expression": "1"})
            except Exception:
                self._cdp_session = await self.page.context.new_cdp_session(self.page)

        return self._cdp_session

    async def cf(
        self,
        time_to_wait_captcha: float = 5,
        max_retries: int = 3,
        wait_after_click: float = 30,
    ) -> bool:
        """尝试通过 shadow root 遍历点击 Cloudflare Turnstile 复选框。"""
        if self.context.browser.config and self.context.browser.config.headless:
            self.warning("当前为无头模式，Cloudflare 验证通过率可能较低。建议设置 headless=False。")

        if not await self.check_fp():
            return True

        for retry_index in range(max_retries):
            print(f"执行cf验证:{max_retries - retry_index}")
            if await self._cf(timeout=time_to_wait_captcha):
                return True
        #     if await self.wait_cloudflare_result(timeout=wait_after_click):
        #         return True
        # return not await self.is_cloudflare_challenge_page()
        return False

    async def close(self):
        if self.page:
            await self.page.close()


if __name__ == '__main__':
    async def test():
        edge = Playwright(config=None)
        await edge.start()
        await edge.close()


    asyncio.run(test())
