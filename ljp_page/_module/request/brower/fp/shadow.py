from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from .base import FP_DOM, CDPBaseSession
from .dom import DomCommands


class ShadowRootNotFound(RuntimeError):  # noqa: N818
    """未找到 shadow root。"""


class CdpElementNotFound(RuntimeError):  # noqa: N818
    """未找到 CDP 元素。"""


@dataclass(slots=True)
class CdpElement:
    """基于 CDP nodeId 的轻量元素包装器。"""

    cdp_session: CDPBaseSession
    node_id: int
    backend_node_id: int | None = None
    dom_cls: type[FP_DOM] = FP_DOM

    async def click(self) -> None:
        """点击当前节点。"""
        await self.dom_cls.cdp_click_node(self.cdp_session, self.node_id)

    @property
    async def outer_html(self) -> str:
        """返回当前节点的 HTML。"""
        response = await self.cdp_session.send(
            **DomCommands.get_outer_html(node_id=self.node_id)
        )
        return response.get("outerHTML") or response.get("result", {}).get("outerHTML", "")

    async def get_shadow_root(self, timeout: float = 0) -> "ShadowRoot":
        """获取当前元素挂载的 shadow root，行为参考 pydoll WebElement.get_shadow_root。"""
        start = asyncio.get_event_loop().time()
        while True:
            response = await self.cdp_session.send(
                **DomCommands.describe_node(node_id=self.node_id, depth=1, pierce=True)
            )
            node_info = response.get("node") or response.get("result", {}).get("node", {})
            shadow_roots = node_info.get("shadowRoots", [])
            if shadow_roots:
                return ShadowRoot.from_node(
                    cdp_session=self.cdp_session,
                    node=shadow_roots[0],
                    dom_cls=self.dom_cls,
                    host_element=self,
                )

            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                raise ShadowRootNotFound("当前元素没有 shadow root")
            await asyncio.sleep(0.5)


@dataclass(slots=True)
class ShadowRoot:
    """通用 ShadowRoot 包装器，只依赖 CDP 指令发送函数。"""

    cdp_session: CDPBaseSession
    node_id: int
    backend_node_id: int | None = None
    mode: str = "open"
    host_element: CdpElement | None = None
    dom_cls: type[FP_DOM] = FP_DOM

    @classmethod
    def from_node(
        cls,
        cdp_session,
        node: dict[str, Any],
        dom_cls: type[FP_DOM] = FP_DOM,
        host_element: CdpElement | None = None,
    ) -> "ShadowRoot":
        """根据 CDP shadow root 节点构建 ShadowRoot。"""
        node_id = node.get("nodeId")
        if node_id is None:
            raise ShadowRootNotFound("shadow root 缺少 nodeId，无法继续查询")
        return cls(
            cdp_session=dom_cls.as_cdp_session(cdp_session),
            node_id=node_id,
            backend_node_id=node.get("backendNodeId"),
            mode=node.get("shadowRootType", "open"),
            host_element=host_element,
            dom_cls=dom_cls,
        )

    @property
    async def inner_html(self) -> str:
        """返回 shadow root 的 HTML。"""
        response = await self.cdp_session.send(
            **DomCommands.get_outer_html(node_id=self.node_id)
        )
        return response.get("outerHTML") or response.get("result", {}).get("outerHTML", "")

    async def query(
        self,
        selector: str,
        *,
        find_all: bool = False,
        timeout: float = 0,
        raise_exc: bool = True,
    ) -> CdpElement | list[CdpElement] | None:
        """在 shadow root 内执行 CSS 查询，参考 pydoll ShadowRoot.query。"""
        start = asyncio.get_event_loop().time()
        while True:
            command = (
                DomCommands.query_selector_all(self.node_id, selector)
                if find_all
                else DomCommands.query_selector(self.node_id, selector)
            )
            response = await self.cdp_session.send(**command)

            if find_all:
                node_ids = response.get("nodeIds") or response.get("result", {}).get("nodeIds", [])
                if node_ids:
                    return [
                        CdpElement(self.cdp_session, node_id, dom_cls=self.dom_cls)
                        for node_id in node_ids
                    ]
            else:
                node_id = response.get("nodeId") or response.get("result", {}).get("nodeId", 0)
                if node_id:
                    return CdpElement(self.cdp_session, node_id, dom_cls=self.dom_cls)

            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                if raise_exc:
                    raise CdpElementNotFound(f"shadow root 内未找到元素: {selector}")
                return [] if find_all else None
            await asyncio.sleep(0.5)

    def __repr__(self) -> str:
        return f"ShadowRoot(mode={self.mode}, node_id={self.node_id})"


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
    "CdpElement",
    "CdpElementNotFound",
    "ShadowRoot",
    "ShadowRootNotFound",
    "find_shadow_roots",
]
