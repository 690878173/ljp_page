"""流水线配置模型。"""

from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator

from ljp_page._module.request.brower.playwright import BrowserLaunchConfig
from ljp_page._module.request.session import SessionConfig

from .enums import PipelineMode


class Config(BaseModel):
    """流水线全局配置。

    属性:
        base_url: 站点根地址。
        p1_url: P1 页面 URL 模板（支持 {} 占位）。
        p2_url: P2 详情页 URL 模板。
        p3_url: P3 内容页 URL 模板。
        save_path: 文件保存根目录。
        start_id / end_id: 自动生成 id_list 的起止范围。
        id_list: 显式指定 ID 列表，优先级高于 start_id/end_id。
        mode: 流水线运行模式。
        max_workers: P2 并发数。
        chapter_concurrency: 章节并发数。
        max_open_files: 最大同时打开文件数。
        directory_num: 目录分片数量。
        directory_mode: 目录分片模式。
        worker_startup_delay: Worker 启动延迟（秒）。
        queue_get_timeout: 队列取任务超时（秒）。
        session_config: aiohttp/curl-cffi 请求配置。
        browser_config: 验证浏览器配置；proxy 必须与 session_config.Proxy 一致。
        http_backend: ``aiohttp`` 或 ``curl_cffi``。
    """

    base_url: str = ""
    p1_url: str | None = None
    p2_url: str | None = None
    p3_url: str | None = None
    save_path: str = "res/"

    start_id: int = 1
    end_id: int = 5
    id_list: list[str] | None = None

    mode: PipelineMode = PipelineMode.MODE2

    max_workers: int = Field(5, ge=1)
    chapter_concurrency: int = Field(20, ge=1)
    max_open_files: int = Field(200, ge=1)
    directory_num: int = Field(100, ge=1)
    directory_mode: str = "mode1"
    worker_startup_delay: float = Field(1.0, ge=0)
    queue_get_timeout: float = Field(2.0, gt=0)
    session_close_timeout: float = Field(2.0, gt=0)

    session_config: SessionConfig = Field(default_factory=SessionConfig)
    browser_config: BrowserLaunchConfig = Field(default_factory=BrowserLaunchConfig)
    http_backend: Literal["aiohttp", "curl_cffi"] = "aiohttp"
    verify_timeout: float = Field(30.0, gt=0)
    verify_attempts: int = Field(3, ge=1, le=3)
    verify_poll_interval: float = Field(0.5, gt=0)
    image_dir: str = "res/images"

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def _generate_id_list(self) -> "Config":
        if self.id_list is None:
            if self.start_id > self.end_id:
                raise ValueError("start_id 不能大于 end_id")
            self.id_list = [str(i) for i in range(self.start_id, self.end_id + 1)]
        else:
            self.id_list = list(self.id_list)
        return self

    @staticmethod
    def is_absolute_url(value: Any) -> bool:
        return urlparse(str(value or "")).scheme in {"http", "https"}

    @classmethod
    def format_url(cls, template: str | None, value: Any) -> str:
        raw_value = getattr(value, "url", value)
        if cls.is_absolute_url(raw_value):
            return str(raw_value)
        if template:
            return str(template).format(raw_value)
        return str(raw_value or "")

    def format_p1_url(self, value: Any) -> str:
        return self.format_url(self.p1_url, value)

    def format_p2_url(self, value: Any) -> str:
        return self.format_url(self.p2_url, value)

    def format_p3_url(self, value: Any) -> str:
        return self.format_url(self.p3_url, value)
