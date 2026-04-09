# 03-29-00-07-00
"""M3U8 解析器。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, List
from urllib.parse import urljoin

from ljp_page._core.base.Ljp_base_class import Ljp_BaseClass


@dataclass(slots=True)
class M3u8Playlist:
    """解析后的媒体播放列表。"""

    url: str
    segment_urls: List[str] = field(default_factory=list)


class M3u8Parser(Ljp_BaseClass):
    """支持 master/media 两类 m3u8，自动下钻到媒体流。"""

    _bandwidth_pattern = re.compile(r"BANDWIDTH=(\d+)", re.IGNORECASE)

    @classmethod
    def _parse_master_streams(cls, text: str, base_url: str) -> list[tuple[int, str]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        streams: list[tuple[int, str]] = []
        for index, line in enumerate(lines):
            if not line.upper().startswith("#EXT-X-STREAM-INF"):
                continue
            if index + 1 >= len(lines):
                continue
            next_line = lines[index + 1]
            if next_line.startswith("#"):
                continue
            match = cls._bandwidth_pattern.search(line)
            bandwidth = int(match.group(1)) if match else 0
            streams.append((bandwidth, urljoin(base_url, next_line)))
        return streams

    @staticmethod
    def _parse_media_segments(text: str, base_url: str) -> list[str]:
        segments: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            segments.append(urljoin(base_url, line))
        return segments

    async def resolve(
        self,
        url: str,
        fetch_text: Callable[[str], Awaitable[str]],
        *,
        max_depth: int = 3,
    ) -> M3u8Playlist:
        current_url = url
        for _ in range(max_depth + 1):
            text = await fetch_text(current_url)
            streams = self._parse_master_streams(text, current_url)
            if streams:
                # 中文注释：优先使用带宽最高的流，避免默认命中低码率。
                streams.sort(key=lambda item: item[0], reverse=True)
                current_url = streams[0][1]
                continue

            segments = self._parse_media_segments(text, current_url)
            if not segments:
                raise ValueError(f"m3u8 has no segments: {current_url}")
            return M3u8Playlist(url=current_url, segment_urls=segments)

        raise RecursionError(f"m3u8 resolve depth exceeded: {url}")


__all__ = ["M3u8Parser", "M3u8Playlist"]
