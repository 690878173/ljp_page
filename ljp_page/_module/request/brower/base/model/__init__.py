"""Synchronous browser abstractions and optional backend adapters."""

from .async_api import AsyncBrowser, AsyncBrowserContext, AsyncPage, CDPSession
from .backend import PlaywrightSyncBackend, SyncBrowserBackend
from .browser import Browser, BrowserContext, Page
from .types import (
    BrowserConfig,
    BrowserCookie,
    CDPResponseBody,
    FetchResult,
    Headers,
    NavigationResult,
)

__all__ = [
    "Browser",
    "AsyncBrowser",
    "AsyncBrowserContext",
    "AsyncPage",
    "BrowserConfig",
    "BrowserContext",
    "BrowserCookie",
    "CDPResponseBody",
    "CDPSession",
    "FetchResult",
    "Headers",
    "NavigationResult",
    "Page",
    "PlaywrightSyncBackend",
    "SyncBrowserBackend",
]
