"""请求/响应数据模型。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import uuid as _uuid

from ..html import Html

_JSON_UNSET = object()

_REQUEST_KEYS = frozenset({
    "headers", "cookies", "timeout", "proxy", "proxies",
    "params", "data", "json_data", "trace_id",
    "allow_redirects", "stream", "verify_ssl",
})


def split_kwargs(kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """从 **kwargs 分离已知请求参数，返回 (known, passthrough)。"""
    known: dict[str, Any] = {}
    for key in _REQUEST_KEYS:
        if key in kwargs:
            known[key] = kwargs.pop(key)
    return known, kwargs


@dataclass(frozen=True)
class AdapterResult:
    """HTTP 适配器返回的原始响应数据。"""
    status_code: int
    headers: dict[str, str]
    content: bytes
    encoding: str | None
    cookies: dict[str, str]


@dataclass
class RequestContext:
    """单次请求的完整快照。"""
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
    trace_id: str = None
    extra: dict[str, Any] = field(default_factory=dict)
    attempt: int = 0

    def __post_init__(self):
        self.trace_id = _uuid.uuid4().hex
        self.method = self.method.upper()


@dataclass
class LjpResponse:
    """统一响应对象，同步/异步共享。"""
    status_code: int
    headers: dict[str, str]
    encoding: str | None
    content: bytes = field(repr=False)
    elapsed: float = 0.0
    retries: int = 0
    request: RequestContext | None = None

    _text_cache: str | None = field(default=None, init=False, repr=False)
    _json_cache: Any = field(default=_JSON_UNSET, init=False, repr=False)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    @property
    def text(self) -> str:
        if self._text_cache is not None:
            return self._text_cache
        encoding = self.encoding or Html.extract_charset(self.content) or "utf-8"
        try:
            self._text_cache = self.content.decode(encoding.strip())
        except (UnicodeDecodeError, LookupError):
            self._text_cache = self.content.decode("utf-8", errors="replace")
        return self._text_cache

    def json(self) -> Any:
        if self._json_cache is _JSON_UNSET:
            try:
                self._json_cache = json.loads(self.text)
            except json.JSONDecodeError as exc:
                raise ValueError("响应 JSON 解析失败") from exc
        return self._json_cache

    def __repr__(self) -> str:
        req = self.request
        method = req.method if req else "-"
        url = req.url if req else "-"
        return (
            f"LjpResponse(status_code={self.status_code}, ok={self.ok}, "
            f"elapsed={self.elapsed:.4f}, retries={self.retries}, "
            f"method='{method}', url='{url}', content_length={len(self.content)})"
        )


__all__ = [
    "split_kwargs",
    "AdapterResult",
    "RequestContext",
    "LjpResponse",
]
