"""Synchronous, backend-neutral browser wrappers.

The wrappers deliberately expose ``source`` instead of hiding the underlying
library object. Common automation can use this module, while backend-specific
features remain available through ``source``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .backend import SyncBrowserBackend
from .types import BrowserConfig, BrowserCookie, Headers, NavigationResult

__all__ = ["Browser", "BrowserContext", "Page"]


class _CookieHeaderOwner:
    """The common cookie/header surface shared by browser, context and page."""

    @property
    def headers(self) -> Headers:
        raise NotImplementedError

    def set_headers(self, headers: Mapping[str, str]) -> None:
        raise NotImplementedError

    def update_headers(self, headers: Mapping[str, str]) -> None:
        merged = self.headers
        merged.update(headers)
        self.set_headers(merged)

    def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        raise NotImplementedError

    def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        raise NotImplementedError

    def clear_cookies(self) -> None:
        raise NotImplementedError


@dataclass(slots=True)
class Browser(_CookieHeaderOwner):
    """A synchronous browser wrapper with a default context.

    Use :meth:`launch` for a newly created browser or :meth:`from_source` to
    wrap a browser created by a backend library. ``source`` is always the raw
    browser object and can be used for library-specific operations.
    """

    source: Any
    backend: SyncBrowserBackend
    config: BrowserConfig = field(default_factory=BrowserConfig)
    _contexts: dict[int, "BrowserContext"] = field(default_factory=dict, init=False, repr=False)
    _default_context: "BrowserContext | None" = field(default=None, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    @classmethod
    def launch(
        cls,
        backend: SyncBrowserBackend,
        config: BrowserConfig | None = None,
    ) -> "Browser":
        """Launch a backend browser and create its default context."""
        resolved_config = config or BrowserConfig()
        browser = cls(backend.launch(resolved_config), backend, resolved_config)
        browser._default_context = browser.new_context(make_default=True)
        return browser

    @classmethod
    def playwright(cls, config: BrowserConfig | None = None) -> "Browser":
        """Launch the bundled synchronous Playwright backend."""
        from .backend import PlaywrightSyncBackend

        return cls.launch(PlaywrightSyncBackend(), config)

    @classmethod
    def from_source(
        cls,
        source: Any,
        backend: SyncBrowserBackend,
        config: BrowserConfig | None = None,
        *,
        create_default_context: bool = True,
    ) -> "Browser":
        """Wrap an already-created native browser object."""
        browser = cls(source, backend, config or BrowserConfig())
        if create_default_context:
            browser._default_context = browser.new_context(make_default=True)
        return browser

    @property
    def default_context(self) -> "BrowserContext":
        if self._default_context is None:
            self._default_context = self.new_context(make_default=True)
        return self._default_context

    @property
    def headers(self) -> Headers:
        return self.default_context.headers

    def set_headers(self, headers: Mapping[str, str]) -> None:
        self.default_context.set_headers(headers)

    def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        return self.default_context.cookies(urls)

    def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        self.default_context.set_cookies(cookies)

    def clear_cookies(self) -> None:
        self.default_context.clear_cookies()

    def new_context(
        self,
        *,
        headers: Mapping[str, str] | None = None,
        cookies: Sequence[BrowserCookie | Mapping[str, Any]] | None = None,
        make_default: bool = False,
        **options: Any,
    ) -> "BrowserContext":
        """Create and return a wrapped browser context."""
        context_headers = dict(headers or self.config.headers)
        source = self.backend.new_context(self.source, headers=context_headers, **options)
        context = self._wrap_context(source, context_headers)
        if cookies:
            context.set_cookies(cookies)
        if make_default or self._default_context is None:
            self._default_context = context
        return context

    @property
    def contexts(self) -> tuple["BrowserContext", ...]:
        return tuple(self._wrap_context(item) for item in self.backend.contexts(self.source))

    def new_page(self, **options: Any) -> "Page":
        """Create a page in the default context."""
        return self.default_context.new_page(**options)

    def close(self) -> None:
        if not self._closed:
            self.backend.close_browser(self.source)
            self._closed = True

    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def _wrap_context(
        self, source: Any, headers: Mapping[str, str] | None = None
    ) -> "BrowserContext":
        key = id(source)
        if key not in self._contexts:
            self._contexts[key] = BrowserContext(source, self, dict(headers or {}))
        return self._contexts[key]


@dataclass(slots=True)
class BrowserContext(_CookieHeaderOwner):
    """A synchronous context wrapper. ``source`` is the raw context object."""

    source: Any
    browser: Browser
    _headers: Headers = field(default_factory=dict, repr=False)
    _pages: dict[int, "Page"] = field(default_factory=dict, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def headers(self) -> Headers:
        return dict(self._headers)

    def set_headers(self, headers: Mapping[str, str]) -> None:
        normalized = {str(name): str(value) for name, value in headers.items()}
        self.browser.backend.set_headers(self.source, normalized)
        self._headers = normalized

    def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        raw_cookies = self.browser.backend.cookies(self.source, urls)
        return [BrowserCookie.from_source(cookie) for cookie in raw_cookies]

    def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        normalized = [BrowserCookie.from_source(cookie) for cookie in cookies]
        self.browser.backend.add_cookies(self.source, [cookie.to_source() for cookie in normalized])

    def clear_cookies(self) -> None:
        self.browser.backend.clear_cookies(self.source)

    def new_page(self, **options: Any) -> "Page":
        return self._wrap_page(self.browser.backend.new_page(self.source, **options))

    @property
    def pages(self) -> tuple["Page", ...]:
        return tuple(self._wrap_page(item) for item in self.browser.backend.pages(self.source))

    def close(self) -> None:
        if not self._closed:
            self.browser.backend.close_context(self.source)
            self._closed = True

    def _wrap_page(self, source: Any) -> "Page":
        key = id(source)
        if key not in self._pages:
            self._pages[key] = Page(source, self)
        return self._pages[key]


@dataclass(slots=True)
class Page(_CookieHeaderOwner):
    """A synchronous page wrapper. ``source`` is the raw page/tab object."""

    source: Any
    context: BrowserContext
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def browser(self) -> Browser:
        return self.context.browser

    @property
    def headers(self) -> Headers:
        return self.context.headers

    def set_headers(self, headers: Mapping[str, str]) -> None:
        self.context.set_headers(headers)

    def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        return self.context.cookies(urls)

    def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        self.context.set_cookies(cookies)

    def clear_cookies(self) -> None:
        self.context.clear_cookies()

    @property
    def url(self) -> str:
        return self.browser.backend.page_url(self.source)

    def title(self) -> str:
        return self.browser.backend.page_title(self.source)

    def content(self) -> str:
        return self.browser.backend.page_content(self.source)

    def goto(self, url: str, **options: Any) -> NavigationResult:
        response = self.browser.backend.goto(self.source, url, **options)
        return self.browser.backend.navigation_result(response, self.url)

    def reload(self, **options: Any) -> NavigationResult:
        response = self.browser.backend.reload(self.source, **options)
        return self.browser.backend.navigation_result(response, self.url)

    def evaluate(self, expression: str, arg: Any = None) -> Any:
        return self.browser.backend.evaluate(self.source, expression, arg)

    def close(self) -> None:
        if not self._closed:
            self.browser.backend.close_page(self.source)
            self._closed = True
