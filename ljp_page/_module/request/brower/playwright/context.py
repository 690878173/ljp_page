"""Asynchronous Playwright browser-context wrapper."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ..base.model import AsyncBrowserContext, BrowserCookie, CDPSession, Headers
from .script import Script

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext

    from .browser import Playwright
    from .page import Ljp_Page

__all__ = ["Ljp_Context"]


class Ljp_Context(AsyncBrowserContext):  # noqa: N801
    """Backend-neutral context API backed by a native Playwright context."""

    def __init__(
        self,
        source: "BrowserContext",
        browser: "Playwright",
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.source = source
        self.browser = browser
        self._headers: Headers = dict(headers or browser.config.extra_http_headers or {})
        self._pages: dict[int, "Ljp_Page"] = {}
        self._init_lock = asyncio.Lock()
        self._started = False
        self._closed = False

    @property
    def headers(self) -> Headers:
        return dict(self._headers)

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def pages(self) -> tuple["Ljp_Page", ...]:
        return tuple(self._wrap_page(page) for page in self.source.pages)

    async def _ensure_started(self) -> None:
        if self._started:
            return
        async with self._init_lock:
            if self._started:
                return
            config = self.browser.config
            if config.init_script:
                await self.source.add_init_script(config.init_script)
            if config.use_stealth_script:
                await self.source.add_init_script(Script.FULL)
            if self._headers:
                await self.source.set_extra_http_headers(self._headers)
            self._started = True

    async def set_headers(self, headers: Mapping[str, str]) -> None:
        normalized = {str(name): str(value) for name, value in headers.items()}
        await self.source.set_extra_http_headers(normalized)
        self._headers = normalized

    async def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        raw_cookies = await (self.source.cookies(list(urls)) if urls else self.source.cookies())
        return [BrowserCookie.from_source(cookie) for cookie in raw_cookies]

    async def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        normalized = [BrowserCookie.from_source(cookie).to_source() for cookie in cookies]
        if normalized:
            await self.source.add_cookies(normalized)

    async def clear_cookies(self) -> None:
        await self.source.clear_cookies()

    async def new_page(self, **options: Any) -> "Ljp_Page":
        """Create a page, optionally navigate it via the ``url`` keyword."""
        if self._closed:
            raise RuntimeError("Browser context is closed")
        await self._ensure_started()
        url = options.pop("url", None)
        if options:
            names = ", ".join(options)
            raise TypeError(f"Playwright context.new_page does not accept: {names}")
        page = self._wrap_page(await self.source.new_page())
        if url is not None:
            await page.goto(str(url))
        return page

    async def new_cdp_session(self, page: "Ljp_Page | Any") -> CDPSession:
        target = getattr(page, "source", page)
        return CDPSession(await self.source.new_cdp_session(target))

    async def close(self) -> None:
        if not self._closed:
            await self.source.close()
            self._closed = True

    def _wrap_page(self, source: Any) -> "Ljp_Page":
        from .page import Ljp_Page

        key = id(source)
        if key not in self._pages:
            self._pages[key] = Ljp_Page(source, self)
        return self._pages[key]
