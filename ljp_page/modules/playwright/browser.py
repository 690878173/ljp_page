import asyncio
import random
from typing import Optional, Dict, Any, List, Union
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error, Frame
from .base import PlaywrightModuleBase

async def draw_click_marker(page, x, y):
    """
    在页面(x,y)位置绘制红色圆点标记（调试用）
    :param page: Playwright Page 实例
    :param x: 点击x坐标
    :param y: 点击y坐标
    """
    # 注入JS，创建一个红色半透明圆点
    await page.evaluate('''(x, y) => {
        // 创建标记元素
        const marker = document.createElement('div');
        marker.id = 'click-marker';
        // 样式：红色圆点，半透明，固定定位，层级最高
        marker.style.cssText = `
            position: fixed;
            left: ${x - 5}px;  // 圆点中心对齐点击坐标
            top: ${y - 5}px;
            width: 10px;
            height: 10px;
            background-color: red;
            border-radius: 50%;
            opacity: 0.8;
            z-index: 999999;  // 确保在最上层
            pointer-events: none;  // 不影响点击操作
        `;
        // 添加到页面
        document.body.appendChild(marker);
        // 5秒后自动移除标记
        setTimeout(() => {
            marker.remove();
        }, 5000);
    }''',  {"x": x, "y": y})
    print(f"🟥 已在坐标 ({x:.1f}, {y:.1f}) 绘制红色标记，5秒后自动消失")

