from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from .ljp_async import Async
from .ljp_threadpool import ThreadPool
from .backend_async import AsyncBackend
from .base import BaseBackend
from .backend_process import ProcessBackend
from .backend_sync import SyncBackend
from .backend_thread import ThreadBackend

if TYPE_CHECKING:
    from ljp_page._module.tools.bind import BindTask

__all__ = ["BackendRouter"]

class BackendRouter:
    """负责 mode 解析与后端懒加载。"""

    SUPPORTED_MODES = {"auto", "sync", "async", "thread", "process"}

    def __init__(
        self,
        *,
        logger: Any = None,
        thread_pool: ThreadPool | None = None,
        asy: Async | None = None,
        thread_max_workers: int | None = None,
        thread_name_prefix: str = "LjpExcThreadPool",
        async_mode: int = 1,
    ) -> None:
        self.logger = logger
        self.thread_pool = thread_pool
        self.asy = asy
        self.process_pool = None

        self._thread_max_workers = thread_max_workers
        self._thread_name_prefix = thread_name_prefix
        self._async_mode = async_mode

        self._sync_backend: SyncBackend = SyncBackend()
        self._thread_backend: ThreadBackend | None = None
        self._async_backend: AsyncBackend | None = None
        self._process_backend: ProcessBackend = ProcessBackend()

    def validate_mode(self, mode: str) -> None:
        """校验 mode 是否受支持。"""
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"不支持的 mode: {mode}")

    def resolve_mode(self, bound_task: BindTask, mode: str) -> str:
        """根据目标类型和上下文解析最终 mode。"""
        self.validate_mode(mode)
        if mode != "auto":
            return mode

        if bound_task.is_async_target():
            return "async"

        if self._in_running_loop():
            return "thread"

        return "sync"

    def get_backend(self, resolved_mode: str) -> BaseBackend:
        """按 mode 懒加载后端。"""
        if resolved_mode == "sync":
            return self._sync_backend

        if resolved_mode == "thread":
            if self._thread_backend is None:
                self._thread_backend = ThreadBackend(
                    pool=self.thread_pool,
                    max_workers=self._thread_max_workers,
                    thread_name_prefix=self._thread_name_prefix,
                    logger=self.logger,
                )
                self.thread_pool = self._thread_backend.pool
            return self._thread_backend

        if resolved_mode == "async":
            if self._async_backend is None:
                self._async_backend = AsyncBackend(
                    runtime=self.asy,
                    async_mode=self._async_mode,
                    logger=self.logger,
                )
                self.asy = self._async_backend.runtime
            return self._async_backend

        if resolved_mode == "process":
            return self._process_backend

        raise ValueError(f"未知 mode: {resolved_mode}")

    def select_backend(self, bound_task: BindTask, mode: str) -> tuple[str, BaseBackend]:
        """一步完成 mode 解析与后端选择。"""
        resolved_mode = self.resolve_mode(bound_task, mode)
        return resolved_mode, self.get_backend(resolved_mode)

    def shutdown(
        self,
        *,
        wait: bool = True,
        cancel_futures: bool = False,
        async_timeout: float = 5.0,
    ) -> None:
        """关闭已初始化的后端。"""
        if self._thread_backend is not None:
            self._thread_backend.shutdown(wait=wait, cancel_futures=cancel_futures)

        if self._async_backend is not None:
            self._async_backend.shutdown(timeout=async_timeout)

    @staticmethod
    def _in_running_loop() -> bool:
        """判断当前线程是否处于事件循环内。"""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return False
        return True
