"""High-level Chrome DevTools Protocol helpers for a Playwright page."""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal

from ..base.model import BrowserCookie, CDPResponseBody, CDPSession

if TYPE_CHECKING:
    from .page import Ljp_Page

__all__ = ["PageCDP"]


class PageCDP:
    """Structured CDP operations bound to one :class:`Ljp_Page`.

    The object does not hide raw protocol access: :meth:`session` returns the
    common :class:`~..base.model.CDPSession`, whose ``source`` is the native
    Playwright session. Methods here cover stable, frequently used workflows
    and leave uncommon commands available through :meth:`send`.
    """

    def __init__(self, page: "Ljp_Page") -> None:
        self.page = page

    async def session(self) -> CDPSession:
        return await self.page.get_cdp_session()

    async def send(
        self,
        method: str | Mapping[str, Any],
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await (await self.session()).send(method, params)

    async def enable(
        self,
        *,
        dom: bool = False,
        network: bool = False,
        page: bool = False,
        runtime: bool = False,
    ) -> None:
        """Enable only the CDP domains needed by the current workflow."""
        commands: list[str] = []
        if dom:
            commands.append("DOM.enable")
        if network:
            commands.append("Network.enable")
        if page:
            commands.append("Page.enable")
        if runtime:
            commands.append("Runtime.enable")
        for command in commands:
            await self.send(command)

    async def evaluate(self, expression: str, **options: Any) -> dict[str, Any]:
        options.setdefault("returnByValue", True)
        options.setdefault("awaitPromise", True)
        return await self.send("Runtime.evaluate", {"expression": expression, **options})

    async def document(self, *, depth: int = -1, pierce: bool = True) -> dict[str, Any]:
        return await self.send("DOM.getDocument", {"depth": depth, "pierce": pierce})

    async def query_selector(self, node_id: int, selector: str) -> int | None:
        result = await self.send("DOM.querySelector", {"nodeId": node_id, "selector": selector})
        node_id = result.get("nodeId")
        return int(node_id) if node_id else None

    async def outer_html(self, *, node_id: int | None = None) -> str:
        if node_id is None:
            document = await self.document(depth=0)
            node_id = int(document["root"]["nodeId"])
        result = await self.send("DOM.getOuterHTML", {"nodeId": node_id})
        return str(result["outerHTML"])

    async def layout_metrics(self) -> dict[str, Any]:
        return await self.send("Page.getLayoutMetrics")

    async def navigation_history(self) -> dict[str, Any]:
        return await self.send("Page.getNavigationHistory")

    async def capture_screenshot(
        self,
        *,
        format: Literal["png", "jpeg", "webp"] = "png",
        quality: int | None = None,
        capture_beyond_viewport: bool = True,
    ) -> bytes:
        params: dict[str, Any] = {
            "format": format,
            "captureBeyondViewport": capture_beyond_viewport,
        }
        if quality is not None:
            params["quality"] = quality
        result = await self.send("Page.captureScreenshot", params)
        return base64.b64decode(result["data"])

    async def capture_snapshot(self, *, format: str = "mhtml") -> str:
        result = await self.send("Page.captureSnapshot", {"format": format})
        return str(result["data"])

    async def print_to_pdf(self, **options: Any) -> bytes:
        result = await self.send("Page.printToPDF", options)
        return base64.b64decode(result["data"])

    async def set_bypass_csp(self, enabled: bool = True) -> dict[str, Any]:
        return await self.send("Page.setBypassCSP", {"enabled": enabled})

    async def set_user_agent(self, user_agent: str, **options: Any) -> dict[str, Any]:
        return await self.send(
            "Emulation.setUserAgentOverride", {"userAgent": user_agent, **options}
        )

    async def set_extra_headers(self, headers: Mapping[str, str]) -> dict[str, Any]:
        normalized = {str(name): str(value) for name, value in headers.items()}
        return await self.send("Network.setExtraHTTPHeaders", {"headers": normalized})

    async def set_cache_disabled(self, disabled: bool = True) -> dict[str, Any]:
        return await self.send("Network.setCacheDisabled", {"cacheDisabled": disabled})

    async def clear_browser_cache(self) -> dict[str, Any]:
        return await self.send("Network.clearBrowserCache")

    async def get_cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        params = {"urls": list(urls)} if urls else {}
        result = await self.send("Network.getCookies", params)
        return [BrowserCookie.from_source(cookie) for cookie in result.get("cookies", [])]

    async def clear_cookies(self) -> dict[str, Any]:
        return await self.send("Network.clearBrowserCookies")

    async def response_body(self, request_id: str) -> CDPResponseBody:
        result = await self.send("Network.getResponseBody", {"requestId": request_id})
        base64_encoded = bool(result.get("base64Encoded", False))
        body = str(result.get("body", ""))
        content = base64.b64decode(body) if base64_encoded else body.encode("utf-8")
        return CDPResponseBody(
            request_id=request_id,
            content=content,
            base64_encoded=base64_encoded,
            source=result,
        )

    async def subscribe(
        self, event: str, handler: Callable[[Any], Any]
    ) -> Callable[[], None]:
        return (await self.session()).on(event, handler)

    async def close(self) -> None:
        """Detach the page's cached CDP session."""
        session = await self.session()
        await session.detach()
