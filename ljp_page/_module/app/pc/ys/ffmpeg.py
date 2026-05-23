# 05-19-14-34-05
"""FFmpeg 视频合并器。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ljp_page._core._base_class import Ljp_Logger


@dataclass(slots=True)
class FfmpegConfig:
    """ffmpeg 合并配置。"""

    ffmpeg_path: str = "ffmpeg"
    log_level: str = "error"


class BaseVideoMerger(Ljp_Logger):
    """视频合并器基类。"""

    async def merge(
        self,
        segment_files: Sequence[Path],
        filelist_path: Path,
        output_file: Path,
    ) -> Path:
        raise NotImplementedError


class FfmpegVideoMerger(BaseVideoMerger):
    """基于 ffmpeg concat 的分片合并实现。"""

    def __init__(self, config: FfmpegConfig, logger=None) -> None:
        super().__init__()
        self.set_logger(logger)
        self.config = config

    async def merge(
        self,
        segment_files: Sequence[Path],
        filelist_path: Path,
        output_file: Path,
    ) -> Path:
        if not segment_files:
            raise ValueError("没有可合并的视频分片")

        filelist_path.parent.mkdir(parents=True, exist_ok=True)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"file '{item.name}'" for item in segment_files]
        filelist_path.write_text("\n".join(lines), encoding="utf-8", newline="")

        command = [
            self.config.ffmpeg_path,
            "-loglevel",
            self.config.log_level,
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(filelist_path),
            "-c",
            "copy",
            "-y",
            str(output_file),
        ]
        proc = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(filelist_path.parent),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            message = stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"ffmpeg 合并失败: {message}")
        return output_file


__all__ = ["BaseVideoMerger", "FfmpegConfig", "FfmpegVideoMerger"]
