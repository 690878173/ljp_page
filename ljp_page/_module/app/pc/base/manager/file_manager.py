from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._module.file import Directory, FileHandler
from .base import Base_Manager

if TYPE_CHECKING:
    from ljp_page._module.app.pc.base.model import Config


class Pc_base_FileManager(Ljp_BaseClass_Logger,Base_Manager):
    """封装文件目录与文件句柄资源。"""

    async def init(self):
        pass

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.directory = Directory(
            config.save_path,
            directory_num=config.directory_num,
            mode=config.directory_mode,
        )
        self.file_handler = FileHandler(
            max_open_files=config.max_open_files,
        )

    async def close(self) -> None:
        await self.file_handler.close_all()


Pc_File_manager = Pc_base_FileManager

__all__ = ["Pc_base_FileManager", "Pc_File_manager"]
