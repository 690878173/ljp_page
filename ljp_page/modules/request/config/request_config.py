import re
import json
from dataclasses import dataclass, field
from typing import Any

from ljp_page.core.base.Ljp_exceptions import LjpBaseException
from ljp_page.core.base.tools_func import _safe_value
from ljp_page.config import ProxyConfig,TimeoutConfig,PoolConfig,LjpConfig,LogConfig,RetryConfig,RequestConfig

_JSON_UNSET = object()



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

    def safe_payload(self) -> dict[str, Any]:
        """返回可安全打印的请求负载。"""

        return {
            "params": _safe_value(self.params),
            "data": _safe_value(self.data),
            "json": _safe_value(self.json_data),
        }

class LjpResponse:
    """统一响应对象，供同步与异步请求共享。"""

    status_code: int
    headers: dict[str, str]
    encoding: str | None
    content: bytes = field(repr=False)
    elapsed: float
    retries: int
    request: RequestContext
    _text_cache: str | None = field(default=None, init=False, repr=False)
    _json_cache: Any = field(default=_JSON_UNSET, init=False, repr=False)

    def __repr__(self) -> str:
        return (
            "LjpResponse("
            f"status_code={self.status_code}, "
            f"ok={self.ok}, "
            f"elapsed={self.elapsed:.4f}, "
            f"retries={self.retries}, "
            f"method='{self.request.method}', "
            f"url='{self.request.url}', "
            f"content_length={len(self.content)}"
            ")"
        )

    @property
    def http_status(self) -> int:
        return self.status_code

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

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
        """从 HTML 的 meta 中提取字符集。"""

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
                raise LjpRequestException(
                    "响应 JSON 解析失败",
                    trace_id=self.request.trace_id,
                    method=self.request.method,
                    url=self.request.url,
                    category="parse",
                    status_code=self.status_code,
                    original_exception=exc,
                ) from exc
        return self._json_cache

class LjpRequestException(LjpBaseException):
    """带 trace_id 与分类字段的请求异常。"""

    def __init__(
        self,
        message: str,
        *,
        trace_id: str,
        method: str,
        url: str,
        category: str,
        retries: int = 0,
        elapsed: float | None = None,
        status_code: int | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        self.trace_id = trace_id
        self.method = method
        self.url = url
        self.category = category
        self.retries = retries
        self.elapsed = elapsed
        self.status_code = status_code
        self.original_exception = original_exception
        super().__init__(message, e=original_exception)

    def __str__(self) -> str:
        parts = [
            super().__str__(),
            f"trace_id={self.trace_id}",
            f"method={self.method}",
            f"url={self.url}",
            f"category={self.category}",
            f"retries={self.retries}",
        ]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.elapsed is not None:
            parts.append(f"elapsed={self.elapsed:.4f}s")
        return " | ".join(parts)







