import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence

import json



from ..._ljp_coro.exceptions import LjpBaseException



BeforeRequestHook = Callable[[Any, "RequestMetadata"], Any]
AfterResponseHook = Callable[[Any, "LjpResponse"], Any]
ErrorHook = Callable[[Any, "LjpRequestException"], Any]
HookValue = Any
_JSON_UNSET = object()

@dataclass
class SessionMetrics:
    """Aggregated request metrics for one custom session instance."""

    request_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    total_elapsed: float = 0.0

@dataclass(frozen=True)
class RequestMetadata:
    """Serializable request metadata for logging and troubleshooting."""

    trace_id: str
    method: str
    url: str
    headers: dict[str, str]
    cookies: dict[str, str]
    timeout: tuple[float, float]
    allow_redirects: bool
    stream: bool
    verify_ssl: bool
    proxy: str | None
    payload: dict[str, Any]

@dataclass
class LjpResponse:
    """Uniform response wrapper returned by sync and async sessions."""

    status_code: int
    headers: dict[str, str]
    encoding: str | None
    content: bytes
    elapsed: float
    retries: int
    request: RequestMetadata
    _text_cache: str | None = field(default=None, init=False, repr=False)
    _json_cache: Any = field(default=_JSON_UNSET, init=False, repr=False)

    @property
    def http_status(self) -> int:
        """Alias for status_code."""

        return self.status_code

    @property
    def ok(self) -> bool:
        """Return True for HTTP 2xx and 3xx responses."""

        return 200 <= self.status_code < 400

    @property
    def binary(self) -> bytes:
        """Return raw response bytes."""

        return self.content

    @property
    def text(self) -> str:
        """
        解码逻辑完全和 requests 对齐：
        1. 先用传入的 encoding
        2. 没有 → 从 HTML meta 标签里找 charset
        3. 没有 → 用 utf-8
        4. 失败 → 容错解码
        """
        if self._text_cache is not None:
            return self._text_cache

        # 1. 使用你传递过来的编码（优先）
        encoding = self.encoding

        # 2. 如果没有编码，从 HTML meta 标签自动提取（和 requests 一样！）
        if not encoding:
            encoding = self._extract_charset_from_html()

        # 3. 兜底默认编码
        encoding = encoding or "utf-8"

        try:
            self._text_cache = self.content.decode(encoding.strip())
        except (UnicodeDecodeError, LookupError):
            # 最后兜底：强制 utf-8 容错解码
            self._text_cache = self.content.decode("utf-8", errors="replace")

        return self._text_cache

    # ====================== 🔥 新增：从HTML提取编码 ======================
    def _extract_charset_from_html(self) -> str | None:
        """从 HTML 中提取 charset，完全模拟 requests 行为"""
        try:
            # 只读取前面 1024 字节，避免大文件
            html = self.content[:1024].decode("ascii", errors="ignore")
            match = re.search(r'charset\s*=\s*["\']?([^"\'\s>]+)', html, re.I)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        return None

    def json(self) -> Any:
        """Parse JSON content."""

        if self._json_cache is _JSON_UNSET:
            try:
                self._json_cache = json.loads(self.text)
            except json.JSONDecodeError as exc:
                raise LjpRequestException(
                    "Failed to parse response JSON",
                    trace_id=self.request.trace_id,
                    method=self.request.method,
                    url=self.request.url,
                    status_code=self.status_code,
                    category="parse",
                    original_exception=exc,
                ) from exc
        return self._json_cache

class LjpRequestException(LjpBaseException):
    """Custom request exception with trace_id metadata."""

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
        details = [super().__str__(), f"trace_id={self.trace_id}"]
        details.append(f"method={self.method}")
        details.append(f"url={self.url}")
        details.append(f"category={self.category}")
        details.append(f"retries={self.retries}")
        if self.status_code is not None:
            details.append(f"status={self.status_code}")
        if self.elapsed is not None:
            details.append(f"elapsed={self.elapsed:.4f}s")
        return " | ".join(details)

@dataclass(frozen=True)
class PreparedRequest:
    """Normalized request options used by both runtimes."""

    metadata: RequestMetadata
    request_kwargs: dict[str, Any]
    proxies: dict[str, str] | None
    proxy_url: str | None

@dataclass
class SessionHooks:
    """Lifecycle callbacks shared by sync and async sessions."""

    before_request: Sequence[BeforeRequestHook] = field(default_factory=tuple)
    after_response: Sequence[AfterResponseHook] = field(default_factory=tuple)
    on_error: Sequence[ErrorHook] = field(default_factory=tuple)

    @classmethod
    def from_value(cls, value: HookValue) -> "SessionHooks":
        """Normalize hook configuration."""

        if value is None:
            return cls()
        if isinstance(value, cls):
            return cls(
                before_request=tuple(value.before_request),
                after_response=tuple(value.after_response),
                on_error=tuple(value.on_error),
            )
        mapping = dict(value)
        return cls(
            before_request=tuple(mapping.get("before_request", ()) or ()),
            after_response=tuple(mapping.get("after_response", ()) or ()),
            on_error=tuple(mapping.get("on_error", ()) or ()),
        )
