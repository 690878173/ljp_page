# 03-29-00-16-00
"""影视下载管理器。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Sequence

from ljp_page.core.base.base_class import Ljp_BaseClass

from .ffmpeg import FfmpegConfig, FfmpegVideoMerger
from .m3u8_parser import M3u8Parser
from .models import VideoEpisode, VideoInfo, YsConfig
from .storage import EpisodePaths, VideoStorage


class BaseVideoManager(Ljp_BaseClass):
    """影视下载管理器基类。"""

    def __init__(self, spider: Any, config: YsConfig, logger: Any = None) -> None:
        super().__init__(logger=logger)
        self.spider = spider
        self.config = config
        self.storage = VideoStorage(config.save_path, logger=logger)
        self.m3u8_parser = M3u8Parser(logger=logger)
        self.merger = FfmpegVideoMerger(
            FfmpegConfig(
                ffmpeg_path=config.ffmpeg_path,
                log_level=config.ffmpeg_log_level,
            ),
            logger=logger,
        )

    async def download_video(self, session: Any, video_info: VideoInfo) -> None:
        raise NotImplementedError


class VideoManager(BaseVideoManager):
    """默认影视下载实现：解析 m3u8、并发下载 ts、ffmpeg 合并。"""

    async def download_video(self, session: Any, video_info: VideoInfo) -> None:
        semaphore = asyncio.Semaphore(max(1, self.config.episode_concurrency))

        async def _episode_task(episode: VideoEpisode) -> None:
            async with semaphore:
                await self._download_episode(session, video_info, episode)

        tasks = [_episode_task(episode) for episode in video_info.episodes]
        results = await self.spider.runtime.gather_inside(tasks, return_exceptions=True)
        for item in results:
            if isinstance(item, Exception):
                self.error(f"episode download failed: {item}")

    async def _download_episode(
        self,
        session: Any,
        video_info: VideoInfo,
        episode: VideoEpisode,
    ) -> None:
        paths = self.storage.build_episode_paths(video_info.title, episode.index, episode.title)

        if self.config.skip_existing and paths.output_file.exists():
            self.info(f"skip existing episode: {paths.output_file}")
            return

        m3u8_url = episode.m3u8_url or await self.spider.get_real_m3u8_url(episode.page_url)
        if not m3u8_url:
            raise ValueError(f"m3u8 url not found: {episode.title}")

        playlist = await self._resolve_playlist(session, m3u8_url)
        await self._download_segments(session, playlist.segment_urls, paths)
        await self._merge_segments(paths)

        if self.config.cleanup_segments:
            await self.spider.runtime.run_in_thread(self.storage.cleanup_segment_dir, paths.segment_dir)

    async def _resolve_playlist(self, session: Any, m3u8_url: str):
        async def _fetch(url: str) -> str:
            text = await self.spider.req.async_get(session=session, url=url, return_type="text")
            if not text:
                raise ValueError(f"empty m3u8 content: {url}")
            return text

        return await self.m3u8_parser.resolve(
            m3u8_url,
            _fetch,
            max_depth=self.config.max_m3u8_depth,
        )

    async def _download_segments(
        self,
        session: Any,
        segment_urls: Sequence[str],
        paths: EpisodePaths,
    ) -> None:
        semaphore = asyncio.Semaphore(max(1, self.config.segment_concurrency))

        async def _segment_task(index: int, segment_url: str) -> bool:
            async with semaphore:
                return await self._download_one_segment(session, index, segment_url, paths)

        tasks = [
            _segment_task(index, segment_url)
            for index, segment_url in enumerate(segment_urls, start=1)
        ]
        results = await self.spider.runtime.gather_inside(tasks, return_exceptions=True)
        failures = [item for item in results if isinstance(item, Exception) or item is False]
        if failures:
            raise RuntimeError(f"segment download failed: {len(failures)}/{len(segment_urls)}")

    async def _download_one_segment(
        self,
        session: Any,
        index: int,
        segment_url: str,
        paths: EpisodePaths,
    ) -> bool:
        target_file = self.storage.build_segment_file(paths.segment_dir, index)
        if target_file.exists() and target_file.stat().st_size > 0:
            return True

        for retry_index in range(self.config.segment_retry + 1):
            try:
                content = await self.spider.req.async_get(
                    session=session,
                    url=segment_url,
                    return_type="content",
                )
                if not content:
                    raise ValueError("empty segment content")

                # 中文注释：写磁盘放在线程池里，避免大分片写入阻塞事件循环。
                await self.spider.runtime.run_in_thread(target_file.write_bytes, content)
                return True
            except Exception as exc:
                if retry_index >= self.config.segment_retry:
                    self.error(f"segment retry exhausted: {segment_url}, error={exc}")
                    return False
                await asyncio.sleep(0.3 * (retry_index + 1))
        return False

    async def _merge_segments(self, paths: EpisodePaths) -> Path:
        segment_files = sorted(paths.segment_dir.glob("*.ts"), key=lambda item: item.name)
        if not segment_files:
            raise RuntimeError(f"no ts files found: {paths.segment_dir}")
        return await self.merger.merge(segment_files, paths.filelist_file, paths.output_file)


__all__ = ["BaseVideoManager", "VideoManager"]
