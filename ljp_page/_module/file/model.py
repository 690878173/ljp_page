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


class ManagedAsyncFile:
    """自行管理生命周期的异步文件对象。

    与 AioFile 不同，本类自行持有 aiofiles 句柄并管理打开/关闭/模式切换，
    不依赖外部 FileHandler 池。
    """

    def __init__(
        self,
        file_path: str | Path,
        mode: str = "a+",
        encoding: str = "utf-8",
    ) -> None:
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

            import aiofiles
            self._file_obj = await aiofiles.open(self.path, **open_kwargs)
            self.mode = target_mode
            self.encoding = target_encoding
            return self
        except Exception as exc:
            raise RuntimeError(f"打开文件失败: {self.path}") from exc

    async def close(self) -> None:
        if not self.opened:
            self._file_obj = None
            return
        try:
            if any(flag in self.mode for flag in ["w", "a", "+"]):
                await self._file_obj.flush()
            await self._file_obj.close()
            self._file_obj = None
        except Exception as exc:
            raise RuntimeError(f"关闭文件失败: {self.path}") from exc

    async def switch_mode(
        self,
        mode: str,
        encoding: str | None = None,
    ) -> "ManagedAsyncFile":
        return await self.open(mode=mode, encoding=encoding)

    async def switch_to_read(self) -> "ManagedAsyncFile":
        await self.switch_mode("r")
        await self.seek(0)
        return self

    async def switch_to_write(self, append: bool = True) -> "ManagedAsyncFile":
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


__all__ = ['SyncFile', "AioFile", "ManagedAsyncFile"]