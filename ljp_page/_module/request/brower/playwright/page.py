"""Asynchronous Playwright page wrapper and CDP conveniences."""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal

from ..base.fingerprint import CDPDOM, CloudflareChallenge
from ..base.fingerprint.dom import _debug
from ..base.model import (
    AsyncPage,
    BrowserCookie,
    CDPSession,
    FetchResult,
    NavigationResult,
)
from .cdp import PageCDP
from .fingerprint import PlaywrightFingerprint
from .request import FetchRequest
from .verification import CfResponseChecker, VerificationGate

if TYPE_CHECKING:
    from playwright.async_api import Page as PlaywrightPage

    from .context import Ljp_Context

__all__ = ["Ljp_Page"]

LoadState = Literal["commit", "domcontentloaded", "load", "networkidle"]


class Ljp_Page(AsyncPage):  # noqa: N801
    """A typed async page surface that preserves native Playwright access.

    ``source`` references the native Playwright page. Use it whenever a
    Playwright-only API is needed; common actions should use this wrapper.
    """

    def __init__(self, source: "PlaywrightPage", context: "Ljp_Context") -> None:
        self.source = source
        self.context = context
        self._cdp_session: CDPSession | None = None
        self.cdp = PageCDP(self)
        self.fingerprint = PlaywrightFingerprint(self)
        self._closed = False
        self._cf_checker = CfResponseChecker()
        self.verify_gate = VerificationGate(checker=self._cf_checker.is_cf_challenge)
        self.fetch = FetchRequest(self)
        self.fetch.set_verify_gate(self.verify_gate)

    @property
    def browser(self) -> Any:
        return self.context.browser

    @property
    def url(self) -> str:
        return self.source.url

    @property
    def frames(self) -> list[Any]:
        return list(self.source.frames)

    @property
    def headers(self) -> dict[str, str]:
        return self.context.headers

    @property
    def request(self) -> Any:
        return self.source.request

    @property
    def closed(self) -> bool:
        return self._closed

    async def title(self) -> str:
        return await self.source.title()

    async def content(self) -> str:
        return await self.source.content()

    async def cookies(self, urls: Sequence[str] | None = None) -> list[BrowserCookie]:
        return await self.context.cookies(urls)

    async def set_cookies(self, cookies: Sequence[BrowserCookie | Mapping[str, Any]]) -> None:
        await self.context.set_cookies(cookies)

    async def clear_cookies(self) -> None:
        await self.context.clear_cookies()

    async def set_headers(self, headers: Mapping[str, str]) -> None:
        await self.context.set_headers(headers)

    async def update_headers(self, headers: Mapping[str, str]) -> None:
        await self.context.update_headers(headers)

    async def goto(
        self,
        url: str,
        *,
        wait_until: LoadState = "domcontentloaded",
        timeout: float | None = 30_000,
        referer: str | None = None,
    ) -> NavigationResult:
        response = await self.source.goto(
            url, wait_until=wait_until, timeout=timeout, referer=referer
        )
        self._cdp_session = None
        return await _navigation_result(response, self.url)

    async def reload(
        self,
        *,
        wait_until: LoadState = "load",
        timeout: float | None = None,
    ) -> NavigationResult:
        response = await self.source.reload(wait_until=wait_until, timeout=timeout)
        self._cdp_session = None
        return await _navigation_result(response, self.url)

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        if arg is None:
            return await self.source.evaluate(expression)
        return await self.source.evaluate(expression, arg)

    async def fetch_request(self, method: str, url: str, **options: Any) -> FetchResult:
        return await self.fetch.request(method, url, **options)

    async def click(self, selector: str, *, timeout: float | None = None, **options: Any) -> None:
        await self.source.click(selector, timeout=timeout, **options)

    async def fill(self, selector: str, value: str, *, timeout: float | None = None) -> None:
        await self.source.fill(selector, value, timeout=timeout)

    async def wait_for_selector(self, selector: str, **options: Any) -> Any:
        return await self.source.wait_for_selector(selector, **options)

    async def solve_cloudflare(
        self,
        *,
        timeout: float = 30.0,
        poll_interval: float = 0.3,
        max_attempts: int = 3,
    ) -> bool:
        """Detect and solve the current Cloudflare challenge.

        This is the public entry point. Shadow DOM traversal, OOPIF target
        attachment, trusted CDP mouse events and replacement-widget retries
        remain implementation details of the page wrapper.
        """
        return await CloudflareChallenge(self).solve(
            timeout=timeout,
            poll_interval=poll_interval,
            max_attempts=max_attempts,
        )

    async def _click_cloudflare_checkbox_cdp(self, frame_id: str) -> bool:
        """Attach to a Cloudflare OOPIF through browser-level CDP and click."""
        if not frame_id or getattr(self.context.browser, "_browser", None) is None:
            return False
        browser_cdp = await self.context.browser._browser.new_browser_cdp_session()

        session_id: str | None = None
        try:
            targets = await browser_cdp.send("Target.getTargets")
            target_infos = targets.get("targetInfos", [])
            target = next(
                (item for item in target_infos if item.get("targetId") == frame_id),
                None,
            )
            if target is None:
                target = next(
                    (
                        item
                        for item in target_infos
                        if item.get("type") == "iframe"
                        and "challenges.cloudflare.com" in item.get("url", "")
                    ),
                    None,
                )
            if target is None:
                _debug("challenge iframe target not found")
                return False
            _debug("challenge iframe target attached")
            attached = await browser_cdp.send(
                "Target.attachToTarget",
                {"targetId": target["targetId"], "flatten": False},
            )
            session_id = attached.get("sessionId")
            if not session_id:
                _debug("challenge iframe target attach failed")
                return False
            loop = asyncio.get_running_loop()
            response: asyncio.Future[dict[str, Any]] = loop.create_future()
            next_id = 0

            def on_message(params: dict[str, Any]) -> None:
                if params.get("sessionId") != session_id:
                    return
                try:
                    message = json.loads(params.get("message", "{}"))
                except (TypeError, json.JSONDecodeError):
                    return
                if not response.done():
                    response.set_result(message)

            unsubscribe = browser_cdp.on(
                "Target.receivedMessageFromTarget", on_message
            )

            async def send_target(method: str, params: dict[str, Any]) -> dict[str, Any]:
                nonlocal next_id, response
                next_id += 1
                response = loop.create_future()
                await browser_cdp.send(
                    "Target.sendMessageToTarget",
                    {
                        "sessionId": session_id,
                        "message": json.dumps(
                            {"id": next_id, "method": method, "params": params}
                        ),
                    },
                )
                message = await asyncio.wait_for(response, timeout=2)
                return message.get("result", {})

            document = await send_target(
                "DOM.getDocument", {"depth": -1, "pierce": True}
            )
            checkbox = CDPDOM.find_node(
                document.get("root", {}),
                lambda node: node.get("nodeName", "").casefold() == "input"
                and CDPDOM.attributes(node).get("type", "").casefold() == "checkbox",
            )
            if checkbox is None:
                _debug("challenge checkbox not found in iframe")
                return False
            _debug("challenge checkbox found")
            node_id = checkbox.get("nodeId")
            if node_id:
                try:
                    await send_target(
                        "DOM.scrollIntoViewIfNeeded", {"nodeId": int(node_id)}
                    )
                    box = await send_target(
                        "DOM.getBoxModel", {"nodeId": int(node_id)}
                    )
                    model = box.get("model", {})
                    quad = model.get("content") or model.get("border")
                    if quad:
                        x_values = quad[0::2]
                        y_values = quad[1::2]
                        x = (min(x_values) + max(x_values)) / 2
                        y = (min(y_values) + max(y_values)) / 2
                        await send_target(
                            "Input.dispatchMouseEvent",
                            {"type": "mouseMoved", "x": x, "y": y},
                        )
                        await send_target(
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mousePressed",
                                "x": x,
                                "y": y,
                                "button": "left",
                                "clickCount": 1,
                            },
                        )
                        await asyncio.sleep(0.1)
                        await send_target(
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mouseReleased",
                                "x": x,
                                "y": y,
                                "button": "left",
                                "clickCount": 1,
                            },
                        )
                        _debug(f"challenge checkbox clicked x={x:.1f} y={y:.1f}")
                        if callable(unsubscribe):
                            unsubscribe()
                        return True
                except Exception as exc:
                    _debug(f"challenge mouse click failed ({type(exc).__name__})")
            resolved = await send_target(
                "DOM.resolveNode", {"nodeId": node_id}
            )
            remote = resolved.get("object", {})
            if not remote.get("objectId"):
                _debug("challenge checkbox resolve failed")
                return False
            clicked = await send_target(
                "Runtime.callFunctionOn",
                {
                    "objectId": remote["objectId"],
                    "functionDeclaration": "function() { this.click(); return true; }",
                    "returnByValue": True,
                    "userGesture": True,
                },
            )
            if callable(unsubscribe):
                unsubscribe()
            _debug("challenge checkbox clicked with DOM fallback")
            return clicked.get("result", {}).get("value") is True
        finally:
            if session_id:
                with contextlib.suppress(Exception):
                    await browser_cdp.send(
                        "Target.detachFromTarget", {"sessionId": session_id}
                    )
            await browser_cdp.detach()

    async def screenshot(self, **options: Any) -> bytes:
        return await self.source.screenshot(**options)

    def locator(self, selector: str) -> Any:
        return self.source.locator(selector)

    def get_by_text(self, text: str, **options: Any) -> Any:
        return self.source.get_by_text(text, **options)

    def get_by_role(self, role: str, **options: Any) -> Any:
        return self.source.get_by_role(role, **options)

    async def get_cdp_session(self, target: Any = None) -> CDPSession:
        """Return a cached page CDP session or a new target-specific session."""
        native_target = getattr(target, "source", target)
        if native_target is not None:
            return await self.context.new_cdp_session(native_target)
        if self._cdp_session is None or self._cdp_session.closed:
            self._cdp_session = await self.context.new_cdp_session(self.source)
        return self._cdp_session

    async def close(self) -> None:
        if self._closed:
            return
        if self._cdp_session is not None:
            await self._cdp_session.close()
        await self.source.close()
        self._closed = True


async def _response_headers(response: Any) -> dict[str, str]:
    if response is None:
        return {}
    try:
        headers = await response.all_headers()
    except AttributeError:
        headers = response.headers
    return {str(name): str(value) for name, value in headers.items()}


async def _navigation_result(response: Any, page_url: str) -> NavigationResult:
    if response is None:
        return NavigationResult(url=page_url, status=None, headers={}, source=None)
    return NavigationResult(
        url=str(response.url),
        status=int(response.status),
        headers=await _response_headers(response),
        source=response,
    )
