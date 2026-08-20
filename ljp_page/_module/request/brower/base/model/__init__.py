"""Synchronous browser abstractions and optional backend adapters."""

from .backend import PlaywrightSyncBackend, SyncBrowserBackend
from .browser import Browser, BrowserContext, Page
from .types import BrowserConfig, BrowserCookie, Headers, NavigationResult

__all__ = [
    "Browser",
    "BrowserConfig",
    "BrowserContext",
    "BrowserCookie",
    "Headers",
    "NavigationResult",
    "Page",
    "PlaywrightSyncBackend",
    "SyncBrowserBackend",
]
