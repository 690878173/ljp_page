from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any, Literal, Optional
from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._module.request.verification import AsyncVerification
from ..fp.fp_cf import CF_Find, CF_str

from .config import BrowserLaunchConfig
from .script import Script
from ..request import Request_need,Request

from playwright.async_api import BrowserContext, Error, Page, TimeoutError, async_playwright




class Playwright(Ljp_BaseClass_Logger):

    def __init__(self, config = None, *, playwright=None):
        super().__init__()
        self.own_playwright = playwright
        self.config: BrowserLaunchConfig = config
        self.browser = None
        self.context:Ljp_Context = None

        self._ua = None  # 新增缓存

    async def start(self):
        if not self.own_playwright:
            self.own_playwright = await async_playwright().start()
        if not self.config:
            self.config = BrowserLaunchConfig()

        context_options = self.config.to_context_dict()
        if self.config.user_data_dir:
            user_data_dir = Path(self.config.user_data_dir).resolve()
            user_data_dir.mkdir(parents=True, exist_ok=True)
            context = await self.own_playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                **self.config.to_dict(),
                **context_options,
            )
            self.browser = context.browser
        else:
            self.browser = await self.own_playwright.chromium.launch(**self.config.to_dict())
            context = await self.browser.new_context(**context_options)
        self.context = Ljp_Context(context, self)

        if self.config.user_agent:
            # 如果配置里显式指定了 UA，直接使用
            self._ua = self.config.user_agent
        else:
            # 否则通过临时页面获取真实 UA
            temp_page = await self.context.own_context.new_page()
            try:
                self._ua = await temp_page.evaluate("navigator.userAgent")
            finally:
                await temp_page.close()

    @property
    async def ua(self) -> str:
        """获取当前浏览器的真实 User-Agent（从缓存读取）"""
        if not self._ua:
            raise RuntimeError("请先启动浏览器 start()，或 UA 尚未初始化")
        return self._ua

    async def new_browser(self,config=None,playwright=None):
        return Playwright(config=config, playwright=playwright or self.own_playwright)

    async def new_page(self, **kwargs) -> Ljp_Page:
        return await self.context.new_page(**kwargs)

    async def new_pages(self,num,**kwargs)->list[Ljp_Page]:
        page_ls = []
        for _ in range(num):
            page_ls.append(await self.new_page())
        return page_ls

    async def new_context(self, **kwargs):
        context = await self.browser.new_context(**kwargs)
        return Ljp_Context(context, self)

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser and not self.config.user_data_dir:
                await self.browser.close()
            if self.own_playwright:
                await self.own_playwright.stop()
        except Exception as e:
            self.error(f"关闭playwright失败: {e}")
        finally:
            self.browser = None
            self.context = None
            self.own_playwright = None


