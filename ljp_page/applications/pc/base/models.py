# 03-31-22-05-00
"""PC crawler data models and runtime config."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from ljp_page.config import LjpConfig


class Mode:
    """Runtime mode constants."""

    MODE1 = "mode1"
    MODE2 = "mode2"
    MODE3 = "mode3"


@dataclass
class PcConfig:
    """通用 PC 爬虫配置。"""

    base_url: str
    save_path: str

    # 文本类爬虫使用 p1/p2；影视类爬虫可为空。
    p2_url: Optional[str] = None
    p1_url: Optional[str] = None

    threadpool_thread_num: int = 10
    runtime_outer_concurrent: int = 20
    runtime_inner_concurrent: int = 100
    max_workers: int = 5
    chapter_concurrency: int = 20
    max_open_files: int = 200

    start_id: int = 1
    end_id: int = 5
    id_ls: Optional[List[Any]] = None

    # 请求配置统一通过 LjpConfig 注入。
    ljp_config: LjpConfig = field(default_factory=LjpConfig)

    mode: str = Mode.MODE1
    worker_startup_delay: float = 1.0
    queue_get_timeout: float = 2.0
    session_close_timeout: float = 2.0

    def __post_init__(self) -> None:
        self._validate_base_params()
        self._validate_save_path()
        self._validate_optional_urls()
        self._validate_id_list()
        self._validate_mode_specific_params()
        # 统一入口：PC 运行时 base_url 与请求配置必须一致，避免双配置分叉。
        if self.ljp_config.request.base_url and self.ljp_config.request.base_url != self.base_url:
            raise ValueError(
                "config error: base_url must match ljp_config.request.base_url"
            )
        self.ljp_config.request.base_url = self.base_url

    @property
    def request_headers(self) -> dict[str, str]:
        """返回请求默认 headers。"""

        return self.ljp_config.request.headers

    @property
    def request_cookies(self) -> dict[str, str]:
        """返回请求默认 cookies。"""

        return self.ljp_config.request.cookies

    def update_request_cookies(self, cookies: dict[str, str]) -> None:
        """合并更新请求 cookies。"""

        self.ljp_config.request.cookies.update(cookies)

    def build_request_config(self) -> LjpConfig:
        """构建运行时使用的请求配置副本。"""

        config = deepcopy(self.ljp_config)
        config.request.base_url = self.base_url
        return config

    def _validate_base_params(self) -> None:
        if not self.base_url:
            raise ValueError("config error: base_url cannot be empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(
                f"config error: base_url must start with http/https: {self.base_url}"
            )

    def _validate_save_path(self) -> None:
        if not self.save_path:
            raise ValueError("config error: save_path cannot be empty")

    def _validate_optional_urls(self) -> None:
        if self.p2_url is not None:
            if "{}" not in self.p2_url:
                raise ValueError(f"config error: p2_url must include '{{}}': {self.p2_url}")
            if not self.p2_url.startswith(("http://", "https://")):
                raise ValueError(
                    f"config error: p2_url must start with http/https: {self.p2_url}"
                )

        if self.p1_url is not None:
            if "{}" not in self.p1_url:
                raise ValueError(f"config error: p1_url must include '{{}}': {self.p1_url}")
            if not self.p1_url.startswith(("http://", "https://")):
                raise ValueError(
                    f"config error: p1_url must start with http/https: {self.p1_url}"
                )

    def _validate_id_list(self) -> None:
        if self.id_ls is None:
            if self.start_id > self.end_id:
                raise ValueError(
                    "config error: "
                    f"start_id({self.start_id}) cannot be larger than end_id({self.end_id})"
                )
            self.id_ls = list(range(self.start_id, self.end_id + 1))
            return

        if not isinstance(self.id_ls, list):
            self.id_ls = list(self.id_ls)

    def _validate_mode_specific_params(self) -> None:
        if self.mode == Mode.MODE2 and not self.p1_url:
            raise ValueError("config error: mode2 requires p1_url")


@dataclass
class P1Result:
    items: List[Any] = field(default_factory=list)
    next_url: Optional[str] = None


@dataclass
class P2ParseResult:
    title: str
    author: str
    description: str
    p3s: List[Tuple[str, str]]
    next_url: Optional[str] = None


@dataclass
class P3ParseResult:
    title: str
    content: str
    next_url: Optional[str] = None


@dataclass
class P2Result:
    id: Any
    url: str
    title: str
    author: str
    description: str
    p3s: List[Tuple[str, str]]
    total_p3: int


@dataclass
class P3Result:
    p2_title: str
    id: int
    title: str
    url: str
    content: str


__all__ = [
    "Mode",
    "P1Result",
    "P2ParseResult",
    "P2Result",
    "P3ParseResult",
    "P3Result",
    "PcConfig",
]
