# 05-19-19-56-59
"""pydoll_pc 请求客户端组件。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, AsyncIterator

from ljp_page._core._base_class import Ljp_BaseClass
from ljp_page._module.request.fp import FP
from ljp_page.pc.edge.pydoll import Edge, EdgeConfig

if TYPE_CHECKING:
    from ljp_page._apps.pydoll_pc.base.model import Config
    from ljp_page._apps.pydoll_pc.base.pc import BasePc


@dataclass
class PydollResponse:
    """把浏览器页面结果包装成框架通用响应对象。"""

    text: str
    url: str
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def content(self) -> bytes:
        return self.text.encode("utf-8")

    def __bool__(self) -> bool:
        return bool(self.text)


class PcRequest(Ljp_BaseClass):
    """使用 pydoll Edge 作为请求源，保留 new_pc 的请求接口形状。"""

    def __init__(self, owner: BasePc, config: Config, logger: Any = None) -> None:
        super().__init__()
        self.set_logger(logger)
        self.owner = owner
        self.config = config
        self.fp_guard = FP()
        self.browser: Edge | None = None
        self.session: Any = None
        self._session_lock = asyncio.Lock()
        self._tab_lock = asyncio.Lock()

    async def init_session(self) -> None:
        if self.session is not None:
            self.owner.session = self.session
            return

        async with self._session_lock:
            if self.session is not None:
                self.owner.session = self.session
                return

            self.browser = self._build_browser()
            self.session = await self.browser.start()
            await self.session.delete_all_cookies()
            await self.session.refresh()

            self.owner.session = self.session
            self.info("pydoll Edge 初始化完成")

    def _build_browser(self) -> Edge:
        """集中创建浏览器，业务侧可通过 config 动态挂载少量 pydoll 参数。"""

        options = getattr(self.config, "pydoll_options", None)
        if options is None:
            headless = bool(getattr(self.config, "pydoll_headless", False))
            options = EdgeConfig(headless=headless).options
            opts = options
            # opts.add_argument("--disable-fonts")
            # opts.add_argument("--disable-notifications")
            # opts.add_argument("--disable-popup-blocking")
            # opts.add_argument("--disable-extensions")
            # opts.add_argument("--disable-plugins")

        connection_port = getattr(self.config, "pydoll_connection_port", None)
        return Edge(options=options, connection_port=connection_port)

    async def do_get(self, session: Any, url: str, *args: Any, **kwargs: Any) -> PydollResponse:
        self.debug(f"pydoll get url:{url}")
        tab = session or self.session
        if tab is None:
            await self.init_session()
            tab = self.session

        # 单 Tab 同时只能承载一个页面，导航和读取源码必须保持原子性，避免并发串页。
        async with self._tab_lock:
            await tab.get(url)
            await tab.refresh()
            await tab.cf()
            html_text = await tab.text()
            self.cookies = await tab.cookies()
            current_url = await self._get_current_url(tab, url)
        return PydollResponse(
            text=html_text,
            url=current_url,
            headers=self.browser.hd if self.browser is not None else {},
        )

    @staticmethod
    async def _get_current_url(tab: Any, fallback: str) -> str:
        current_url = getattr(tab, "current_url", None)
        if current_url is None:
            return fallback
        if callable(current_url):
            current_url = current_url()
        if hasattr(current_url, "__await__"):
            current_url = await current_url
        return str(current_url or fallback)

    async def get(
        self,
        session: Any,
        url: str,
        *args: Any,
        check_fp: bool = True,
        **kwargs: Any,
    ) -> PydollResponse:
        seen_version = await self.fp_guard.before_request() if check_fp else None
        res = await self.do_get(session, url, *args, **kwargs)

        if not check_fp:
            return res

        if not await self.owner.Fp(res.text):
            return res

        await self.fp_guard.handle_blocked(
            seen_version,
            self.owner.fp_do,
            session,
            url,
            *args,
            **kwargs,
        )
        return res

    async def close(self) -> None:
        if self.browser is not None:
            await self.browser.close()
        self.browser = None
        self.session = None
        self.owner.session = None

class XsTabPool:
    """Xs 专用 Tab 池，用多个 Tab 保持浏览器请求并发且不串页。"""

    def __init__(self, pc: Any, size: int) -> None:
        self.pc = pc
        self.size = max(1, int(size))
        self._tabs: list[Any] = []
        self._queue: asyncio.Queue[Any] = asyncio.Queue()
        self._started = False
        self._start_lock = asyncio.Lock()

    async def start(self) -> None:
        if self._started:
            return

        async with self._start_lock:
            if self._started:
                return

            await self.pc.req.init_session()
            browser = self.pc.req.browser
            first_tab = self.pc.session
            if first_tab is None or browser is None:
                raise RuntimeError("pydoll Edge 未初始化，无法创建 Xs Tab 池")

            self._tabs.append(first_tab)
            await self._queue.put(first_tab)
            for _ in range(self.size - 1):
                tab = await browser.new_tab()
                await tab.refresh()
                self._tabs.append(tab)
                await self._queue.put(tab)

            self._started = True
            self.pc.info(f"Xs Tab 池初始化完成: {self.size} 个 Tab")

    @asynccontextmanager
    async def lease(self) -> AsyncIterator[Any]:
        await self.start()
        tab = await self._queue.get()
        try:
            yield tab
        finally:
            self._queue.put_nowait(tab)

Pc_Request = PcRequest

__all__ = ["PcRequest", "Pc_Request", "PydollResponse","XsTabPool"]