class Playwright(PlaywrightModuleBase):
    """
    Playwright 异步封装，支持自动管理生命周期，集成常用功能和简单的反检测机制
    """
    def __init__(self, headless: bool = True, args: list = None, logger=None, 
                 user_agent: str = None, proxy: Dict = None, viewport: Dict = None):
        super().__init__(logger=logger)
        self.headless = headless
        # 默认启动参数，增强稳定性与反检测基础
        self.args = args or [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-position=0,0',
            '--ignore-certificate-errors',
            '--ignore-ssl-errors',
            '--disable-blink-features=AutomationControlled',  # 关键：禁用自动化控制特征
        ]
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.proxy = proxy
        self.viewport = viewport or {'width': 1920, 'height': 1080}
        
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
                launch_kwargs = {
                    'headless': self.headless,
                    'args': self.args,
                }
                if self.proxy:
                    launch_kwargs['proxy'] = self.proxy

                self.browser = await self.playwright.chromium.launch(**launch_kwargs)
                
                context_kwargs = {
                    'viewport': self.viewport,
                    'user_agent': self.user_agent,
                    'java_script_enabled': True,
                    'ignore_https_errors': True,
                }
                
                self.context = await self.browser.new_context(**context_kwargs)
                
                # 注入反检测脚本
                await self._inject_stealth_scripts(self.context)
                
                self.page = await self.context.new_page()
                self.info("Playwright started successfully.")
            except Exception as e:
                self.error(f"Failed to start Playwright: {e}")
                if self.playwright:
                    await self.playwright.stop()
                raise

    async def _inject_stealth_scripts(self, context: BrowserContext):
        """注入反检测脚本，隐藏webdriver特征"""
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        # 可以添加更多stealth脚本，如修改navigator.plugins, navigator.languages等

    async def _init_click(self,page):
        ss = '''
        // 全局监听鼠标按下事件（包括page.mouse.down()触发的）
        document.addEventListener('mousedown', function(e) {
            // 创建红色标记圆点
            const dot = document.createElement('div');
            dot.style.cssText = `
                position: fixed !important;
                left: ${e.clientX - 8}px !important;
                top: ${e.clientY - 8}px !important;
                width: 16px !important;
                height: 16px !important;
                background: red !important;
                border: 2px solid white !important;
                border-radius: 50% !important;
                opacity: 0.9 !important;
                z-index: 9999999 !important;  // 最高层级，覆盖所有元素
                pointer-events: none !important;  // 不影响后续操作
                box-shadow: 0 0 10px red !important;  // 加阴影，更显眼
                transition: opacity 2s !important;
            `;
            dot.id = 'click-dot-' + Date.now();
            document.body.appendChild(dot);
            // 3秒后淡出，5秒后移除
            setTimeout(() => dot.style.opacity = 0, 3000);
            setTimeout(() => dot.remove(), 5000);
        });

        // 额外监听click事件（兜底）
        document.addEventListener('click', function(e) {
            const cross = document.createElement('div');
            cross.style.cssText = `
                position: fixed !important;
                left: ${e.clientX}px !important;
                top: ${e.clientY}px !important;
                width: 20px !important;
                height: 20px !important;
                opacity: 0.8 !important;
                z-index: 9999999 !important;
                pointer-events: none !important;
            `;
            // 画十字线（更精准）
            cross.innerHTML = `
                <div style="position:absolute; top:10px; left:0; width:20px; height:2px; background:yellow;"></div>
                <div style="position:absolute; left:10px; top:0; width:2px; height:20px; background:yellow;"></div>
            `;
            cross.id = 'click-cross-' + Date.now();
            document.body.appendChild(cross);
            setTimeout(() => cross.remove(), 5000);
        });
    '''
        await page.add_init_script(ss)
        print("✅ 全局点击可视化已注入：任何点击都会显示红色圆点+黄色十字线！")

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
            self.warning(f"Error during Playwright stop: {e}")
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
            self.error(f"Navigate to {url} failed: {e}")
            raise

    async def get_cookies(self, as_dict: bool = False) -> Union[List[Dict], Dict[str, str]]:
        """获取当前上下文的所有Cookie"""
        if not self.context:
            return {} if as_dict else []
        cookies = await self.context.cookies()
        if as_dict:
            return {c['name']: c['value'] for c in cookies}
        return cookies

    async def wait_for_selector(self, selector: str, state: str = 'visible', timeout: int = 30000) -> Optional[Any]:
        """等待元素出现"""
        page = await self.get_page()
        try:
            return await page.wait_for_selector(selector, state=state, timeout=timeout)
        except Exception as e:
            self.warning(f"Wait for selector '{selector}' failed: {e}")
            return None

    async def click(self, selector: str, timeout: int = 30000):
        """点击元素"""
        page = await self.get_page()
        try:
            await page.click(selector, timeout=timeout)
        except Exception as e:
            self.error(f"Click selector '{selector}' failed: {e}")
            raise

    async def mouse_move_random(self):
        """模拟随机鼠标移动"""
        page = await self.get_page()
        width = self.viewport['width']
        height = self.viewport['height']
        x = random.randint(0, width)
        y = random.randint(0, height)
        await page.mouse.move(x, y, steps=10)

    # --- Cloudflare / 反爬虫对抗功能 ---

    async def is_valid_response(self, text: str = None) -> bool:
        """判断页面内容是否有效（非验证页面）"""
        if text is None:
            page = await self.get_page()
            text = await page.content()
            
        invalid_keywords = [
            "Just a moment", 
            "www.cloudflare.com", 
            "challenge-platform",
            "Verify you are human"
        ]
        return not any(keyword in text for keyword in invalid_keywords)

    async def handle_cf_challenge(self) -> bool:
        """处理 Cloudflare/Turnstile 验证"""
        page = await self.get_page()
        self.info("正在检测 Cloudflare 验证...")
        iframe_element = None
        cf_ls = ['div.ehurV4 > div > div','iframe[src*="challenges"]','iframe[title*="Cloudflare"]']

        try:
        #     # 1. 尝试寻找常见的 iframe (Turnstile)
        #     try:
        #         for selector in cf_ls:
        #             iframe_element = await self.wait_for_selector(selector,timeout=10000)
        #             if iframe_element:
        #                 break
        #     except:
        #         pass
        #
        #     if iframe_element:
        #         self.info("发现验证 iframe，尝试点击...")
        #         frame = await iframe_element.content_frame()
        #         if frame:
        #             checkbox_ls = ['input[type="checkbox"]','.ctp-checkbox-label']
        #             checkbox = None
        #             try:
        #                 for selector in checkbox_ls:
        #                     checkbox = await frame.wait_for_selector(selector, timeout=3000)
        #                     if checkbox:
        #                         break
        #             except:
        #                 pass
        #
        #             if checkbox:
        #                 await self._human_like_click(page, checkbox)
        #                 self.info("已点击验证框")
        #                 return True
        #     else:
        #         # 尝试直接寻找页面上的按钮
        #         self.info("未发现 iframe，尝试搜索页面主体...")
        #         verify_btn = await page.query_selector('#challenge-stage input[type="button"]')
        #         if verify_btn:
        #              await verify_btn.click()
        #              return True

            parent_selector = 'div#ehurV4 > div > div'
            await page.wait_for_selector(parent_selector,timeout=5000)
            print("目标父元素已加载")
            element = page.locator(parent_selector)
            bounding_box = await element.bounding_box()
            if not bounding_box:
                print("❌ 无法获取父容器坐标")
                return False

            # 父容器的基础信息
            parent_x = bounding_box['x']  # 父容器左上角x
            parent_y = bounding_box['y']  # 父容器左上角y
            parent_w = bounding_box['width']  # 父容器宽度
            parent_h = bounding_box['height']  # 父容器高度

            # 3. 手动校准验证按钮的相对位置（核心！需根据实际页面调整比例）
            # 👇 关键参数：按人工观察的按钮位置调整（示例值，你需要微调）
            # 比如：按钮在父容器的 10%宽度、20%高度 位置 → x_ratio=0.1, y_ratio=0.2
            # 比如：按钮在父容器的 左侧15px、顶部20px 位置 → x_offset=15, y_offset=20
            x_ratio = 0.15  # 按钮x坐标 = 父容器x + 父容器宽度 * 0.15
            y_ratio = 0.5  # 按钮y坐标 = 父容器y + 父容器高度 * 0.20
            x_offset = 5  # 额外x偏移（像素），微调位置
            y_offset = 8  # 额外y偏移（像素），微调位置
            for i in range(1,10):
                btn_x = parent_x + parent_w * x_ratio + random.uniform(-2, 2) + x_offset
                btn_y = parent_y + parent_h * y_ratio + random.uniform(-2, 2) + y_offset
                btn_x = btn_x * i
                btn_y = btn_y * i
                print(btn_x, btn_y)
                break
                # await draw_click_marker(page,btn_x,btn_y )
            await self._init_click(page)
            await page.mouse.move(
                btn_x, btn_y,
                steps=random.randint(15, 30)  # 步数越多，移动越慢（真人特征）
            )
            # 步骤2：停留随机时间（0.5-1秒，真人会犹豫）
            await asyncio.sleep(random.uniform(0.5, 1.0))
            # 步骤3：按下鼠标（模拟真人按下去的延迟）
            await page.mouse.down()
            # 步骤4：短暂停留后松开（模拟真人点击的按压感）
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.mouse.up()

            print(f"✅ 精准点击验证按钮（坐标：{btn_x:.1f}, {btn_y:.1f}）")


        except Exception as e:
            self.debug(f"验证检测过程中的异常（非致命）: {e}")
        
        return False

    async def _human_like_click(self, page, element):
        """模拟人类点击行为"""
        await asyncio.sleep(random.uniform(0.3, 0.7))
        box = await element.bounding_box()
        if box:
            # 移动到元素中心附近随机偏移
            x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
            y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.mouse.down()
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.mouse.up()

    async def bypass_cloudflare(self, url: str, max_retries: int = 3) -> bool:
        """
        尝试访问 URL 并绕过 Cloudflare 验证
        :return: 是否成功绕过并进入正常页面
        """
        # 强制开启有头模式，提高通过率
        original_headless = self.headless
        if self.headless:
            self.info("为了绕过验证，临时切换到有头模式...")
            # 注意：Playwright 不支持动态切换 headless，需要重启
            # 但这里我们假设实例已经在外部被正确配置，或者在此方法内重启
            # 简单起见，如果当前是 headless，我们建议用户在初始化时就设为 False
            # 或者在这里不做处理，仅提示。
            # 如果必须切换，需要调用 restart，但这会丢失上下文。
            # 策略：如果检测到 headless=True，发出警告。
            self.warning("当前为无头模式，Cloudflare 验证通过率可能较低。建议初始化时设置 headless=False。")

        try:
            await self.goto(url)
            page = await self.get_page()
            
            # 初步检查
            content = await page.content()
            if await self.is_valid_response(content):
                self.info("未遇到验证，直接访问成功")
                return True

            self.info("检测到 Cloudflare 盾，开始尝试绕过...")
            for i in range(max_retries):
                if await self.handle_cf_challenge():
                    self.info("已执行点击操作，等待跳转...")
                    await asyncio.sleep(random.uniform(3, 5))
                
                content = await page.content()
                if await self.is_valid_response(content):
                    self.info("验证通过！")
                    return True
                
                self.info(f"验证未通过或需再次验证，第 {i+1} 次重试...")
                await asyncio.sleep(2)
            
            self.error("无法绕过 Cloudflare 验证")
            return False

        except Exception as e:
            self.error(f"Bypass process failed: {e}")
            return False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

if __name__ == '__main__':
    async def test():
        # 使用上下文管理器
        url = 'https://www.bz11111.net/shuku/6-size-0-64.html'
        async with Playwright(headless=False) as pw:
            page = await pw.get_page()
            await page.goto(url)
            title = await page.title()
            print(f"Page Title: {title}")
            # yz = await page.wait_for_selector('#kw', timeout=10000)
            # print(yz)
            s = await pw.bypass_cloudflare(url)
            print(s)
            await asyncio.sleep(1000)


    asyncio.run(test())
