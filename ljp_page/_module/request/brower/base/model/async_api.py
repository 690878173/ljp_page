"""Backend-independent asynchronous browser contracts and CDP wrapper."""

from __future__ import annotations

import abc
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Callable

from .types import BrowserCookie, FetchResult, Headers, NavigationResult

__all__ = ["AsyncBrowser", "AsyncBrowserContext", "AsyncPage", "CDPSession"]


class CDPSession:
    """A small typed wrapper around a native CDP session.

    Commands created by ``base.commands`` can be passed directly. The wrapper
    normalizes enum values recursively and leaves the native session accessible
    through :attr:`source` for library-specific APIs.
    """

    def __init__(self, source: Any) -> None:
        self.source = source
        self._closed = False

    async def send(
        self,
        method: str | Mapping[str, Any] | Enum | None = None,
        params: Mapping[str, Any] | None = None,
        **command: Any,
    ) -> dict[str, Any]:
        if isinstance(method, Mapping):
            command = {**method, **command}
            method = command.pop("method", None)
            params = command.pop("params", params)
        elif command:
            method = command.pop("method", method)
            params = command.pop("params", params)
        command.pop("id", None)
        command.pop("sessionId", None)
        if method is None:
            raise ValueError("CDP method cannot be empty")
        if command:
            raise TypeError(f"Unknown CDP command fields: {', '.join(command)}")

        method_name = _normalize_cdp_value(method)
        if not isinstance(method_name, str):
            raise TypeError("CDP method must resolve to str")
        result = await self.source.send(method_name, _normalize_cdp_value(dict(params or {})))
        return dict(result or {})

    async def detach(self) -> None:
        if not self._closed:
            detach = getattr(self.source, "detach", None)
            if detach is not None:
                await detach()
            self._closed = True

    async def close(self) -> None:
        await self.detach()

    @property
    def closed(self) -> bool:
        return self._closed

    def on(self, event: str, handler: Callable[[Any], Any]) -> Callable[[], None]:
        """Subscribe to a native CDP event and return an unsubscribe callback."""
        subscribe = getattr(self.source, "on", None)
        if not callable(subscribe):
            raise TypeError("The native CDP session does not support event subscriptions")
        subscribe(event, handler)

        def unsubscribe() -> None:
            remove = getattr(self.source, "remove_listener", None) or getattr(
                self.source, "off", None
            )
            if callable(remove):
                remove(event, handler)

        return unsubscribe


class AsyncBrowser(abc.ABC):
    """Common asynchronous browser contract implemented by backend adapters."""

    source: Any

    @abc.abstractmethod
    async def start(self) -> "AsyncBrowser": ...

    @abc.abstractmethod
    async def new_context(self, **options: Any) -> "AsyncBrowserContext": ...

    @abc.abstractmethod
    async def new_page(self, **options: Any) -> "AsyncPage": ...

    @abc.abstractmethod
    async def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]: ...

    @abc.abstractmethod
    async def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None: ...

    @abc.abstractmethod
    async def close(self) -> None: ...


class AsyncBrowserContext(abc.ABC):
    """Common asynchronous browser-context contract."""

    source: Any
    browser: AsyncBrowser

    @property
    @abc.abstractmethod
    def headers(self) -> Headers: ...

    @abc.abstractmethod
    async def set_headers(self, headers: Mapping[str, str]) -> None: ...

    async def update_headers(self, headers: Mapping[str, str]) -> None:
        merged = self.headers
        merged.update(headers)
        await self.set_headers(merged)

    @abc.abstractmethod
    async def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]: ...

    @abc.abstractmethod
    async def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None: ...

    @abc.abstractmethod
    async def clear_cookies(self) -> None: ...

    @abc.abstractmethod
    async def new_page(self, **options: Any) -> "AsyncPage": ...

    @abc.abstractmethod
    async def close(self) -> None: ...


class AsyncPage(abc.ABC):
    """Common asynchronous page contract with browser-session fetch support."""

    source: Any
    context: AsyncBrowserContext

    @property
    @abc.abstractmethod
    def url(self) -> str: ...

    @abc.abstractmethod
    async def title(self) -> str: ...

    @abc.abstractmethod
    async def content(self) -> str: ...

    @abc.abstractmethod
    async def goto(self, url: str, **options: Any) -> NavigationResult: ...

    @abc.abstractmethod
    async def reload(self, **options: Any) -> NavigationResult: ...

    @abc.abstractmethod
    async def evaluate(self, expression: str, arg: Any = None) -> Any: ...

    @abc.abstractmethod
    async def fetch_request(self, method: str, url: str, **options: Any) -> FetchResult: ...

    @abc.abstractmethod
    async def get_cdp_session(self, target: Any = None) -> CDPSession: ...

    @abc.abstractmethod
    async def close(self) -> None: ...


def _normalize_cdp_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _normalize_cdp_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_normalize_cdp_value(item) for item in value]
    if isinstance(value, list):
        return [_normalize_cdp_value(item) for item in value]
    return value
