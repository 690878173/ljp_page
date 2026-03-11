import asyncio
import time
import logging
from typing import Optional, Dict, List
import aiohttp
from aiohttp import ClientSession
from ljp_page._ljp_network.playwright.ljp_Playwright import Playwright

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
        self.user_agent: Optional[str] = None
        self.cookies: Dict[str, str] = {}
        self.cookie_expire_time: float = 0
        self.cookie_valid_hours = 6  # Cookie有效期（小时）

    async def _fetch_cf_clearance(self) -> bool:
        """使用封装的 Playwright 获取 cf_clearance"""
        try:
            # 使用 headless=False 以便通过验证，生产环境可视情况调整
            # 注意：很多 CF 验证在 headless 模式下很难通过
            async with Playwright(headless=False, logger=logger) as pw:
                # 尝试绕过 Cloudflare
                success = await pw.bypass_cloudflare(self.base_url)
                
                if not success:
                    logger.error("无法绕过 Cloudflare 验证")
                    return False

                # 提取 Cookie 和 User-Agent
                page = await pw.get_page()
                cookies = await pw.get_cookies(as_dict=True)
                self.cookies = cookies
                self.user_agent = await page.evaluate("navigator.userAgent")
                
                self.cookie_expire_time = time.time() + self.cookie_valid_hours * 3600
                logger.info(f"成功获取 Cookies ({len(cookies)} 个) 和 User-Agent")
                return True

        except Exception as e:
            logger.error(f"获取 Cookie 过程中发生错误: {e}", exc_info=True)
            return False

    async def fetch_with_retry(self, session: ClientSession, params: Dict) -> Optional[str]:
        # 检查 Cookie 有效性
        if not self.user_agent or time.time() > self.cookie_expire_time:
            logger.info("Cookie/UA 过期或未初始化，重新获取...")
            if not await self._fetch_cf_clearance():
                logger.error("获取 Cookie 失败，无法发起请求")
                return None

        # 构造请求头
        headers = {
            "User-Agent": self.user_agent,
            "Referer": self.base_url,
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        
        # 使用完整的 cookies
        cookies = self.cookies if self.cookies else {}

        # 带重试请求
        for retry in range(self.max_retries):
            try:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    cookies=cookies,
                    timeout=15
                ) as response:
                    text = await response.text()
                    
                    # 简单的有效性检查，更复杂的检查可以使用 Playwright 类中的静态方法或逻辑
                    # 这里为了保持 test.py 简洁，仅做基本判断
                    is_valid = "Just a moment" not in text and "cloudflare" not in text.lower()
                    
                    # 检查状态码和内容
                    if response.status in [200, 404] and is_valid:
                        logger.info(f"请求成功（参数：{params}，状态码：{response.status}）")
                        return text
                    elif response.status in [403, 503] or not is_valid:
                        logger.warning(f"请求被拦截（状态码 {response.status}，重试次数：{retry+1}），重新获取 Cookie...")
                        if not await self._fetch_cf_clearance():
                            continue
                    else:
                        logger.warning(f"请求状态异常（状态码 {response.status}）")
            except Exception as e:
                logger.error(f"请求异常（重试次数：{retry+1}）：{str(e)}")
                await asyncio.sleep(1)
        
        logger.error(f"超过最大重试次数（{self.max_retries}次），请求失败")
        return None

async def batch_fetch(bypasser: CloudflareBypasser, params_list: List[Dict]):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(5)  # 降低并发以避免触发更严格的风控

        async def bounded_fetch(params):
            async with semaphore:
                return await bypasser.fetch_with_retry(session, params)

        tasks = [bounded_fetch(params) for params in params_list]
        results = await asyncio.gather(*tasks)
        return results

if __name__ == "__main__":
    BASE_URL = "https://m.diyibanzhu.me/wap.php"
    # 批量请求参数（示例取第1页）
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
    
    # 运行测试
    start_time = time.time()
    try:
        results = asyncio.run(batch_fetch(bypasser, params_list))
        logger.info(f"所有请求完成，耗时：{time.time() - start_time:.2f}秒")

        # 处理结果
        for i, result in enumerate(results):
            if result:
                logger.info(f"第{i+1}页内容长度：{len(result)}字符")
            else:
                logger.warning(f"第{i+1}页请求失败")
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
