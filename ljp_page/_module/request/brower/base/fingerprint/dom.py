"""Small, backend-neutral DOM operations expressed through CDP."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable, Iterator
from typing import Any

from ..model import CDPSession

__all__ = ["CDPDOM"]


def _debug(message: str) -> None:
    if os.environ.get("LJP_BROWSER_DEBUG_CDP") == "1":
        print(f"[browser-cdp] {message}", flush=True)


class CDPDOM:
    """DOM traversal and node interaction using the common CDP session."""

    @staticmethod
    def attributes(node: dict[str, Any]) -> dict[str, str]:
        raw_attributes = node.get("attributes", [])
        return {
            str(raw_attributes[index]): str(raw_attributes[index + 1])
            for index in range(0, len(raw_attributes) - 1, 2)
        }

    @classmethod
    def iter_nodes(cls, root: dict[str, Any]) -> Iterator[dict[str, Any]]:
        yield root
        content_document = root.get("contentDocument")
        if isinstance(content_document, dict):
            yield from cls.iter_nodes(content_document)
        for field in ("shadowRoots", "templateContent", "children"):
            children = root.get(field, [])
            if isinstance(children, dict):
                yield from cls.iter_nodes(children)
            elif isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        yield from cls.iter_nodes(child)

    @classmethod
    def find_node(
        cls, root: dict[str, Any], predicate: Callable[[dict[str, Any]], bool]
    ) -> dict[str, Any] | None:
        return next((node for node in cls.iter_nodes(root) if predicate(node)), None)

    @staticmethod
    async def document(session: CDPSession) -> dict[str, Any]:
        return await session.send("DOM.getDocument", {"depth": -1, "pierce": True})

    @staticmethod
    async def query_selector(
        session: CDPSession, node_id: int, selector: str
    ) -> dict[str, Any] | None:
        result = await session.send(
            "DOM.querySelector", {"nodeId": node_id, "selector": selector}
        )
        found_node_id = result.get("nodeId")
        if not found_node_id:
            return None
        result = await session.send(
            "DOM.describeNode", {"nodeId": found_node_id, "depth": 1}
        )
        return result.get("node")

    @classmethod
    async def find_selector(
        cls, session: CDPSession, selector: str
    ) -> dict[str, Any] | None:
        document = await cls.document(session)
        root = document.get("root")
        if not isinstance(root, dict) or not root.get("nodeId"):
            return None
        return await cls.query_selector(session, int(root["nodeId"]), selector)

    @staticmethod
    async def click_node(
        session: CDPSession,
        node_id: int,
        *,
        hold_time: float = 0.1,
    ) -> None:
        """Click a node with the browser's trusted mouse event sequence.

        The sequence mirrors a native element click: scroll the node into
        view, move to its center, press, hold briefly, and release.  A DOM
        ``click()`` is retained only for nodes that do not expose a usable
        box model (for example, hidden or virtual elements).
        """
        try:
            await session.send("DOM.scrollIntoViewIfNeeded", {"nodeId": node_id})
            box = await session.send("DOM.getBoxModel", {"nodeId": node_id})
            quad = box["model"].get("content") or box["model"]["border"]
            x_values = quad[0::2]
            y_values = quad[1::2]
            x = (min(x_values) + max(x_values)) / 2
            y = (min(y_values) + max(y_values)) / 2
            await session.send(
                "Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}
            )
            await session.send(
                "Input.dispatchMouseEvent",
                {
                    "type": "mousePressed",
                    "x": x,
                    "y": y,
                    "button": "left",
                    "clickCount": 1,
                },
            )
            await asyncio.sleep(max(0.0, hold_time))
            await session.send(
                "Input.dispatchMouseEvent",
                {
                    "type": "mouseReleased",
                    "x": x,
                    "y": y,
                    "button": "left",
                    "clickCount": 1,
                },
            )
            return
        except (KeyError, TypeError, ValueError):
            pass

        resolved = await session.send("DOM.resolveNode", {"nodeId": node_id})
        object_id = resolved["object"]["objectId"]
        await session.send(
            "Runtime.callFunctionOn",
            {
                "objectId": object_id,
                "functionDeclaration": "function() { this.click(); }",
            },
        )

    @staticmethod
    async def click_cloudflare_checkbox(
        session: CDPSession, iframe_node: dict[str, Any]
    ) -> bool:
        """Click Turnstile's checkbox from the live iframe DOM.

        The iframe itself can be resolved from a closed outer shadow root by CDP.
        Its document and inner shadow root must then be traversed in JavaScript;
        a coordinate click is unreliable while the widget is still hidden.
        """
        frame_id = iframe_node.get("frameId")
        if frame_id:
            world = await session.send(
                "Page.createIsolatedWorld",
                {
                    "frameId": frame_id,
                    "worldName": "ljp-cloudflare-checkbox",
                    "grantUniveralAccess": True,
                },
            )
            context_id = world.get("executionContextId")
            if context_id:
                result = await session.send(
                    "Runtime.evaluate",
                    {
                        "contextId": context_id,
                        "expression": """
                            (() => {
                                const body = document.body;
                                const root = body && body.shadowRoot;
                                const checkbox = (root && root.querySelector(
                                    'input[type="checkbox"]'
                                )) || document.querySelector('input[type="checkbox"]');
                                if (!checkbox) return false;
                                checkbox.click();
                                return true;
                            })()
                        """,
                        "returnByValue": True,
                        "awaitPromise": True,
                        "userGesture": True,
                    },
                )
                if result.get("result", {}).get("value") is True:
                    return True
                body_result = await session.send(
                    "Runtime.evaluate",
                    {
                        "contextId": context_id,
                        "expression": "document.body",
                        "returnByValue": False,
                    },
                )
                body_object = body_result.get("result", {}).get("object", {})
                body_object_id = body_object.get("objectId")
                if body_object_id:
                    try:
                        described = await session.send(
                            "DOM.describeNode",
                            {
                                "objectId": body_object_id,
                                "depth": -1,
                                "pierce": True,
                            },
                        )
                    except Exception:
                        described = {}
                    body_node = described.get("node", {})
                    checkbox = _find_checkbox_node(body_node)
                    if checkbox and checkbox.get("nodeId"):
                        resolved_checkbox = await session.send(
                            "DOM.resolveNode", {"nodeId": int(checkbox["nodeId"])}
                        )
                        checkbox_object = resolved_checkbox.get(
                            "object", resolved_checkbox.get("result", {}).get("object", {})
                        )
                        checkbox_object_id = (
                            checkbox_object.get("objectId")
                            if isinstance(checkbox_object, dict)
                            else None
                        )
                        if checkbox_object_id:
                            clicked = await session.send(
                                "Runtime.callFunctionOn",
                                {
                                    "objectId": checkbox_object_id,
                                    "functionDeclaration": (
                                        "function() { this.click(); return true; }"
                                    ),
                                    "returnByValue": True,
                                    "userGesture": True,
                                },
                            )
                            if clicked.get("result", {}).get("value") is True:
                                return True

        node_id = iframe_node.get("nodeId")
        if not node_id:
            return False
        resolved = await session.send("DOM.resolveNode", {"nodeId": int(node_id)})
        remote = resolved.get("object", resolved.get("result", {}).get("object", {}))
        object_id = remote.get("objectId") if isinstance(remote, dict) else None
        if not object_id:
            return False
        result = await session.send(
            "Runtime.callFunctionOn",
            {
                "objectId": object_id,
                "functionDeclaration": """
                    function() {
                        const doc = this.contentDocument;
                        const body = doc && doc.body;
                        const root = body && body.shadowRoot;
                        const checkbox = root && root.querySelector('input[type="checkbox"]');
                        if (!checkbox) return false;
                        checkbox.click();
                        return true;
                    }
                """,
                "returnByValue": True,
                "userGesture": True,
            },
        )
        value = result.get("result", {}).get("value")
        return value is True


def _find_checkbox_node(root: dict[str, Any]) -> dict[str, Any] | None:
    return CDPDOM.find_node(
        root,
        lambda node: node.get("nodeName", "").casefold() == "input"
        and CDPDOM.attributes(node).get("type", "").casefold() == "checkbox",
    )
