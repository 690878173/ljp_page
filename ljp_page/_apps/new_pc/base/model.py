# 05-19-15-08-00
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ljp_page._modules.request.cg_session.config import LjpConfig


class ModeType:
    """new_pc 运行模式常量。"""

    MODE1 = "mode1"
    MODE2 = "mode2"
    MODE3 = "mode3"

    VALUES = {MODE1, MODE2, MODE3}


@dataclass
class Config:
    """new_pc 通用配置。"""
    base_url: str = ""
    p2_url: str | None = None
    p1_url: str | None = None
    p3_url: str | None = None
    save_path: str = "res/"

    start_id: int = 1
    end_id: int = 5
    id_ls: list[Any] | None = None

    mode: str = ModeType.MODE1
    max_workers: int = 5
    chapter_concurrency: int = 99999999
    max_open_files: int = 200
    directory_num: int = 100
    directory_mode: str = "mode1"
    worker_startup_delay: float = 1.0
    queue_get_timeout: float = 2.0
    session_close_timeout: float = 2.0

    ljp_config: LjpConfig = field(default_factory=LjpConfig)

    def __post_init__(self) -> None:
        if self.mode not in ModeType.VALUES:
            raise ValueError(f"不支持的运行模式: {self.mode}")
        if self.max_workers < 1:
            raise ValueError("max_workers 必须大于等于 1")
        if self.chapter_concurrency < 1:
            raise ValueError("chapter_concurrency 必须大于等于 1")
        if self.max_open_files < 1:
            raise ValueError("max_open_files 必须大于等于 1")
        if self.worker_startup_delay < 0:
            raise ValueError("worker_startup_delay 不能小于 0")
        if self.queue_get_timeout <= 0:
            raise ValueError("queue_get_timeout 必须大于 0")
        if self.session_close_timeout <= 0:
            raise ValueError("session_close_timeout 必须大于 0")

        if self.id_ls is None:
            if self.start_id > self.end_id:
                raise ValueError("start_id 不能大于 end_id")
            self.id_ls = [str(i) for i in range(self.start_id, self.end_id + 1)]
            return
        self.id_ls = list(self.id_ls)


@dataclass
class P1Item:
    name: str
    url: str
    description: str | None = None

    next_url: str | None = None
    other: Any = None

@dataclass
class P1Result:
    items: list[P1Item] = field(default_factory=list)
    next_url: str | None = None


@dataclass
class P3Item:
    url: str
    name: str
    p2_name: str = ""
    content: str = ""
    id: int | None = None

    description: str | None = None
    next_url: str | None = None
    other: Any = None


@dataclass
class P2Item:
    url: str
    name: str
    author: str
    description: str
    p3items: list[P3Item]

    next_url: str | None = None
    other: Any = None

    def __post_init__(self) -> None:
        p3_id = 1
        for p3item in self.p3items:
            if p3item.id is None:
                p3item.id = p3_id
            p3_id += 1



@dataclass
class P2Result:
    items: list[P2Item] = field(default_factory=list)

    next_url: str | None = None
    other: Any = None


Mode = ModeType
PcConfig = Config

__all__ = [
    "ModeType",
    "Mode",
    "Config",
    "PcConfig",
    "P1Item",
    "P1Result",
    "P2Item",
    "P2Result",
    "P3Item",
]
