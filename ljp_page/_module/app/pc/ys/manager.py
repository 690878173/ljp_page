# 05-19-14-34-05
"""new_pc 影视下载管理器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable

from ljp_page._core._base_class import Ljp_BaseClass

from .ffmpeg import FfmpegConfig, FfmpegVideoMerger
from .m3u8_parser import M3u8Parser, M3u8Playlist
from .models import VideoEpisode, VideoInfo, YsConfig
from .storage import EpisodePaths, VideoStorage


class BaseVideoManager(Ljp_BaseClass):
    """影视下载管理器基类。"""

    def __init__(self, spider: Any, config: YsConfig, logger: Any = None) -> None:
        super().__init__()
        self.set_logger(logger)
        self.spider = spider
        self.config = config
        self.storage = VideoStorage(config.save_path, logger=logger)
        self.m3u8_parser = M3u8Parser()
        self.m3u8_parser.set_logger(logger)
        self.merger = FfmpegVideoMerger(
            FfmpegConfig(
                ffmpeg_path=config.ffmpeg_path,
                log_level=config.ffmpeg_log_level,
            ),
            logger=logger,
        )

    def build_episode_paths(
        self,
        video_info: VideoInfo,
        episode: VideoEpisode,
    ) -> EpisodePaths:
        raise NotImplementedError

    def should_skip_episode(self, paths: EpisodePaths) -> bool:
        raise NotImplementedError


class VideoManager(BaseVideoManager):
    """影视落盘管理器，负责路径、写入、合并和临时文件清理。"""

    def build_episode_paths(
        self,
        video_info: VideoInfo,
        episode: VideoEpisode,
    ) -> EpisodePaths:
        return self.storage.build_episode_paths(
            video_info.title,
            episode.index,
            episode.title,
            self.config.output_suffix,
        )

    def should_skip_episode(self, paths: EpisodePaths) -> bool:
        if self.config.skip_existing and paths.output_file.exists():
            self.info(f"检测到已存在文件，跳过: {paths.output_file}")
            return True
        return False

    async def resolve_playlist(
        self,
        m3u8_url: str,
        fetch_text: Callable[[str], Awaitable[str]],
    ) -> M3u8Playlist:
        return await self.m3u8_parser.resolve(
            m3u8_url,
            fetch_text,
            max_depth=self.config.max_m3u8_depth,
        )

    def segment_exists(self, paths: EpisodePaths, index: int) -> bool:
        target_file = self.storage.build_segment_file(paths.segment_dir, index)
        return target_file.exists() and target_file.stat().st_size > 0

    async def write_segment(self, paths: EpisodePaths, index: int, content: bytes) -> Path:
        target_file = self.storage.build_segment_file(paths.segment_dir, index)
        # 中文注释：分片写入属于落盘操作，统一交给管理器走线程池写入。
        await self.spider.exc.submit(target_file.write_bytes, content, mode="thread")
        return target_file

    async def merge_segments(self, paths: EpisodePaths) -> Path:
        segment_files = sorted(paths.segment_dir.glob("*.ts"), key=lambda item: item.name)
        if not segment_files:
            raise RuntimeError(f"未找到视频分片: {paths.segment_dir}")
        return await self.merger.merge(segment_files, paths.filelist_file, paths.output_file)

    async def cleanup_episode(self, paths: EpisodePaths) -> None:
        if self.config.cleanup_segments:
            await self.spider.exc.submit(
                self.storage.cleanup_segment_dir,
                paths.segment_dir,
                mode="thread",
            )


__all__ = ["BaseVideoManager", "VideoManager"]
