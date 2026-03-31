# 03-29-00-03-00
"""影视下载存储策略。"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from ljp_page.core.base.Ljp_base_class import Ljp_BaseClass


@dataclass(slots=True)
class EpisodePaths:
    """单集下载涉及的路径集合。"""

    video_dir: Path
    segment_dir: Path
    output_file: Path
    filelist_file: Path


class VideoStorage(Ljp_BaseClass):
    """统一管理影视下载目录与文件命名。"""

    def __init__(self, root_path: str, logger=None) -> None:
        super().__init__(logger=logger)
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(value: str) -> str:
        bad_chars = '\\/:*?"<>|'
        cleaned = value or "untitled"
        for char in bad_chars:
            cleaned = cleaned.replace(char, "_")
        return cleaned.strip() or "untitled"

    def build_episode_paths(self, video_title: str, episode_index: int, episode_title: str) -> EpisodePaths:
        safe_video = self.sanitize_filename(video_title)
        safe_episode = self.sanitize_filename(episode_title)
        prefix = f"{episode_index:03d}_{safe_episode}"

        video_dir = self.root / safe_video
        segment_dir = video_dir / "_segments" / prefix
        output_file = video_dir / f"{prefix}.mp4"
        filelist_file = segment_dir / "filelist.txt"

        video_dir.mkdir(parents=True, exist_ok=True)
        segment_dir.mkdir(parents=True, exist_ok=True)
        return EpisodePaths(
            video_dir=video_dir,
            segment_dir=segment_dir,
            output_file=output_file,
            filelist_file=filelist_file,
        )

    @staticmethod
    def build_segment_file(segment_dir: Path, sequence: int) -> Path:
        return segment_dir / f"{sequence:05d}.ts"

    def cleanup_segment_dir(self, segment_dir: Path) -> None:
        if segment_dir.exists():
            shutil.rmtree(segment_dir, ignore_errors=True)


__all__ = ["EpisodePaths", "VideoStorage"]