class Ljp_Context(Ljp_BaseClass_Logger):  # noqa: N801
    def __init__(self, context: BrowserContext, browser: Playwright):
        super().__init__()
        self.own_context = context
        self.browser = browser
        self.start = False
        self.cdp_verification_gate = AsyncVerification(
            self._check_cdp_response_meet_cf,
            self._handle_cdp_response_cf,
        )
        self.init_()

    async def init_(self):
        config = self.browser.config
        if config and config.init_script:
            await self.own_context.add_init_script(config.init_script)
        if config and config.use_stealth_script:
            await self.own_context.add_init_script(Script.FULL)
        self.start = True

    async def new_page(self, **kwargs):
        if not self.start:
            await self.init_()
        page = await self.own_context.new_page()
        return Ljp_Page(page, self)

    async def new_cdp_session(self, page: "Ljp_Page"):
        return await self.own_context.new_cdp_session(page.own_page)

    @staticmethod
    def _response_text(response: dict) -> str:
        """提取 CDP/fetch 响应文本，用于识别 Cloudflare 验证页。"""

        if not isinstance(response, dict):
            return ""

        text = response.get("text")
        text_parts = [text] if isinstance(text, str) else []

        content = response.get("content")
        if isinstance(content, list):
            content = bytes(content)
        if isinstance(content, bytes):
            text_parts.append(content.decode("utf-8", errors="replace"))
            text_parts.append(content.decode("gbk", errors="replace"))
        return "\n".join(dict.fromkeys(text_parts))

    @staticmethod
    def _response_headers(response: Any) -> dict[str, str]:
        if not isinstance(response, dict):
            return {}
        headers = response.get("headers") or {}
        return {str(key).lower(): str(value) for key, value in headers.items()}

    async def _check_cdp_response_meet_cf(self, response: Any) -> bool:
        """判断 CDP/fetch 响应是否是 Cloudflare 验证页。"""

        text = self._response_text(response)
        text_lower = text.lower()
        if any(keyword.lower() in text_lower for keyword in CF_str.INVALID_TITLE_KEYWORDS):
            return True
        if "cf-chl" in text_lower or "challenges.cloudflare.com" in text_lower:
            return True

        status = int(response.get("status") or 0) if isinstance(response, dict) else 0
        headers = self._response_headers(response)
        server = headers.get("server", "").lower()
        return status in {403, 503} and "cloudflare" in server

    async def _handle_cdp_response_cf(self, verify_context) -> None:
        """CDP 请求命中 Cloudflare 后，刷新页面并执行页面验证。"""

        page: Ljp_Page = verify_context.own_page
        final_url = verify_context.get("final_url", "")
        page.warning(f"CDP 请求遇到 Cloudflare 验证，暂停同上下文请求: {final_url}")

        if verify_context.get("cf_refresh", True):
            try:
                await page.refresh(wait_until="domcontentloaded", timeout=10000)
            except Exception as exc:
                page.warning(f"刷新页面准备验证失败，继续尝试直接验证: {exc}")

        verified = await page.cf(
            time_to_wait_captcha=verify_context.get("cf_time_to_wait_captcha", 5),
            max_retries=verify_context.get("cf_max_retries", 3),
            wait_after_click=verify_context.get("cf_wait_after_click", 30),
        )
        if not verified:
            page.warning("Cloudflare 验证未确认通过，当前请求将按验证重试次数继续处理")

    async def close(self):
        if self.own_context:
            for page in self.own_context.pages:
                await page.close()
            await self.own_context.close()

class Ljp_Page(Ljp_BaseClass_Logger, CF_Find,Request_need):  # noqa: N801

    def __init__(self, page: Page, context: Ljp_Context):
        super().__init__()
        self.own_page = page
        self.context = context

        self._cdp_session = None
        self.cdp_verification_gate = context.cdp_verification_gate
        self.cdp_request = Request(self)

    @property
    def request(self):
        return self.own_page.request

    async def execute_command(self, expression, **kwargs):
        return await self.own_page.evaluate(expression, **kwargs)


    async def goto(self,url: str,wait_until: Optional[Literal["commit", "domcontentloaded", "load", "networkidle"]] = 'domcontentloaded',timeout: float | None = 10000,referer=None,):
        """通用跳转方法，带重试和错误处理"""
        try:
            await self.own_page.goto(url, wait_until=wait_until, timeout=timeout, referer=referer)
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
    @property
    async def cookie(self):
        cookies = await self.context.own_context.cookies()
        return cookies

    @property
    def url(self):
        return self.own_page.url

    async def _title(self) -> str:
        return await self.own_page.title()

    @property
    async def title(self):
        return await self._title()

    @property
    async def frames(self):
        return self.own_page.frames

    @property
    async def content(self):
        return await self._content()

    async def _content(self):
        return await self.own_page.content()

    async def locator(self,selector):

        return self.own_page.locator(selector)

    async def get_by_text(self,text):
        return self.own_page.get_by_text(text)

    async def click(self, selector: str, timeout: int = 30000):
        """点击元素"""
        try:
            await self.own_page.click(selector, timeout=timeout)
        except Exception as e:
            self.error(f"Click selector '{selector}' failed: {e}")
            raise

    async def get_cdp_session(self,owm=None):
        if owm:
            cdp_session = await self.own_page.context.new_cdp_session(owm)
            return cdp_session

        if not self._cdp_session:
            self._cdp_session = await self.own_page.context.new_cdp_session(self.own_page)
        else:
            try:
                await self._cdp_session.send("Runtime.evaluate", {"expression": "1"})
            except Exception:
                self._cdp_session = await self.own_page.context.new_cdp_session(self.own_page)

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
        if self.own_page:
            await self.own_page.close()


if __name__ == '__main__':
    async def test():
        edge = Playwright(config=None)
        await edge.start()
        await edge.close()


    asyncio.run(test())
