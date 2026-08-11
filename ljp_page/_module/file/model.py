from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import io
import time

if TYPE_CHECKING:
    from aiofiles.threadpool.text import AsyncTextIOWrapper

# 运行时延迟导入aiofiles，不在这里顶层import


class BaseFile(ABC):
    """统一抽象接口，同步、异步都遵守这套方法名"""
    def __init__(self, path, mode: str = "a", encoding: str = "utf-8"):
        self.path: Path = Path(path).expanduser().resolve()
        self.mode = mode
        self.encoding = encoding
        self._write_num = 0
        self.need_flush_num = 10  # 修正拼写
        self.last_write_ts = time.time()


    @abstractmethod
    def open(self):
        ...

    @abstractmethod
    def write(self, data: str):
        ...

    @abstractmethod
    def close(self):
        ...

    @abstractmethod
    def read(self) -> str:
        ...

    @abstractmethod
    def readlines(self) -> list[str]:
        ...


class SyncFile(BaseFile):
    def __init__(self, path, mode: str = "a", encoding: str = "utf-8"):
        super().__init__(path, mode, encoding)
        self._fp: io.TextIOBase | None = None

    def open(self):
        if self._fp is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fp = open(self.path, mode=self.mode, encoding=self.encoding)

    def write(self, data: str):
        if self._fp is None:
            self.open()
        self._fp.write(data)
        self.last_write_ts = time.time()
        self._write_num += 1
        if self._write_num >= self.need_flush_num:
            self._write_num = 0
            self._fp.flush()



    def read(self) -> str:
        if self._fp is None:
            self.open()
        return self._fp.read()

    def readlines(self) -> list[str]:
        if self._fp is None:
            self.open()
        return self._fp.readlines()

    def close(self):
        if self._fp is not None:
            self._fp.flush()
            self._fp.close()
            self._fp = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AioFile(BaseFile):
    def __init__(self, path, mode: str = "a", encoding: str = "utf-8"):
        super().__init__(path, mode, encoding)
        self._fp: Optional["AsyncTextIOWrapper"] = None

    def _load_dep(self):
        try:
            import aiofiles
            from aiofiles.threadpool.text import AsyncTextIOWrapper
        except ImportError as e:
            raise RuntimeError("使用AioFile需要安装aiofiles: pip install aiofiles") from e
        globals()["aiofiles"] = aiofiles

    async def open(self):
        self._load_dep()
        if self._fp is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            import aiofiles
            self._fp = await aiofiles.open(self.path, mode=self.mode, encoding=self.encoding)

    async def write(self, data: str):
        if self._fp is None:
            await self.open()
        await self._fp.write(data)
        self.last_write_ts = time.time()
        self._write_num += 1
        if self._write_num >= self.need_flush_num:
            self._write_num = 0
            await self._fp.flush()

    async def read(self) -> str:
        if self._fp is None:
            await self.open()
        return await self._fp.read()

    async def readlines(self) -> list[str]:
        if self._fp is None:
            await self.open()
        return await self._fp.readlines()

    async def close(self):
        if self._fp is not None:
            await self._fp.flush()
            await self._fp.close()
            self._fp = None

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


__all__ = ['SyncFile', "AioFile"]