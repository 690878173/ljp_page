import asyncio
import time
from typing import Optional, Dict, List
from playwright.async_api import async_playwright  # 改用异步API
import aiohttp
from aiohttp import ClientSession
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CloudflareBypasser:
    def __init__(self, base_url: str, max_retries: int = 3):
        self.base_url = base_url
        self.max_retries = max_retries
        self.cf_clearance: Optional[str] = None
        self.user_agent: Optional[str] = None
        self.cookie_expire_time: float = 0
        self.cookie_valid_hours = 6  # Cookie有效期（小时）

    async def _find_checkbox(self, page):
        find_element_js = """() => {
                                const hostElement = document.querySelector('#uMtSJ0 > div > div');
                                if (!hostElement) return null;
                                console.log(hostElement);
                                return hostElement;
                                // 2. 访问shadow root（即使closed，页面内JS仍可访问）
                                const shadowRoot = hostElement.shadowRoot;
                                if (!shadowRoot) return null;
                                console.log(shadowRoot);

                                // 3. 在shadow root内查找iframe
                                iframe = shadowRoot.querySelector('iframe[title="包含 Cloudflare 安全质询的小组件"]');
                                if (!iframe) return null;
                                console.log(iframe);
                                return iframe;
                            }"""
        iframe = await page.evaluate(find_element_js)
        iframe = await page.query_selector('#uMtSJ0 > div > div')
        if not iframe:
            logger.error("未找到iframe元素")
            return None
        return iframe
        iframe_document = await iframe.content_frame()
        target_element = await iframe_document.evaluate_handle("""() => {
            const host = document.querySelector('body');  // iframe的#document中的宿主元素
            return host.shadowRoot.querySelector('input[type="checkbox"]');  // 穿透内层shadow root
        }""")
        if target_element:
            return target_element
        else:
            logger.error("未找到复选框元素")


    async def _fetch_cf_clearance(self) -> bool:
        """【异步版本】用Playwright获取cf_clearance和User-Agent"""
        try:
            async with async_playwright() as p:  # 异步上下文管理器
                # 启动无头Chrome（异步方法）
                browser = await p.chromium.launch(
                    headless=False,  # 调试时改为False
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                    ]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                # 异步访问页面
                await page.goto(self.base_url, timeout=60000)

                # 等待验证完成（异步等待）
                try:
                    await asyncio.sleep(7)
                    # 点击复选框（异步操作）
                    # //*[@id="uMtSJ0"]/div/label/input
                    # //*[@id="uMtSJ0"]/div/div
                    checkbox = await self._find_checkbox(page)
                    print(checkbox)
                    if checkbox:
                        await asyncio.sleep(0.5)  # 停留0.5秒
                        await checkbox.click()
                        await checkbox.click()
                        await asyncio.sleep(2)  # 等待点击后验证完成
                        print('点击完成')
                    else:
                        logger.error("未找到复选框元素")
                except Exception as e:
                    logger.error(f"验证超时：{str(e)}")
                    await browser.close()
                    return False

                # 提取Cookie（异步方法）
                cookies = await context.cookies()
                for cookie in cookies:
                    if cookie["name"] == "cf_clearance":
                        self.cf_clearance = cookie["value"]
                        break
                if not self.cf_clearance:
                    logger.error("未获取到cf_clearance Cookie")
                    await browser.close()
                    return False

                # 提取User-Agent（异步执行JS）
                self.user_agent = await page.evaluate("navigator.userAgent")
                self.cookie_expire_time = time.time() + self.cookie_valid_hours * 3600
                logger.info("成功获取cf_clearance和User-Agent")

                await browser.close()
                return True
        except Exception as e:
            logger.error(f"获取Cookie失败：{str(e)}", exc_info=True)
            return False

    async def _is_valid_response(self, text: str) -> bool:
        return "Just a moment" not in text and "cloudflare" not in text.lower()

    async def fetch_with_retry(self, session: ClientSession, params: Dict) -> Optional[str]:
        # 检查Cookie有效性
        if not self.cf_clearance or time.time() > self.cookie_expire_time:
            logger.info("Cookie过期或未初始化，重新获取...")
            if not await self._fetch_cf_clearance():  # 异步调用，需加await
                logger.error("获取Cookie失败，无法发起请求")
                return None

        # 构造请求头
        headers = {
            "User-Agent": self.user_agent,
            "Referer": self.base_url,
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        cookies = {"cf_clearance": self.cf_clearance}

        # 带重试请求
        for retry in range(self.max_retries):
            try:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    cookies=cookies,
                    timeout=10
                ) as response:
                    text = await response.text()
                    if await self._is_valid_response(text):
                        logger.info(f"请求成功（参数：{params}，状态码：{response.status}）")
                        return text
                    else:
                        logger.warning(f"请求被拦截（重试次数：{retry+1}），重新获取Cookie...")
                        if not await self._fetch_cf_clearance():  # 异步调用
                            continue
            except Exception as e:
                logger.error(f"请求异常（重试次数：{retry+1}）：{str(e)}")
                await asyncio.sleep(1)
        logger.error(f"超过最大重试次数（{self.max_retries}次），请求失败")
        return None

async def batch_fetch(bypasser: CloudflareBypasser, params_list: List[Dict]):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(20)  # 并发限制

        async def bounded_fetch(params):
            async with semaphore:
                return await bypasser.fetch_with_retry(session, params)

        tasks = [bounded_fetch(params) for params in params_list]
        results = await asyncio.gather(*tasks)
        return results

if __name__ == "__main__":
    BASE_URL = "https://m.diyibanzhu.me/wap.php"
    # 批量请求参数（1-5页）
    params_list = [
        {
            'action': 'shuku',
            'tid': '',
            'over': '',
            'order': '4',
            'uid': '',
            'totalresult': '15695',
            'pageno': str(page)
        } for page in range(1, 2)
    ]

    bypasser = CloudflareBypasser(base_url=BASE_URL)
    start_time = time.time()
    results = asyncio.run(batch_fetch(bypasser, params_list))
    logger.info(f"所有请求完成，耗时：{time.time() - start_time:.2f}秒")

    # 处理结果
    for i, result in enumerate(results):
        if result:
            logger.info(f"第{i+1}页内容长度：{len(result)}字符")
        else:
            logger.warning(f"第{i+1}页请求失败")