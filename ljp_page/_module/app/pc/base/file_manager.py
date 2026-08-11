"""文件管理器 —— 封装目录与文件句柄资源。"""

from __future__ import annotations

from ljp_page._module.file import Directory, FileHandler

from .config import Config


class FileManager:
    """管理输出目录结构和文件句柄池。

    属性:
        directory: 目录分片管理器。
        file_handler: 文件句柄池。
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.directory = Directory(
            config.save_path,
            directory_num=config.directory_num,
            mode=config.directory_mode,
        )
        self.file_handler = FileHandler(
            max_open_files=config.max_open_files,
        )

    async def init(self) -> None:
        pass

    async def close(self) -> None:
        await self.file_handler.close_all()
