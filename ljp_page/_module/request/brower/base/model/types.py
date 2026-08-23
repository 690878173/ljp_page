"""Public value types used by the synchronous browser API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeAlias

Headers: TypeAlias = dict[str, str]

__all__ = [
    "BrowserConfig",
    "BrowserCookie",
    "CDPResponseBody",
    "FetchResult",
    "Headers",
    "NavigationResult",
]


@dataclass(frozen=True, slots=True)
class BrowserConfig:
    """Common launch settings understood by the bundled Playwright adapter."""

    headless: bool = True
    browser_type: str = "chromium"
    channel: str | None = None
    executable_path: str | None = None
    args: tuple[str, ...] = ()
    slow_mo: float | None = None
    headers: Headers = field(default_factory=dict)
    launch_options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BrowserCookie:
    """Library-independent browser cookie with the original item in ``source``."""

    name: str
    value: str
    url: str | None = None
    domain: str | None = None
    path: str | None = None
    expires: float | None = None
    http_only: bool | None = None
    secure: bool | None = None
    same_site: str | None = None
    source: Any = field(default=None, compare=False, repr=False)

    @classmethod
    def from_source(cls, value: "BrowserCookie | Mapping[str, Any]") -> "BrowserCookie":
        if isinstance(value, cls):
            return value
        return cls(
            name=str(value["name"]),
            value=str(value["value"]),
            url=_optional_str(value.get("url")),
            domain=_optional_str(value.get("domain")),
            path=_optional_str(value.get("path")),
            expires=_optional_float(value.get("expires", value.get("expiry"))),
            http_only=_optional_bool(value.get("httpOnly", value.get("http_only"))),
            secure=_optional_bool(value.get("secure")),
            same_site=_optional_str(value.get("sameSite", value.get("same_site"))),
            source=value,
        )

    def to_source(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name, "value": self.value}
        for source_name, value in (
            ("url", self.url),
            ("domain", self.domain),
            ("path", self.path),
            ("expires", self.expires),
            ("httpOnly", self.http_only),
            ("secure", self.secure),
            ("sameSite", self.same_site),
        ):
            if value is not None:
                result[source_name] = value
        return result


@dataclass(frozen=True, slots=True)
class NavigationResult:
    """The normalized result of :meth:`Page.goto` or :meth:`Page.reload`."""

    url: str
    status: int | None
    headers: Headers
    source: Any = field(default=None, compare=False, repr=False)

    @property
    def ok(self) -> bool | None:
        """Whether an HTTP response was successful; ``None`` when absent."""
        return None if self.status is None else 200 <= self.status < 400


@dataclass(frozen=True, slots=True)
class FetchResult:
    """A typed result produced by a request executed in a browser page.

    ``source`` retains the JSON-like value returned by the underlying browser
    evaluation. ``content`` is always bytes, so callers need not compensate for
    the JavaScript ``number[]`` representation of an ``ArrayBuffer``.
    """

    url: str
    status: int
    headers: Headers
    content: bytes = field(repr=False)
    cookies: str = ""
    source: Any = field(default=None, compare=False, repr=False)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 400

    @property
    def text(self) -> str:
        content_type = next(
            (value for name, value in self.headers.items() if name.lower() == "content-type"),
            "",
        )
        charset = _charset_from_content_type(content_type)
        return self.content.decode(charset or "utf-8", errors="replace")

    @property
    def encoding(self) -> str | None:
        content_type = next(
            (value for name, value in self.headers.items() if name.lower() == "content-type"),
            "",
        )
        return _charset_from_content_type(content_type)

    def json(self) -> Any:
        import json

        return json.loads(self.text)

    def raise_for_status(self) -> "FetchResult":
        if not self.ok:
            raise RuntimeError(f"Browser fetch failed with HTTP {self.status}: {self.url}")
        return self


@dataclass(frozen=True, slots=True)
class CDPResponseBody:
    """Decoded response body returned by ``Network.getResponseBody``."""

    request_id: str
    content: bytes = field(repr=False)
    base64_encoded: bool
    source: Any = field(default=None, compare=False, repr=False)

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_bool(value: Any) -> bool | None:
    return None if value is None else bool(value)


def _charset_from_content_type(content_type: str) -> str | None:
    for item in content_type.split(";")[1:]:
        key, separator, value = item.strip().partition("=")
        if separator and key.lower() == "charset":
            return value.strip('"')
    return None
