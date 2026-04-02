# 04-01-20-18-00
"""Xs 爬虫核心实现。"""

from __future__ import annotations

from typing import Any

from ..base import Pc

from .manager import XsManager


class Xs(Pc):
    """小说爬虫：实现章节清洗与顺序落盘。"""

    def get_manager(self) -> Any:
        self.manager = XsManager
        return self.manager


__all__ = ["Xs"]
