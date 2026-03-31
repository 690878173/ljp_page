# 03-29-00-00-00
"""影视爬虫数据模型与配置。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ljp_page.applications.pc.base.models import Mode, PcConfig


@dataclass
class VideoEpisode:
    """单集信息。"""

    index: int
    title: str
    page_url: str
    m3u8_url: str | None = None


@dataclass
class VideoInfo:
    """影视详情信息。"""

    id: Any
    title: str
    url: str
    description: str
    episodes: List[VideoEpisode] = field(default_factory=list)

    @property
    def total_episodes(self) -> int:
        return len(self.episodes)


@dataclass
class PageParseResult:
    """分页解析结果。"""

    items: List[Any] = field(default_factory=list)
    next_url: Optional[str] = None


@dataclass
class YsConfig(PcConfig):
    """影视爬虫配置。"""

    info_url: str = ""
    page_url: Optional[str] = None

    episode_concurrency: int = 3
    segment_concurrency: int = 16
    segment_retry: int = 2
    max_m3u8_depth: int = 3
    download_chunk_size: int = 64 * 1024

    skip_existing: bool = True
    cleanup_segments: bool = True
    ffmpeg_path: str = "ffmpeg"
    ffmpeg_log_level: str = "error"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.info_url:
            raise ValueError("config error: info_url cannot be empty")
        if "{}" not in self.info_url:
            raise ValueError(f"config error: info_url must include '{{}}': {self.info_url}")
        if not self.info_url.startswith(("http://", "https://")):
            raise ValueError(
                f"config error: info_url must start with http/https: {self.info_url}"
            )

        if self.page_url is not None:
            if "{}" not in self.page_url:
                raise ValueError(f"config error: page_url must include '{{}}': {self.page_url}")
            if not self.page_url.startswith(("http://", "https://")):
                raise ValueError(
                    f"config error: page_url must start with http/https: {self.page_url}"
                )

        if self.mode == Mode.MODE2 and not self.page_url:
            raise ValueError("config error: ys mode2 requires page_url")


__all__ = ["PageParseResult", "VideoEpisode", "VideoInfo", "YsConfig"]
