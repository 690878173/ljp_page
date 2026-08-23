"""Browser automation public base API.

Concrete backends remain in subpackages, for example ``brower.playwright``.
"""

from .base import (
    AsyncBrowser,
    AsyncBrowserContext,
    AsyncPage,
    BrowserCookie,
    CDPResponseBody,
    CDPSession,
    FetchResult,
    Headers,
    NavigationResult,
)

__all__ = [
    "AsyncBrowser",
    "AsyncBrowserContext",
    "AsyncPage",
    "BrowserCookie",
    "CDPResponseBody",
    "CDPSession",
    "FetchResult",
    "Headers",
    "NavigationResult",
]
