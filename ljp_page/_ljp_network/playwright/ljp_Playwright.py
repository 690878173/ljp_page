import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error

class Playwright:
    """
    Playwright 异步封装，支持自动管理生命周期
    """
    def __init__(self, headless: bool = True, args: list = None, logger=None):
        self.logger = logger
        self.headless = headless
        self.args = args or [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-position=0,0',
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
        ]
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """启动浏览器"""
        if self.browser:
            return
            
        async with self._lock:
            if self.browser:
                return
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=self.args
                )
                self.context = await self.browser.new_context(
                     viewport={'width': 1920, 'height': 1080},
                     user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                self.page = await self.context.new_page()
                if self.logger:
                    self.logger.info("Playwright started successfully.")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to start Playwright: {e}")
                raise

    async def stop(self):
        """关闭资源"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error during Playwright stop: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    async def restart(self):
        """重启浏览器"""
        await self.stop()
        await self.start()

    async def get_page(self) -> Page:
        """获取页面对象，如果未启动则自动启动"""
        if not self.page:
            await self.start()
        return self.page
        
    async def goto(self, url: str, wait_until: str = 'domcontentloaded', timeout: int = 30000):
        """通用跳转方法，带重试和错误处理"""
        page = await self.get_page()
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
        except Error as e:
            if self.logger:
                self.logger.error(f"Navigate to {url} failed: {e}")
            raise

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

if __name__ == '__main__':
    async def test():
        # 使用上下文管理器
        async with Playwright(headless=True) as pw:
            page = await pw.get_page()
            await page.goto('https://www.baidu.com')
            title = await page.title()
            print(f"Page Title: {title}")

    asyncio.run(test())
