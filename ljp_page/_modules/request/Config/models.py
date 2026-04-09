from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ljp_page._core.base.tools_func import _safe_value
from ljp_page._core.exceptions import LjpRequestException

_JSON_UNSET = object()


@dataclass
class SessionMetrics:
    """单个会话实例上的聚合指标。"""

    request_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    total_elapsed: float = 0.0


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
        return {
            "params": _safe_value(self.params),
            "data": _safe_value(self.data),
            "json": _safe_value(self.json_data),
        }


@dataclass
class LjpResponse:
    """统一响应对象，供同步与异步请求共享。"""

    status_code: int
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
                trace_id = self.request.trace_id if self.request else "-"
                method = self.request.method if self.request else "-"
                url = self.request.url if self.request else "-"
                raise LjpRequestException(
                    "响应 JSON 解析失败",
                    trace_id=trace_id,
                    method=method,
                    url=url,
                    category="parse",
                    status_code=self.status_code,
                    original_exception=exc,
                ) from exc
        return self._json_cache


__all__ = [
    "LjpRequestException",
    "LjpResponse",
    "RequestContext",
    "SessionMetrics",
]
