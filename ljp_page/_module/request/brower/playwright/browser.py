"""Asynchronous Playwright browser implementation for the common browser API."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base.model import AsyncBrowser, BrowserCookie
from .config import BrowserLaunchConfig
from .context import Ljp_Context
from .page import Ljp_Page

__all__ = ["BrowserLaunchConfig", "Ljp_Context", "Ljp_Page", "Playwright"]


class Playwright(AsyncBrowser):
    """A lifecycle-safe asynchronous Playwright browser wrapper.

    ``source`` is the native Playwright ``Browser`` for normal launches and the
    native persistent ``BrowserContext`` for persistent launches. The runtime
    stays private; ``source`` is the only public raw-object access path.
    """

    def __init__(
        self,
        config: BrowserLaunchConfig | None = None,
        *,
        playwright: Any = None,
    ) -> None:
        self.config = config or BrowserLaunchConfig()
        self._runtime = playwright
        self.source: Any = None
        self._browser: Any = None
        self.context: Any = None
        self._contexts: dict[int, Any] = {}
        self._lock = asyncio.Lock()
        self._owns_runtime = playwright is None
        self._persistent = False
        self._closed = False
        self._ua: str | None = self.config.user_agent

    @property
    def started(self) -> bool:
        return self.context is not None and not self._closed

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def contexts(self) -> tuple[Ljp_Context, ...]:
        return tuple(self._contexts.values())

    @property
    def headers(self) -> dict[str, str]:
        return self.default_context.headers

    @property
    def default_context(self) -> "Ljp_Context":
        if self.context is None:
            raise RuntimeError("Browser has not started; call await start() first")
        return self.context

    async def start(self) -> "Playwright":
        """Start the native runtime once and create the default context."""
        if self.started:
            return self
        async with self._lock:
            if self.started:
                return self
            if self._runtime is None:
                from playwright.async_api import async_playwright

                self._runtime = await async_playwright().start()
                self._owns_runtime = True

            launcher = getattr(self._runtime, self.config.browser_type, None)
            if launcher is None:
                message = f"Unsupported Playwright browser type: {self.config.browser_type!r}"
                raise ValueError(message)

            context_options = self.config.to_context_dict()
            if self.config.user_data_dir:
                user_data_dir = Path(self.config.user_data_dir).resolve()
                user_data_dir.mkdir(parents=True, exist_ok=True)
                native_context = await launcher.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    **self.config.to_dict(),
                    **context_options,
                )
                self._browser = native_context.browser
                self.source = native_context
                self._persistent = True
            else:
                self._browser = await launcher.launch(**self.config.to_dict())
                native_context = await self._browser.new_context(**context_options)
                self.source = self._browser
                self._persistent = False

            self.context = self._wrap_context(native_context)
            if self.config.cookies:
                await self.context.set_cookies(self.config.cookies)
            self._closed = False
        return self

    async def ua(self) -> str:
        """Return the configured or browser-reported user agent."""
        if not self.started:
            raise RuntimeError("Browser has not started; call await start() first")
        if self._ua is None:
            page = await self.default_context.new_page()
            try:
                self._ua = await page.evaluate("navigator.userAgent")
            finally:
                await page.close()
        return self._ua

    async def set_headers(self, headers: Mapping[str, str]) -> None:
        await self.default_context.set_headers(headers)

    async def update_headers(self, headers: Mapping[str, str]) -> None:
        await self.default_context.update_headers(headers)

    async def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        return await self.default_context.cookies(urls)

    async def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        await self.default_context.set_cookies(cookies)

    async def clear_cookies(self) -> None:
        await self.default_context.clear_cookies()

    async def new_context(self, **options: Any) -> "Ljp_Context":
        """Create an isolated browser context.

        Persistent launches only have their launch context; Playwright does not
        expose ``Browser.new_context`` for that mode, so this method raises a
        clear error instead of returning an invalid object.
        """
        if not self.started:
            raise RuntimeError("Browser has not started; call await start() first")
        if self._persistent or self._browser is None:
            raise RuntimeError("Persistent contexts cannot create additional Playwright contexts")
        context_options = self.config.to_context_dict()
        default_headers = context_options.pop("extra_http_headers", None)
        headers = options.pop("headers", options.pop("extra_http_headers", default_headers))
        cookies = options.pop("cookies", None)
        context_options.update(options)
        native_context = await self._browser.new_context(**context_options)
        context = self._wrap_context(native_context, headers=headers)
        if cookies:
            await context.set_cookies(cookies)
        return context

    async def new_page(self, **options: Any) -> "Ljp_Page":
        return await self.default_context.new_page(**options)

    async def new_pages(self, count: int, **options: Any) -> list["Ljp_Page"]:
        if count < 0:
            raise ValueError("count must be >= 0")
        return [await self.new_page(**options) for _ in range(count)]

    async def new_browser(
        self,
        config: BrowserLaunchConfig | None = None,
        playwright: Any = None,
    ) -> "Playwright":
        """Create an unstarted sibling wrapper sharing a supplied runtime."""
        return Playwright(config=config, playwright=playwright or self._runtime)

    async def close(self) -> None:
        """Close contexts, browser and owned Playwright runtime exactly once."""
        if self._closed:
            return
        async with self._lock:
            if self._closed:
                return
            try:
                if self._persistent and self.context is not None:
                    await self.context.close()
                elif self._browser is not None:
                    await self._browser.close()
            finally:
                if self._runtime is not None and self._owns_runtime:
                    await self._runtime.stop()
                self.source = None
                self._browser = None
                self.context = None
                self._contexts.clear()
                self._runtime = None
                self._closed = True

    async def __aenter__(self) -> "Playwright":
        return await self.start()

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    def _wrap_context(
        self, source: Any, *, headers: Mapping[str, str] | None = None
    ) -> "Ljp_Context":
        from .context import Ljp_Context

        key = id(source)
        if key not in self._contexts:
            self._contexts[key] = Ljp_Context(source, self, headers=headers)
        return self._contexts[key]
