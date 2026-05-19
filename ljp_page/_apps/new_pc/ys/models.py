# 05-19-14-34-05
"""new_pc 影视下载模型与配置。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..base.model import Config, Mode


@dataclass
class VideoEpisode:
    """单集信息。

    参数:
        index: 集数序号。
        title: 单集标题。
        page_url: 播放页地址。
        m3u8_url: 可选的真实 m3u8 地址。
    返回值:
        VideoEpisode: 单集数据对象。
    """

    index: int
    title: str
    page_url: str = ""
    m3u8_url: str | None = None
    description: str | None = None
    other: Any = None


@dataclass
class VideoInfo:
    """影视详情信息。"""

    id: Any
    title: str
    url: str
    description: str = ""
    episodes: list[VideoEpisode] = field(default_factory=list)
    other: Any = None

    @property
    def total_episodes(self) -> int:
        return len(self.episodes)


@dataclass
class PageParseResult:
    """分页解析结果。"""

    items: list[Any] = field(default_factory=list)
    next_url: str | None = None
    other: Any = None


@dataclass
class YsConfig(Config):
    """new_pc 影视下载配置。"""

    episode_concurrency: int = 3
    segment_concurrency: int = 16
    segment_retry: int = 2
    max_m3u8_depth: int = 3

    skip_existing: bool = True
    cleanup_segments: bool = True
    output_suffix: str = "mp4"
    ffmpeg_path: str = "ffmpeg"
    ffmpeg_log_level: str = "error"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.episode_concurrency = max(1, int(self.episode_concurrency))
        self.segment_concurrency = max(1, int(self.segment_concurrency))
        self.segment_retry = max(0, int(self.segment_retry))
        self.max_m3u8_depth = max(0, int(self.max_m3u8_depth))
        self.output_suffix = self.output_suffix.strip().lstrip(".") or "mp4"
        if self.mode == Mode.MODE2 and not self.p1_url:
            raise ValueError("YsConfig 在 mode2 下必须配置 p1_url")


__all__ = ["PageParseResult", "VideoEpisode", "VideoInfo", "YsConfig"]
