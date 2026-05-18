# 04-29-23-31-00
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ljp_page._modules.request.cg_session.config import LjpConfig


class ModeType:
    """new_pc 运行模式常量。"""

    MODE1 = "mode1"
    MODE2 = "mode2"
    MODE3 = "mode3"


@dataclass
class Config:
    """new_pc 通用配置。"""
    base_url:str = ''
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
        if self.id_ls is None:
            self.id_ls = [str(i) for i in range(self.start_id, self.end_id + 1)]
            return
        self.id_ls = list(self.id_ls)


@dataclass
class P1Item:
    name: str
    url: str
    description: str|None = None

    next_url: str|None = None
    other: Optional[Any] = None

@dataclass
class P1Result:
    items: List[P1Item] = field(default_factory=list)
    next_url: Optional[str] = None


@dataclass
class P3Item:
    url: str
    name: str
    p2_name: str = ""
    content: str = ""
    id: int|None = None

    description: str | None = None
    next_url: str | None = None
    other: Optional[Any] = None


@dataclass
class P2Item:
    url: str
    name: str
    author: str
    description: str
    p3items:list[P3Item]

    next_url: str | None = None
    other: Optional[Any] = None

    def __post_init__(self) -> None:
        p3_id = 1
        for p3item in self.p3items:
            p3item.id = p3_id
            p3_id += 1



@dataclass
class P2Result:
    items: List[P2Item] = field(default_factory=list)

    next_url: str | None = None
    other: Optional[Any] = None

