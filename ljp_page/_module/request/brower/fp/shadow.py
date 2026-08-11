from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
import random

from .base import FP_DOM, CDPBaseSession
from .dom import DomCommands,InputCommands,RuntimeCommands


from ljp_page._core.utils.other import f_mark


class ShadowRootNotFound(RuntimeError):  # noqa: N818
    """未找到 shadow root。"""


class CdpElementNotFound(RuntimeError):  # noqa: N818
    """未找到 CDP 元素。"""


@dataclass(slots=True)
class CDPNode:
    """所有 CDP 节点的基类，提供点击、查询、属性获取等通用能力。"""

    cdp_session: CDPBaseSession
    node_id: int
    backend_node_id: int | None = None

    # ---------- 核心交互能力 ----------
    async def click(self) -> None:
        """模拟真实鼠标点击（含坐标计算和 JS 回退）。"""
        session = self.cdp_session
        if await session.is_closed:
            print('连接关闭了无法点击')
            return

        # 1. 滚动到视图
        await session.send(**DomCommands.scroll_into_view_if_needed(node_id=self.node_id))

        # 2. 尝试坐标点击
        try:
            box = await session.send(**DomCommands.get_box_model(node_id=self.node_id))
            quad = box["model"].get("content") or box["model"]["border"]
            x_values = quad[0::2]
            y_values = quad[1::2]
            width = max(x_values) - min(x_values)
            height = max(y_values) - min(y_values)

            import random
            x = min(x_values) + width * 0.5 + random.uniform(-min(3, width / 4), min(3, width / 4))
            y = min(y_values) + height * 0.5 + random.uniform(-min(3, height / 4), min(3, height / 4))

            await session.send(**InputCommands.dispatch_mouse_event("mouseMoved", x, y))
            await asyncio.sleep(0.1)
            await session.send(**InputCommands.dispatch_mouse_event("mousePressed", x, y))
            await asyncio.sleep(0.08)
            await session.send(**InputCommands.dispatch_mouse_event("mouseReleased", x, y))
            return
        except Exception:
            # 3. 坐标点击失败，回退到 JS 点击
            remote = await session.send(**DomCommands.resolve_node(node_id=self.node_id))
            object_id = remote["object"]["objectId"]
            await session.send(
                **RuntimeCommands.call_function_on(
                    object_id=object_id,
                    function_declaration="function() { this.click(); }",
                )
            )

    async def query(self, selector: str, timeout: float = 0) -> CDPNode | None:
        """在当前节点作用域内查找第一个匹配元素（支持 Shadow DOM）。"""
        start = asyncio.get_event_loop().time()
        while True:
            resp = await self.cdp_session.send(
                **DomCommands.query_selector(self.node_id, selector)
            )
            node_id = resp.get("nodeId")
            if node_id:
                return CDPNode(self.cdp_session, node_id)
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                return None
            await asyncio.sleep(0.3)

    async def query_all(self, selector: str, timeout: float = 0) -> list[CDPNode]:
        """在当前节点作用域内查找所有匹配元素。"""
        start = asyncio.get_event_loop().time()
        while True:
            resp = await self.cdp_session.send(
                **DomCommands.query_selector_all(self.node_id, selector)
            )
            node_ids = resp.get("nodeIds", [])
            if node_ids:
                return [CDPNode(self.cdp_session, nid) for nid in node_ids]
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                return []
            await asyncio.sleep(0.3)

    # ---------- 属性获取 ----------
    @property
    async def outer_html(self) -> str:
        resp = await self.cdp_session.send(**DomCommands.get_outer_html(node_id=self.node_id))
        return resp.get("outerHTML") or resp.get("result", {}).get("outerHTML", "")

    async def get_attribute(self, name: str) -> str | None:
        # 利用 Runtime 获取属性
        remote = await self.cdp_session.send(**DomCommands.resolve_node(node_id=self.node_id))
        obj_id = remote["object"]["objectId"]
        result = await self.cdp_session.send(
            **RuntimeCommands.call_function_on(
                object_id=obj_id,
                function_declaration=f"function() {{ return this.getAttribute('{name}'); }}",
                return_by_value=True,
            )
        )
        return result.get("result", {}).get("value")

    async def get_shadow_root(self, timeout: float = 0) -> "ShadowRoot":
        start = asyncio.get_event_loop().time()
        while True:
            response = await self.cdp_session.send(
                **DomCommands.describe_node(node_id=self.node_id, depth=1, pierce=True)
            )
            node_info = response.get("node") or {}
            shadow_roots = node_info.get("shadowRoots", [])
            if shadow_roots:
                root_node = shadow_roots[0]
                root_id = root_node.get("nodeId")
                if root_id:
                    return ShadowRoot(
                        cdp_session=self.cdp_session,
                        node_id=root_id,
                        backend_node_id=root_node.get("backendNodeId"),
                        mode=root_node.get("shadowRootType", "open"),
                    )
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                raise ShadowRootNotFound("当前元素没有 shadow root")
            await asyncio.sleep(0.5)


@dataclass(slots=True)
class ShadowRoot(CDPNode):
    """通用 ShadowRoot 包装器，只依赖 CDP 指令发送函数。"""
    mode: str = "open"

    @classmethod
    def from_node(cls, cdp_session, node, dom_cls=None):
        return cls(
            cdp_session=cdp_session,
            node_id=node["nodeId"],
            backend_node_id=node.get("backendNodeId"),
            mode=node.get("shadowRootType", "open"),
        )

    def __repr__(self) -> str:
        return f"ShadowRoot(mode={self.mode}, node_id={self.node_id})"


@f_mark(f'考虑移除,没有用法')
async def find_shadow_roots(
    cdp_session,
    *,
    dom_cls: type[FP_DOM] = FP_DOM,
    deep: bool = False,
    timeout: float = 0,
) -> list[ShadowRoot]:
    """通过 CDP 查找当前目标内的 shadow root。"""
    session = dom_cls.as_cdp_session(cdp_session)
    start = asyncio.get_event_loop().time()
    while True:
        dom = await dom_cls.cdp_get_document(session)
        roots = dom_cls.find_shadow_roots(dom["root"], deep=deep)
        if roots:
            return [
                ShadowRoot.from_node(cdp_session=session, node=node, dom_cls=dom_cls)
                for node in roots
            ]
        if not timeout or asyncio.get_event_loop().time() - start > timeout:
            return []
        await asyncio.sleep(0.5)


__all__ = [
    "CdpElementNotFound",
    "ShadowRoot",
    "ShadowRootNotFound",
    "find_shadow_roots",
]
