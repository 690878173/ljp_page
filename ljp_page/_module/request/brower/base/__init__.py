"""Backend-neutral browser contracts, values and typed CDP command factories.

This package intentionally does not import a browser backend. Concrete
implementations such as ``brower.playwright`` depend on this package, never
the reverse.
"""

from .fingerprint import (
    CDPDOM,
    CLOUDFLARE_TARGET,
    ChallengePage,
    ChallengeSolver,
    ChallengeTarget,
    CloudflareChallenge,
)
from .model import (
    AsyncBrowser,
    AsyncBrowserContext,
    AsyncPage,
    Browser,
    BrowserConfig,
    BrowserContext,
    BrowserCookie,
    CDPResponseBody,
    CDPSession,
    FetchResult,
    Headers,
    NavigationResult,
    Page,
    PlaywrightSyncBackend,
    SyncBrowserBackend,
)

__all__ = [
    "AsyncBrowser",
    "AsyncBrowserContext",
    "AsyncPage",
    "Browser",
    "BrowserConfig",
    "BrowserContext",
    "BrowserCookie",
    "CDPDOM",
    "CDPResponseBody",
    "CDPSession",
    "CLOUDFLARE_TARGET",
    "ChallengePage",
    "ChallengeSolver",
    "ChallengeTarget",
    "CloudflareChallenge",
    "FetchResult",
    "Headers",
    "NavigationResult",
    "Page",
    "PlaywrightSyncBackend",
    "SyncBrowserBackend",
]
