from __future__ import annotations

import asyncio
import datetime
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._core.exceptions import CloseFileException, OpenFileException
from ljp_page._core.logger import loguru_logger


# TODO 考虑删除此文件，目录模式考虑保留

class _FileHandlerBase(Ljp_BaseClass_Logger):
    """异步文件句柄池基类。"""

    def __init__(self, max_open_files: int = 100):
        super().__init__()
        self.logger = loguru_logger
        self._max_open_files = max(1, int(max_open_files))
        self._file_dict: OrderedDict[Path, Any] = OrderedDict()
        self._access_time: dict[Path, float] = {}
        self._lock = asyncio.Lock()
        self._is_closed = False

    def _get_max_open_files(self) -> int:
        return self._max_open_files

    def _get_file_count(self) -> int:
        return len(self._file_dict)

    @staticmethod
    def _normalize_path(file_path: str | Path) -> Path:
        return Path(file_path).expanduser().resolve()

    async def _get_file_handle(
        self,
        file_path: str | Path,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> Any:
        if self._is_closed:
            raise OpenFileException("文件句柄管理器已关闭", file_path=file_path)

        normalized_path = self._normalize_path(file_path)
        cached_file = self._file_dict.get(normalized_path)
        if self._is_reusable_handle(cached_file, mode, encoding):
            self._touch(normalized_path)
            return cached_file

        async with self._lock:
            if self._is_closed:
                raise OpenFileException("文件句柄管理器已关闭", file_path=normalized_path)

            cached_file = self._file_dict.get(normalized_path)
            if self._is_reusable_handle(cached_file, mode, encoding):
                self._touch(normalized_path)
                return cached_file

            if cached_file is not None:
                await self._close_file(normalized_path)

            if len(self._file_dict) >= self._max_open_files:
                oldest_path = next(iter(self._file_dict))
                await self._close_file(oldest_path)

            try:
                normalized_path.parent.mkdir(parents=True, exist_ok=True)
                open_kwargs: dict[str, Any] = {"mode": mode}
                if "b" not in mode:
                    open_kwargs["encoding"] = encoding

                file_obj = await aiofiles.open(normalized_path, **open_kwargs)
                self._file_dict[normalized_path] = file_obj
                self._access_time[normalized_path] = time.time()
                return file_obj
            except Exception as exc:
                raise OpenFileException(file_path=normalized_path, e=exc)


    @staticmethod
    def _is_reusable_handle(file_obj: Any, mode: str, encoding: str) -> bool:
        if file_obj is None or getattr(file_obj, "closed", False):
            return False
        if getattr(file_obj, "mode", None) != mode:
            return False
        if "b" in mode:
            return True
        return getattr(file_obj, "encoding", None) == encoding

    def _touch(self, file_path: Path) -> None:
        self._access_time[file_path] = time.time()
        self._file_dict.move_to_end(file_path)

    async def _close_file(self, file_path: str | Path) -> None:
        normalized_path = self._normalize_path(file_path)
        file_obj = self._file_dict.pop(normalized_path, None)
        self._access_time.pop(normalized_path, None)
        if file_obj is None:
            return

        try:
            if getattr(file_obj, "closed", False):
                return
            if any(flag in getattr(file_obj, "mode", "") for flag in ["w", "a", "+"]):
                await file_obj.flush()
            await file_obj.close()
            self.debug(f"关闭文件：{normalized_path}", self._close_file.__name__)
        except Exception as exc:
            raise CloseFileException(file_path=normalized_path, e=exc)

    async def _close_all(self) -> None:
        async with self._lock:
            self._is_closed = True
            for file_path in list(self._file_dict.keys()):
                try:
                    await self._close_file(file_path)
                except Exception as exc:
                    self.error(exc)

        self.info("所有文件句柄已关闭")


class FileHandler(_FileHandlerBase):
    """文件句柄管理器，对外提供异步打开和关闭接口。"""

    async def get(
        self,
        file_path: str | Path,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> Any:
        return await self._get_file_handle(file_path, mode, encoding)

    async def close(self, file_path: str | Path) -> None:
        await self._close_file(file_path)

    async def close_all(self) -> None:
        await self._close_all()

    def get_stats(self) -> dict[str, Any]:
        return {
            "max_open_files": self._get_max_open_files(),
            "current_open_files": self._get_file_count(),
            "closed": self._is_closed,
        }

    async def __aenter__(self) -> "FileHandler":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close_all()


class _DirectoryBase(Ljp_BaseClass_Logger):
    """目录分配器基类。"""

    def __init__(
        self,
        directory_path: str | Path,
        directory_num: int = 100,
        mode: str = "mode1",
    ):
        super().__init__()
        self.logger = loguru_logger
        self._directory_path = Path(directory_path).expanduser().resolve()
        self._directory_num = max(1, int(directory_num))
        self._mode = mode
        self._current_dir: Path | None = None
        self._file_counter = 0
        self._lock = threading.Lock()
        self._file_count_cache: dict[Path, int] = {}
        self._mode_handlers = {
            "mode1": self._get_mode1_directory,
            "mode2": self._get_mode2_directory,
        }
        self._init_directory()

    def _init_directory(self) -> None:
        self._directory_path.mkdir(parents=True, exist_ok=True)
        if self._mode not in self._mode_handlers:
            raise ValueError(f"不支持的目录模式: {self._mode}")
        self._current_dir = self._mode_handlers[self._mode]()

    def _get_file_count(self, dir_path: Path) -> int:
        if dir_path in self._file_count_cache:
            return self._file_count_cache[dir_path]

        if not dir_path.exists():
            self._file_count_cache[dir_path] = 0
            return 0

        count = sum(1 for item in dir_path.iterdir() if item.is_file())
        self._file_count_cache[dir_path] = count
        return count

    def _get_mode1_directory(self) -> Path:
        # mode1：根目录下按 1、2、3... 创建子目录，每个子目录最多存放 directory_num 个文件。
        numeric_dirs = [
            int(item.name)
            for item in self._directory_path.iterdir()
            if item.is_dir() and item.name.isdigit()
        ]
        current_number = max(numeric_dirs, default=1)
        current_dir = self._directory_path / str(current_number)
        current_dir.mkdir(parents=True, exist_ok=True)

        if self._get_file_count(current_dir) >= self._directory_num:
            current_dir = self._directory_path / str(current_number + 1)
            current_dir.mkdir(parents=True, exist_ok=True)

        self._file_counter = self._get_file_count(current_dir)
        return current_dir

    def _get_mode2_directory(self) -> Path:
        current_dir = self._directory_path / datetime.date.today().strftime("%Y-%m-%d")
        current_dir.mkdir(parents=True, exist_ok=True)
        self._file_counter = self._get_file_count(current_dir)
        return current_dir

    def _next_directory(self) -> Path:
        if self._mode == "mode2":
            return self._get_mode2_directory()

        if self._current_dir is None:
            return self._get_mode1_directory()

        if self._file_counter >= self._directory_num:
            next_number = int(self._current_dir.name) + 1
            self._current_dir = self._directory_path / str(next_number)
            self._current_dir.mkdir(parents=True, exist_ok=True)
            self._file_counter = self._get_file_count(self._current_dir)

        return self._current_dir

    def _get_file_path(self, file_name: str | Path) -> Path:
        with self._lock:
            directory = self._next_directory()
            file_path = directory / Path(file_name).name
            if self._mode == "mode1" and not file_path.exists():
                self._file_counter += 1
                self._file_count_cache[directory] = self._file_counter
            return file_path

    def _list_all_files(self, recursive: bool = True) -> list[Path]:
        if recursive:
            return [item for item in self._directory_path.rglob("*") if item.is_file()]
        return [item for item in self._directory_path.iterdir() if item.is_file()]

    def _find_file_path(self, file_name: str | Path, recursive: bool = True) -> Path | None:
        target_name = Path(file_name).name
        files = self._list_all_files(recursive)
        matched_files = [item for item in files if item.name == target_name]
        if not matched_files:
            return None
        return max(matched_files, key=lambda item: item.stat().st_mtime)


class Directory(_DirectoryBase):
    """目录管理器，负责根据模式生成文件保存路径。"""

    def get_file_path(self, file_name: str | Path) -> Path:
        return self._get_file_path(file_name)

    def list_all_files(self, recursive: bool = True) -> list[Path]:
        return self._list_all_files(recursive)

    def find_file_path(self, file_name: str | Path, recursive: bool = True) -> Path | None:
        return self._find_file_path(file_name, recursive)

    def get_current_dir(self) -> Path | None:
        return self._current_dir

    def get_stats(self) -> dict[str, Any]:
        return {
            "directory_path": self._directory_path,
            "current_dir": self._current_dir,
            "file_counter": self._file_counter,
            "directory_num": self._directory_num,
            "mode": self._mode,
        }


class ManagedAsyncFile(Ljp_BaseClass_Logger):
    """自行管理生命周期的异步文件对象。"""

    def __init__(
        self,
        file_path: str | Path,
        mode: str = "a+",
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self.logger = loguru_logger
        self.path = Path(file_path).expanduser().resolve()
        self.mode = mode
        self.encoding = encoding
        self._file_obj: Any = None

    @property
    def opened(self) -> bool:
        return self._file_obj is not None and not getattr(self._file_obj, "closed", True)

    @property
    def closed(self) -> bool:
        return not self.opened

    async def open(
        self,
        mode: str | None = None,
        encoding: str | None = None,
    ) -> "ManagedAsyncFile":
        """打开文件，并记录当前打开模式与编码。"""
        target_mode = mode or self.mode
        target_encoding = encoding or self.encoding

        if self.opened and self.mode == target_mode and self.encoding == target_encoding:
            return self

        if self.opened:
            await self.close()

        try:
            if any(flag in target_mode for flag in ["w", "a", "x", "+"]):
                self.path.parent.mkdir(parents=True, exist_ok=True)

            open_kwargs: dict[str, Any] = {"mode": target_mode}
            if "b" not in target_mode:
                open_kwargs["encoding"] = target_encoding

            self._file_obj = await aiofiles.open(self.path, **open_kwargs)
            self.mode = target_mode
            self.encoding = target_encoding
            return self
        except Exception as exc:
            raise OpenFileException(file_path=self.path, e=exc)

    async def close(self) -> None:
        """刷新并关闭当前文件句柄。"""
        if not self.opened:
            self._file_obj = None
            return

        try:
            if any(flag in self.mode for flag in ["w", "a", "+"]):
                await self._file_obj.flush()
            await self._file_obj.close()
            self._file_obj = None
        except Exception as exc:
            raise CloseFileException(file_path=self.path, e=exc)

    async def switch_mode(
        self,
        mode: str,
        encoding: str | None = None,
    ) -> "ManagedAsyncFile":
        """切换文件打开模式，适合在读取检查与继续写入之间转换。"""
        return await self.open(mode=mode, encoding=encoding)

    async def switch_to_read(self) -> "ManagedAsyncFile":
        """切换为读取模式，并将读取位置移动到文件开头。"""
        await self.switch_mode("r")
        await self.seek(0)
        return self

    async def switch_to_write(self, append: bool = True) -> "ManagedAsyncFile":
        """切换为写入模式，默认追加写入，避免覆盖已有内容。"""
        await self.switch_mode("a" if append else "w")
        return self

    async def read(self, size: int = -1) -> Any:
        if not self.opened:
            await self.open()
        return await self._file_obj.read(size)

    async def write(self, data: Any) -> Any:
        if not self.opened:
            await self.open()
        return await self._file_obj.write(data)

    async def flush(self) -> None:
        if self.opened:
            await self._file_obj.flush()

    async def seek(self, offset: int, whence: int = 0) -> Any:
        if not self.opened:
            await self.open()
        return await self._file_obj.seek(offset, whence)

    async def tell(self) -> Any:
        if not self.opened:
            await self.open()
        return await self._file_obj.tell()

    async def __aenter__(self) -> "ManagedAsyncFile":
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()


__all__ = ["Directory", "FileHandler", "ManagedAsyncFile"]
