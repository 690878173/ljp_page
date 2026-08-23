"""Adapter-neutral HTTP request and response models."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import cast

from ljp_page._core.exceptions import HTTPStatusException

from ..html import Html
from .types import BackendOptions, CookieMap, HeaderMap, JsonValue, QueryParams, RequestData

_JSON_UNSET = object()


@dataclass(frozen=True, slots=True)
class RequestArgs:
    """The complete, backend-independent description of one HTTP request."""

    method: str
    url: str
    headers: HeaderMap
    timeout: tuple[float, float]
    allow_redirects: bool
    stream: bool
    verify_ssl: bool
    params: QueryParams | None = None
    data: RequestData | None = None
    json_data: JsonValue | None = None
    cookies: CookieMap | None = None
    proxies: Mapping[str, str] | None = None
    proxy_url: str | None = None
    extra: BackendOptions = field(default_factory=dict)
    attempt: int = 0
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", self.method.upper())
        object.__setattr__(self, "headers", dict(self.headers))
        object.__setattr__(self, "cookies", dict(self.cookies) if self.cookies else None)
        object.__setattr__(self, "proxies", dict(self.proxies) if self.proxies else None)
        object.__setattr__(self, "extra", dict(self.extra))


@dataclass(slots=True)
class RequestsReponse:
    """The unified response model returned by every adapter and session."""

    request_args: RequestArgs
    status_code: int
    url: str
    headers: HeaderMap
    content: bytes
    encoding: str | None = None
    cookies: CookieMap = field(default_factory=dict)
    history: tuple[str, ...] = ()
    elapsed: float = 0.0
    retries: int = 0
    raw: object | None = field(default=None, repr=False)
    extra: dict[str, object] = field(default_factory=dict)

    _text_cache: str | None = field(default=None, init=False, repr=False)
    _json_cache: JsonValue | object = field(default=_JSON_UNSET, init=False, repr=False)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    @property
    def is_redirect(self) -> bool:
        return self.status_code in {301, 302, 303, 307, 308}

    @property
    def text(self) -> str:
        if self._text_cache is None:
            encoding = self.encoding or Html.extract_charset(self.content) or "utf-8"
            try:
                self._text_cache = self.content.decode(encoding.strip())
            except (LookupError, UnicodeDecodeError):
                self._text_cache = self.content.decode("utf-8", errors="replace")
        return self._text_cache

    def json(self, **kwargs: object) -> JsonValue:
        if kwargs:
            return cast(JsonValue, json.loads(self.text, **kwargs))
        if self._json_cache is _JSON_UNSET:
            self._json_cache = cast(JsonValue, json.loads(self.text))
        return cast(JsonValue, self._json_cache)

    def raise_for_status(self) -> None:
        if not self.ok:
            raise HTTPStatusException(
                f"HTTP {self.status_code}",
                url=self.url,
                context={"status_code": self.status_code, "url": self.url},
            )

    def __repr__(self) -> str:
        method = self.request_args.method
        return (
            f"RequestsReponse(status_code={self.status_code}, ok={self.ok}, "
            f"method={method!r}, url={self.url!r}, content_length={len(self.content)})"
        )

__all__ = [
    "RequestArgs",
    "RequestsReponse",
]
