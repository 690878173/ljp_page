from __future__ import annotations

import base64
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..browser.options import ChromiumOptions

from ..browser.chromium.edge import Edge as _Edge

from ..browser.tab import Tab as _Tab
import asyncio

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.options import Options

class EdgeConfig:
    def __init__(self,headless: bool = False):
        profile_dir = (Path.cwd() / "edge_profile").resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)

        options = ChromiumOptions()
        options.headless = headless
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-restore-session-state")
        options.add_argument("--disable-session-crashed-bubble")  # 禁止崩溃恢复
        options.add_argument("--hide-crash-restore-bubble")  # 隐藏崩溃提示
        self.options = options
from ljp_page._module.request.brower.pydoll import Request

def tab_lock(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # 自动获取当前 tab 的锁
        async with self.tab_lock:
            await self.bring_to_front()
            return await func(self, *args, **kwargs)
    return wrapper

class Tab:
    def __init__(self,tab,edge):
        self.tab:_Tab = tab
        self.edge:Edge = edge
        self.tab_lock = self.edge.tab_lock
        self._request = None

    @property
    def request(self):
        if self._request is None:
            self._request = Request(self.tab)
        return self._request

    @property
    async def title(self) -> str:
        return await self.tab.title

    @property
    async def cookies(self) -> dict:
        cook = await self.tab.get_cookies()
        cookie = {
            item.get('name'): item.get('value')
            for item in cook
            if item.get('name') and item.get('value') is not None
        }
        return cookie

    async def delete_all_cookies(self):
        await self.tab.delete_all_cookies()
    @property
    async def current_url(self) -> str:
        return await self.tab.current_url

    @tab_lock
    async def cf(self, time_to_wait_captcha: float = 10,max_time_to_wait_captcha=100) -> None:
        wait_title = ['Just a moment...','请稍候…']
        cur_title = await self.tab.title
        re_num = 3
        while cur_title in wait_title and re_num > 0:
            re_num -= 1
            print(f'执行cf验证:{re_num}')
            await self.tab.cf(time_to_wait_captcha=time_to_wait_captcha)
            cur_title = await self.tab.title

    async def go_to(self,url):
        await self.tab.go_to(url)

    async def get(self,url):
        await self.go_to(url)

    async def text(self):
        return await self.tab.page_source

    async def refresh(self,ignore_cache: bool = True,script_to_evaluate_on_load: Optional[str] = None,):
        await self.tab.refresh(ignore_cache,script_to_evaluate_on_load,)

    async def bring_to_front(self):
        return await self.tab.bring_to_front()

    @tab_lock
    async def get_image_bytes(self, img_url: str) -> bytes:
        """
        仅使用 PyDoll 的 execute_script
        从浏览器内部获取图片二进制
        完全不走 requests，自带 cookie/验证
        """
        # 切换到当前 tab
        await asyncio.sleep(1)

        # 🔥 核心：只用 execute_script 执行 JS 获取图片 base64
        js = f"""
            async function() {{
                try {{
                    let response = await fetch("{img_url}", {{
                        method: "GET",
                        credentials: "include",
                        mode: "cors"
                    }});
                    let blob = await response.blob();
                    return new Promise((resolve) => {{
                        let reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    }});
                }} catch (e) {{
                    return "error:" + e.message;
                }}
            }}
        """

        # 执行
        base64_str = await self.tab.execute_script(js)

        # 检查失败
        if base64_str.startswith("error:"):
            raise Exception(f"获取图片失败: {base64_str}")

        # 解码 base64 → 二进制
        base64_data = base64_str.split(",")[1]
        img_bytes = base64.b64decode(base64_data)

        return img_bytes

    async def close(self):
        await self.tab.close()


class Edge:

    def __init__(
        self,
        options: Optional[Options] = EdgeConfig().options,
        connection_port: Optional[int] = None,
    ):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0'
        }
        self.edge = _Edge(options=options, connection_port=connection_port)
        self.tab_lock = asyncio.Lock()

        self.tab_queue:asyncio.Queue|None = None

    async def start(self):
        tab = await self.edge.start()
        version = await self.edge.get_version()
        self.headers = {'User-Agent':version['userAgent']}
        return Tab(tab,self)


    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None):
        async with self.tab_lock:
            tab = await self.edge.new_tab(url, browser_context_id)
            return Tab(tab,self)

    @property
    def hd(self) -> dict:
        return self.headers


    async def create_tab_pool(self,num):
        self.tab_queue = asyncio.Queue()
        for i in range(num):
            tab = await self.new_tab()
            self.tab_queue.put_nowait(tab)

    async def get_tab_one(self) -> Tab:
        tab = await self.tab_queue.get()
        await self.tab_queue.put(tab)
        return tab



    async def __aenter__(self) -> 'Browser':
        """异步上下文管理器条目。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出并进行清理。"""
        await self.edge.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        await self.__aexit__(None, None, None)


__all__ = [
    'Tab',
    'Edge',
    'EdgeConfig',
    'ChromiumOptions'
]