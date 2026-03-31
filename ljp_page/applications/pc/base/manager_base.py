# 03-28-21-05-00
"""PC 章节写入管理器基类。"""

from __future__ import annotations

import asyncio
import inspect
import re
from typing import Any, Dict

from ....logger import Logger
from ljp_page.core.base.base_class import Ljp_BaseClass

from .models import P2Result, P3Result


class BaseManager(Ljp_BaseClass):
    """章节写入管理器：负责顺序写盘和收尾动作。"""

    P2Result = P2Result
    P3Result = P3Result

    def __init__(self, pc: Any, data: P2Result, file_handle: Any, log: Logger) -> None:
        self.pc = pc
        self.data = data
        self.file_handle = file_handle
        self.logger = log

        self.expected_id = 1
        self.pending: Dict[int, BaseManager.P3Result] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

        super().__init__(self.logger)

    async def add_p3(self, p3: P3Result) -> None:
        raise NotImplementedError("add_p3 must be implemented")

    async def init(self) -> bool:
        if self._initialized:
            return True
        self._initialized = True

        try:
            result = self.target_init()
            if inspect.isawaitable(result):
                await result
            self.info(f"manager initialized: {self.data.title}")
            return True
        except Exception as exc:
            self.error(f"manager init failed: {self.data.title}, error: {exc}")
            return False

    async def target_init(self) -> None:
        return None

    async def finish(self) -> None:
        self.info(f"manager finished: {self.data.title}")

    @staticmethod
    def sanitize_filename(title: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', "_", title)

    @staticmethod
    def get_file_path(title: str) -> str:
        return f"{title}.txt"

    def _get_p_mode(self, title: str, index: int) -> str:
        return title


__all__ = ["BaseManager"]
