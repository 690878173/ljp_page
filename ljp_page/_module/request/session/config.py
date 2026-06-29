import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from ljp_page._core.utils.config import TimeoutConfig, SessionPoolConfig, ProxyConfig
from ljp_page._core.utils.retry import RetryConfig

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
)
_JSON_UNSET = object()

@dataclass
class RequestConfig:
    """请求行为配置。"""

    base_url: str = ""
    verify_ssl: bool = True
    allow_redirects: bool = True
    stream: bool = False
    delay: float = 0.0
    trust_env: bool = True
    headers: dict[str, str] = field(
        default_factory=lambda: {"User-Agent": DEFAULT_USER_AGENT}
    )
    cookies: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.delay = max(0.0, self.delay)

    def update_headers(self,headers):
        self.headers.update(headers)

    def update_cookies(self, cookies):
        self.cookies.update(cookies)

@dataclass
class LjpConfig:
    request: RequestConfig = field(default_factory=RequestConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    sessionpool: SessionPoolConfig = field(default_factory=SessionPoolConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    log: Any | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestContext:
    """请求上下文，供中间件和适配器共享。"""

    trace_id: str
    method: str
    url: str
    headers: dict[str, str]
    cookies: dict[str, str]
    timeout: tuple[float, float]
    allow_redirects: bool
    stream: bool
    verify_ssl: bool
    proxy_url: str | None
    proxies: dict[str, str] | None
    params: Any = None
    data: Any = None
    json_data: Any = None
    extra: dict[str, Any] = field(default_factory=dict)
    attempt: int = 0

    @classmethod
    def resolve(cls,**request_kwargs) -> tuple[
        dict[Any, Any] | Any, dict[Any, Any] | Any, Any, Any, Any, Any, Any, Any, Any]:
        kw = dict(request_kwargs)
        headers = kw.pop("headers", None) or {}
        cookies = kw.pop("cookies", None) or {}
        timeout = kw.pop("timeout", None)
        proxy = kw.pop("proxy", None)
        proxies = kw.pop("proxies", None)
        params = kw.pop("params", None)
        data = kw.pop("data", None)
        json_data = kw.pop("json_data", None)
        trace_id = kw.pop("trace_id", uuid.uuid4().hex)
        return headers,cookies,timeout,proxy,proxies,params,data,json_data,trace_id


@dataclass(frozen=True)
class AdapterResponse:
    """适配器统一响应结构。"""

    status_code: int
    headers: dict[str, str]
    content: bytes
    encoding: str | None
    cookies: dict[str, str]

@dataclass
class LjpResponse:
    """统一响应对象，供同步与异步请求共享。"""

    status: int
    headers: dict[str, str]
    encoding: str | None
    content: bytes = field(repr=False)
    elapsed: float = 0.0
    retries: int = 0
    request: RequestContext | None = None
    _text_cache: str | None = field(default=None, init=False, repr=False)
    _json_cache: Any = field(default=_JSON_UNSET, init=False, repr=False)

    def __repr__(self) -> str:
        req = self.request
        method = req.method if req else "-"
        url = req.url if req else "-"
        return (
            "LjpResponse("
            f"status_code={self.status_code}, "
            f"ok={self.ok}, "
            f"elapsed={self.elapsed:.4f}, "
            f"retries={self.retries}, "
            f"method='{method}', "
            f"url='{url}', "
            f"content_length={len(self.content)}"
            ")"
        )

    @property
    def status_code(self) -> int:
        return self.status

    @property
    def http_status(self) -> int:
        return self.status

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 400

    @property
    def binary(self) -> bytes:
        return self.content

    @property
    def text(self) -> str:
        if self._text_cache is not None:
            return self._text_cache

        encoding = self.encoding or self._extract_charset_from_html() or "utf-8"
        try:
            self._text_cache = self.content.decode(encoding.strip())
        except (UnicodeDecodeError, LookupError):
            self._text_cache = self.content.decode("utf-8", errors="replace")
        return self._text_cache

    def _extract_charset_from_html(self) -> str | None:
        try:
            html = self.content[:1024].decode("ascii", errors="ignore")
            match = re.search(r'charset\s*=\s*["\']?([^"\'\s>]+)', html, re.I)
            if match:
                return match.group(1).strip()
        except Exception:
            return None
        return None

    def json(self) -> Any:
        if self._json_cache is _JSON_UNSET:
            try:
                self._json_cache = json.loads(self.text)
            except json.JSONDecodeError as exc:
                raise Exception(
                    "响应 JSON 解析失败",
                ) from exc
        return self._json_cache


__all__ = [
    "RequestConfig",
    "LjpConfig",
    "RequestContext",
    "AdapterResponse",
    "LjpResponse",
    "SessionPoolConfig",
    "RetryConfig",
]
