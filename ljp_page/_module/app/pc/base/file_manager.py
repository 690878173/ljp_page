"""文件管理器 —— 封装目录与文件句柄资源。"""

from __future__ import annotations

from ljp_page._module.file.manager import Directory

from .config import Config


class FileManager:
    """管理输出目录结构。

    属性:
        directory: 目录分片管理器。
    """

    def __init__(self, config: Config) -> None:
        self.directory = Directory(
            config.save_path,
            directory_num=config.directory_num,
            mode=config.directory_mode,
        )

    async def init(self) -> None:
        pass

    async def close(self) -> None:
        pass
