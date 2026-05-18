from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional


from ..browser.options import ChromiumOptions

from ..browser.chromium.edge import Edge as _Edge
from ..browser.tab import Tab as _Tab


if TYPE_CHECKING:
    from ljp_page._modules.pydoll.browser.options import Options

class EdgeConfig:
    def __init__(self,headless: bool = False):
        profile_dir = (Path.cwd() / "edge_profile").resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)

        options = ChromiumOptions()
        options.headless = headless
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")
        self.options = options

class Tab:
    def __init__(self,tab):
        self.tab:_Tab = tab

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

    @property
    async def current_url(self) -> str:
        return await self.tab.current_url

    async def cf(self, time_to_wait_captcha: float = 10,max_time_to_wait_captcha=100) -> None:
        wait_title = ['Just a moment...','请稍候…']
        cur_title = await self.tab.title
        while cur_title in wait_title:
            await self.tab.cf(time_to_wait_captcha=time_to_wait_captcha)
            cur_title = await self.tab.title
            print(cur_title)

    async def go_to(self,url):
        await self.tab.go_to(url)

    async def refresh(self,ignore_cache: bool = True,script_to_evaluate_on_load: Optional[str] = None,):
        await self.tab.refresh(ignore_cache,script_to_evaluate_on_load,)


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

    async def start(self):
        tab = await self.edge.start()
        version = await self.edge.get_version()
        self.headers = {'User-Agent':version['userAgent']}
        return Tab(tab)

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None):
        tab = await self.edge.new_tab(url, browser_context_id)
        return Tab(tab)

    @property
    def hd(self) -> dict:
        return self.headers



    async def __aenter__(self) -> 'Browser':
        """异步上下文管理器条目。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出并进行清理。"""
        await self.edge.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self):
        await self.__aexit__(None, None, None)


