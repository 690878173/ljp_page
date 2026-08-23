"""Public browser automation API.

Application code imports browser automation exclusively from this package.
Backend modules remain implementation details under ``ljp_page._module``.
"""

from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import mapped_module_exports

_EXPORTS = {
    "AsyncBrowser": "ljp_page._module.request.brower.base",
    "AsyncBrowserContext": "ljp_page._module.request.brower.base",
    "AsyncPage": "ljp_page._module.request.brower.base",
    "Browser": "ljp_page._module.request.brower.base",
    "BrowserConfig": "ljp_page._module.request.brower.base",
    "BrowserContext": "ljp_page._module.request.brower.base",
    "BrowserCookie": "ljp_page._module.request.brower.base",
    "CDPDOM": "ljp_page._module.request.brower.base",
    "CDPResponseBody": "ljp_page._module.request.brower.base",
    "CDPSession": "ljp_page._module.request.brower.base",
    "CLOUDFLARE_TARGET": "ljp_page._module.request.brower.base",
    "ChallengePage": "ljp_page._module.request.brower.base",
    "ChallengeSolver": "ljp_page._module.request.brower.base",
    "ChallengeTarget": "ljp_page._module.request.brower.base",
    "CloudflareChallenge": "ljp_page._module.request.brower.base",
    "FetchError": "ljp_page._module.request.brower.playwright.request",
    "FetchRequest": "ljp_page._module.request.brower.playwright.request",
    "FetchResult": "ljp_page._module.request.brower.base",
    "Headers": "ljp_page._module.request.brower.base",
    "Ljp_Context": "ljp_page._module.request.brower.playwright.context",
    "Ljp_Page": "ljp_page._module.request.brower.playwright.page",
    "NavigationResult": "ljp_page._module.request.brower.base",
    "Page": "ljp_page._module.request.brower.base",
    "PageCDP": "ljp_page._module.request.brower.playwright.cdp",
    "Playwright": "ljp_page._module.request.brower.playwright.browser",
    "PlaywrightFingerprint": "ljp_page._module.request.brower.playwright.fingerprint",
    "PlaywrightSyncBackend": "ljp_page._module.request.brower.base",
    "BrowserLaunchConfig": "ljp_page._module.request.brower.playwright.config",
    "SyncBrowserBackend": "ljp_page._module.request.brower.base",
}

if TYPE_CHECKING:
    from ljp_page._module.request.brower.base import *  # noqa: F403
    from ljp_page._module.request.brower.playwright import *  # noqa: F403

__getattr__, __all__ = mapped_module_exports(_EXPORTS)
