# 05-19-14-34-05
"""new_pc 影视爬虫基类。"""

from __future__ import annotations

import asyncio
import inspect
import re
from typing import Any

from ljp_page._core._exceptions import No, Notfound
from ljp_page._modules.request import LjpResponse

from ..base.model import P1Result, P2Item, P2Result, P3Item
from ..base.pc import BasePc
from .manager import BaseVideoManager, VideoManager
from .models import PageParseResult, VideoEpisode, VideoInfo, YsConfig


class Ys(BasePc):
    """影视爬虫默认实现，业务站点可继承后只补解析逻辑。"""

    Config = YsConfig
    VideoInfo = VideoInfo
    VideoEpisode = VideoEpisode
    PageParseResult = PageParseResult
    M3U8_RE = re.compile(r"""https?://[^"' <>\]]+?\.m3u8(?:\?[^"' <>\]]*)?""", re.I)

    def __init__(self, config: YsConfig, ui=None):
        super().__init__(config, ui)

    def build_other(self) -> None:
        super().build_other()
        self.video_manager = self.manager(self, self.config, self.logger)

    def get_manager(self) -> type[BaseVideoManager]:
        return VideoManager

    def parse_p1(self, response: LjpResponse, url: str) -> PageParseResult | P1Result | list[Any]:
        return self.parse_page_videos(response.text, url)

    def parse_p2(self, res_html: str, url: str, video_id: Any = None) -> VideoInfo | P2Result:
        return self.parse_video_info(res_html, video_id, url)

    def parse_p3(self, res_html: str, url: str) -> VideoEpisode | P3Item | str | dict[str, Any]:
        match = self.M3U8_RE.search(res_html or "")
        if not match:
            raise Notfound("未在播放页中解析到 m3u8", resource=url)
        return VideoEpisode(index=1, title="", page_url=url, m3u8_url=match.group(0))

    def parse_page_videos(self, html_str: str, page_url: str) -> PageParseResult | list[Any]:
        raise NotImplementedError("需要继承实现 parse_page_videos 或 parse_p1")

    def parse_video_info(self, html_str: str, video_id: Any, url: str) -> VideoInfo | P2Result:
        raise NotImplementedError("需要继承实现 parse_video_info 或 parse_p2")

    async def _p1_work(self, p1_id: Any) -> list[Any]:
        if not self.config.p1_url:
            return [p1_id]

        page_url = self.format_p1_url(p1_id)
        response = await self.get(self.session, page_url)
        if not response:
            return []

        parsed = await self.parse_html(self.parse_p1, response, page_url)
        return self._coerce_page_items(parsed)

    async def p2_work(self, p2_id: Any) -> None:
        try:
            video_info = await self._fetch_video_info(p2_id)
            if self.ui and hasattr(self.ui, "add_movie"):
                ui_result = self.ui.add_movie(video_info)
                if inspect.isawaitable(ui_result):
                    await ui_result
                return
            if self.ui and hasattr(self.ui, "add_p2"):
                ui_result = self.ui.add_p2(video_info)
                if inspect.isawaitable(ui_result):
                    await ui_result
                return
            await self.download(video_info)
        except Notfound as exc:
            self.warning(f"影视资源不存在: {p2_id}, {exc}")
        except Exception as exc:
            self.error(f"p2 任务出错: {p2_id}, {exc}")

    async def download(self, video_info: VideoInfo) -> None:
        """按剧集调度影视下载流程。

        参数:
            video_info: 已解析出的影视详情。
        返回值:
            None。
        """

        if not video_info.episodes:
            self.warning(f"未解析到剧集: {video_info.title}")
            return

        semaphore = asyncio.Semaphore(self.config.episode_concurrency)

        async def _episode_task(episode: VideoEpisode) -> None:
            async with semaphore:
                await self._download_episode(video_info, episode)

        handles = self.exc.submit_many_inside(
            [_episode_task(episode) for episode in video_info.episodes],
            mode="async",
        )
        for handle in handles:
            try:
                await handle
            except Exception as exc:
                self.error(f"单集下载失败: {exc}")

    async def _download_episode(self, video_info: VideoInfo, episode: VideoEpisode) -> None:
        paths = self.video_manager.build_episode_paths(video_info, episode)
        if self.video_manager.should_skip_episode(paths):
            return

        m3u8_url = episode.m3u8_url or await self.get_real_m3u8_url(episode.page_url)
        if not m3u8_url:
            raise Notfound(f"未找到 m3u8 地址: {episode.title}", resource=episode.page_url)

        playlist = await self.video_manager.resolve_playlist(m3u8_url, self._fetch_m3u8_text)
        await self._download_segments(playlist.segment_urls, paths)
        output_file = await self.video_manager.merge_segments(paths)
        self.info(f"单集下载完成: {output_file}")
        await self.video_manager.cleanup_episode(paths)

    async def _fetch_m3u8_text(self, url: str) -> str:
        response = await self.get(self.session, url)
        text = response.text
        if not text:
            raise No(f"m3u8 内容为空: {url}")
        return text

    async def _download_segments(self, segment_urls: list[str], paths) -> None:
        semaphore = asyncio.Semaphore(self.config.segment_concurrency)

        async def _segment_task(index: int, segment_url: str) -> bool:
            async with semaphore:
                return await self._download_one_segment(index, segment_url, paths)

        tasks = [
            _segment_task(index, segment_url)
            for index, segment_url in enumerate(segment_urls, start=1)
        ]
        handles = self.exc.submit_many_inside(tasks, mode="async")

        failures: list[Any] = []
        for handle in handles:
            try:
                if await handle is False:
                    failures.append(handle)
            except Exception as exc:
                failures.append(exc)

        if failures:
            raise RuntimeError(f"分片下载失败: {len(failures)}/{len(segment_urls)}")

    async def _download_one_segment(self, index: int, segment_url: str, paths) -> bool:
        if self.video_manager.segment_exists(paths, index):
            return True

        for retry_index in range(self.config.segment_retry + 1):
            try:
                response = await self.get(self.session, segment_url, check_fp=False)
                content = response.content
                if not content:
                    raise No(f"分片内容为空: {segment_url}")
                await self.video_manager.write_segment(paths, index, content)
                return True
            except Exception as exc:
                if retry_index >= self.config.segment_retry:
                    self.error(f"分片重试耗尽: {segment_url}, 错误: {exc}")
                    return False
                await asyncio.sleep(0.3 * (retry_index + 1))
        return False

    async def _fetch_video_info(self, p2_id: Any) -> VideoInfo:
        if isinstance(p2_id, VideoInfo):
            return self._normalize_video_info(p2_id, p2_id.id, p2_id.url)

        video_id = self._resolve_video_id(p2_id)
        detail_url = self._format_p2_source_url(p2_id)
        response = await self.get(self.session, detail_url)
        html_str = response.text
        if not html_str:
            raise No(f"详情页响应为空: {detail_url}")

        parsed = await self._call_parse_p2(html_str, detail_url, video_id)
        return self._coerce_video_info(parsed, video_id, detail_url)

    async def _call_parse_p2(self, html_str: str, detail_url: str, video_id: Any) -> Any:
        signature = inspect.signature(self.parse_p2)
        params = list(signature.parameters.values())
        accepts_args = any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in params)
        positional = [
            param
            for param in params
            if param.kind
            in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        if accepts_args or len(positional) >= 3:
            return await self.parse_html(self.parse_p2, html_str, detail_url, video_id)
        return await self.parse_html(self.parse_p2, html_str, detail_url)

    async def get_real_m3u8_url(self, episode_page_url: str) -> str | None:
        if not episode_page_url:
            return None
        response = await self.get(self.session, self.format_p3_url(episode_page_url))
        parsed = await self.parse_html(self.parse_p3, response.text, episode_page_url)
        return self._extract_m3u8_url(parsed)

    @staticmethod
    def _coerce_page_items(parsed: Any) -> list[Any]:
        if isinstance(parsed, P1Result | PageParseResult):
            return parsed.items
        if isinstance(parsed, list):
            return parsed
        return [parsed]

    @staticmethod
    def _resolve_video_id(source: Any) -> Any:
        return getattr(source, "id", None) or getattr(source, "name", None) or source

    def _format_p2_source_url(self, source: Any) -> str:
        raw_url = getattr(source, "url", source)
        return self.format_p2_url(raw_url)

    def _coerce_video_info(self, parsed: Any, video_id: Any, detail_url: str) -> VideoInfo:
        if isinstance(parsed, VideoInfo):
            return self._normalize_video_info(parsed, video_id, detail_url)
        if isinstance(parsed, P2Result):
            if not parsed.items:
                raise Notfound("未解析到影视详情", resource=detail_url)
            return self._from_p2_item(parsed.items[0], video_id, detail_url)
        if isinstance(parsed, P2Item):
            return self._from_p2_item(parsed, video_id, detail_url)
        if isinstance(parsed, dict):
            return self._from_dict(parsed, video_id, detail_url)
        raise TypeError(f"无法转换影视详情数据: {type(parsed).__name__}")

    def _normalize_video_info(self, info: VideoInfo, video_id: Any, detail_url: str) -> VideoInfo:
        info.id = info.id if info.id is not None else video_id
        info.url = info.url or detail_url
        info.episodes = self._normalize_episodes(info.episodes)
        return info

    def _from_p2_item(self, item: P2Item, video_id: Any, detail_url: str) -> VideoInfo:
        return VideoInfo(
            id=video_id,
            title=item.name,
            url=item.url or detail_url,
            description=item.description or "",
            episodes=self._normalize_episodes(item.p3items),
            other=item.other,
        )

    def _from_dict(self, data: dict[str, Any], video_id: Any, detail_url: str) -> VideoInfo:
        raw_episodes = data.get("episodes") or data.get("p3items") or []
        return VideoInfo(
            id=data.get("id", video_id),
            title=str(data.get("title") or data.get("name") or video_id),
            url=str(data.get("url") or detail_url),
            description=str(data.get("description") or ""),
            episodes=self._normalize_episodes(raw_episodes),
            other=data.get("other"),
        )

    def _normalize_episodes(self, raw_episodes: list[Any]) -> list[VideoEpisode]:
        episodes: list[VideoEpisode] = []
        for index, item in enumerate(raw_episodes or [], start=1):
            episode = self._coerce_episode(item, index)
            episode.index = index
            episodes.append(episode)
        return episodes

    def _coerce_episode(self, item: Any, index: int) -> VideoEpisode:
        if isinstance(item, VideoEpisode):
            return item
        if isinstance(item, P3Item):
            return VideoEpisode(
                index=item.id or index,
                title=item.name or f"第{index}集",
                page_url=self.format_p3_url(item.url),
                m3u8_url=self._extract_m3u8_url(item.content) or self._extract_m3u8_url(item.other),
                description=item.description,
                other=item.other,
            )
        if isinstance(item, dict):
            page_url = str(item.get("page_url") or item.get("url") or "")
            return VideoEpisode(
                index=int(item.get("index") or item.get("id") or index),
                title=str(item.get("title") or item.get("name") or f"第{index}集"),
                page_url=self.format_p3_url(page_url),
                m3u8_url=item.get("m3u8_url") or self._extract_m3u8_url(item),
                description=item.get("description"),
                other=item.get("other"),
            )
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            return VideoEpisode(
                index=index,
                title=str(item[0] or f"第{index}集"),
                page_url=self.format_p3_url(item[1]),
                m3u8_url=str(item[2]) if len(item) >= 3 and item[2] else None,
            )
        raise TypeError(f"无法转换剧集数据: {item!r}")

    @classmethod
    def _extract_m3u8_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, VideoEpisode):
            return value.m3u8_url or cls._extract_m3u8_url(value.page_url)
        if isinstance(value, P3Item):
            return cls._extract_m3u8_url(value.content) or cls._extract_m3u8_url(value.url)
        if isinstance(value, dict):
            for key in ("m3u8_url", "m3u8", "url", "content"):
                result = cls._extract_m3u8_url(value.get(key))
                if result:
                    return result
            return None
        text = str(value)
        if text.startswith(("http://", "https://")) and ".m3u8" in text.lower():
            return text
        match = cls.M3U8_RE.search(text)
        return match.group(0) if match else None


VideoSpiderBase = Ys

__all__ = ["VideoSpiderBase", "Ys"]
