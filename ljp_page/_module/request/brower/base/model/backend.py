"""Backend contract and the synchronous Playwright implementation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .types import BrowserConfig, Headers, NavigationResult

if TYPE_CHECKING:
    from playwright.sync_api import Browser as PlaywrightBrowser

__all__ = ["PlaywrightSyncBackend", "SyncBrowserBackend"]


@runtime_checkable
class SyncBrowserBackend(Protocol):
    """Operations a synchronous backend must provide to use the wrappers."""

    def launch(self, config: BrowserConfig) -> Any: ...
    def close_browser(self, browser: Any) -> None: ...
    def contexts(self, browser: Any) -> Sequence[Any]: ...
    def new_context(self, browser: Any, *, headers: Headers, **options: Any) -> Any: ...
    def close_context(self, context: Any) -> None: ...
    def set_headers(self, context: Any, headers: Headers) -> None: ...
    def cookies(
        self, context: Any, urls: Sequence[str] | None = None
    ) -> Sequence[Mapping[str, Any]]: ...
    def add_cookies(self, context: Any, cookies: Sequence[Mapping[str, Any]]) -> None: ...
    def clear_cookies(self, context: Any) -> None: ...
    def pages(self, context: Any) -> Sequence[Any]: ...
    def new_page(self, context: Any, **options: Any) -> Any: ...
    def close_page(self, page: Any) -> None: ...
    def page_url(self, page: Any) -> str: ...
    def page_title(self, page: Any) -> str: ...
    def page_content(self, page: Any) -> str: ...
    def goto(self, page: Any, url: str, **options: Any) -> Any: ...
    def reload(self, page: Any, **options: Any) -> Any: ...
    def evaluate(self, page: Any, expression: str, arg: Any = None) -> Any: ...
    def navigation_result(self, response: Any, page_url: str) -> NavigationResult: ...


class PlaywrightSyncBackend:
    """Adapter for ``playwright.sync_api`` with lazy optional dependency loading."""

    def __init__(self) -> None:
        self._runtimes: dict[int, Any] = {}

    def launch(self, config: BrowserConfig) -> Any:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise ImportError(
                "Playwright is required for PlaywrightSyncBackend. "
                "Install it with: pip install ljp-page[automation]"
            ) from error

        runtime = sync_playwright().start()
        try:
            browser_launcher = getattr(runtime, config.browser_type)
        except AttributeError as error:
            runtime.stop()
            message = f"Unsupported Playwright browser type: {config.browser_type!r}"
            raise ValueError(message) from error

        launch_options = dict(config.launch_options)
        launch_options["headless"] = config.headless
        if config.channel is not None:
            launch_options["channel"] = config.channel
        if config.executable_path is not None:
            launch_options["executable_path"] = config.executable_path
        if config.args:
            launch_options["args"] = list(config.args)
        if config.slow_mo is not None:
            launch_options["slow_mo"] = config.slow_mo
        try:
            browser = browser_launcher.launch(**launch_options)
        except Exception:
            runtime.stop()
            raise
        self._runtimes[id(browser)] = runtime
        return browser

    def close_browser(self, browser: "PlaywrightBrowser") -> None:
        try:
            browser.close()
        finally:
            runtime = self._runtimes.pop(id(browser), None)
            if runtime is not None:
                runtime.stop()

    def contexts(self, browser: Any) -> Sequence[Any]:
        return browser.contexts

    def new_context(self, browser: Any, *, headers: Headers, **options: Any) -> Any:
        if headers:
            options["extra_http_headers"] = headers
        return browser.new_context(**options)

    def close_context(self, context: Any) -> None:
        context.close()

    def set_headers(self, context: Any, headers: Headers) -> None:
        context.set_extra_http_headers(headers)

    def cookies(
        self, context: Any, urls: Sequence[str] | None = None
    ) -> Sequence[Mapping[str, Any]]:
        return context.cookies(list(urls)) if urls else context.cookies()

    def add_cookies(self, context: Any, cookies: Sequence[Mapping[str, Any]]) -> None:
        context.add_cookies(list(cookies))

    def clear_cookies(self, context: Any) -> None:
        context.clear_cookies()

    def pages(self, context: Any) -> Sequence[Any]:
        return context.pages

    def new_page(self, context: Any, **options: Any) -> Any:
        if options:
            raise TypeError("Playwright page creation does not accept page options")
        return context.new_page()

    def close_page(self, page: Any) -> None:
        page.close()

    def page_url(self, page: Any) -> str:
        return page.url

    def page_title(self, page: Any) -> str:
        return page.title()

    def page_content(self, page: Any) -> str:
        return page.content()

    def goto(self, page: Any, url: str, **options: Any) -> Any:
        return page.goto(url, **options)

    def reload(self, page: Any, **options: Any) -> Any:
        return page.reload(**options)

    def evaluate(self, page: Any, expression: str, arg: Any = None) -> Any:
        return page.evaluate(expression) if arg is None else page.evaluate(expression, arg)

    def navigation_result(self, response: Any, page_url: str) -> NavigationResult:
        if response is None:
            return NavigationResult(url=page_url, status=None, headers={}, source=None)
        return NavigationResult(
            url=str(response.url),
            status=int(response.status),
            headers=_response_headers(response),
            source=response,
        )


def _response_headers(response: Any) -> Headers:
    try:
        raw_headers = response.all_headers()
    except AttributeError:
        raw_headers = response.headers
    return {str(name): str(value) for name, value in raw_headers.items()}
