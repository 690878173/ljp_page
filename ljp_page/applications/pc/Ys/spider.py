# 03-29-00-23-00
"""影视爬虫基类。"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from ljp_page.applications.pc.base.base_pc import BasePc
from ljp_page.core.base.Ljp_base_class import Ljp_Decorator
from ljp_page.exceptions import MeetCheckError
from ljp_page.logger import Logger

from .manager import BaseVideoManager, VideoManager
from .models import PageParseResult, VideoInfo, YsConfig


class VideoSpiderBase(BasePc, ABC):
    """影视爬虫抽象基类。"""

    Config = YsConfig
    VideoInfo = VideoInfo
    PageParseResult = PageParseResult

    def __init__(
        self,
        config: Config,
        log: Logger = None,
        MainWindows_ui: Any = None,
        stop_flag: bool = False,
        pause_flag: bool = False,
    ) -> None:
        super().__init__(
            config=config,
            log=log,
            MainWindows_ui=MainWindows_ui,
            stop_flag=stop_flag,
            pause_flag=pause_flag,
        )
        manager_cls = self.get_manager()
        self.video_manager = manager_cls(self, self.config, self.log)

    @Ljp_Decorator.handle_exceptions(MeetCheckError, BasePc.meet_fanpa)
    async def get(self, session: Any, url: str, *args: Any, **kwargs: Any) -> Any:
        self.debug(f"request url: {url}", self.get.__name__)
        return await self.req.async_get(session=session, url=url, *args, **kwargs)

    async def _fetch_video_info(self, video_id: Any) -> Optional[VideoInfo]:
        info_url = self.config.info_url.format(video_id)
        html_str = await self.get(self.session, info_url)
        if not html_str:
            return None
        parsed = await self.parse_html(self.parse_video_info, html_str, video_id, info_url)
        if not isinstance(parsed, self.VideoInfo):
            raise TypeError("parse_video_info must return VideoInfo")
        return parsed

    async def _process_page(self, page_id: Any) -> List[Any]:
        if not self.config.page_url:
            raise ValueError("ys mode2 requires page_url")
        page_url = self.config.page_url.format(page_id)
        html_str = await self.get(self.session, page_url)
        if not html_str:
            return []

        parsed = await self.parse_html(self.parse_page_videos, html_str, page_url)
        if isinstance(parsed, self.PageParseResult):
            return parsed.items
        if isinstance(parsed, list):
            return parsed
        raise TypeError("parse_page_videos must return PageParseResult or list")

    async def work(self, work_id: Any) -> None:
        video_info = await self._fetch_video_info(work_id)
        if video_info is None:
            self.warning(f"video info empty: {work_id}")
            return

        if self.ui and hasattr(self.ui, "add_movie"):
            result = self.ui.add_movie(video_info)
            if inspect.isawaitable(result):
                await result
            return

        await self.video_manager.download_video(self.session, video_info)

    def get_manager(self) -> type[BaseVideoManager]:
        return VideoManager

    @staticmethod
    @abstractmethod
    def parse_video_info(html_str: str, video_id: Any, url: str) -> VideoInfo:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def parse_page_videos(html_str: str, page_url: str) -> PageParseResult | list[Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_real_m3u8_url(self, episode_page_url: str) -> Optional[str]:
        raise NotImplementedError


class Ys(VideoSpiderBase):
    """影视爬虫默认实现（保留给业务站点继承）。"""

    pass


__all__ = ["VideoSpiderBase", "Ys"]
