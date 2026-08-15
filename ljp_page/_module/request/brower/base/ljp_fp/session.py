from __future__ import annotations

import asyncio
import random
from typing import Any, Iterator
from ..commands.dom_commands import DomCommands
from ..commands.input_commands import InputCommands
from ..commands.runtime_commands import RuntimeCommands
from .dom import DOM

class CDPBaseSession:
    """统一 CDP 会话适配器。

    支持 Playwright 的 CDPSession、具有 send 方法的对象，以及直接传入
    send 协程函数的场景。内部统一暴露 send(method=..., params=...)。
    """
    dom = DOM

    def __init__(self, cdp_session) -> None:
        self.cdp_session = cdp_session

    async def send(self,method: str | None = None,params: dict[str, Any] | None = None,**command,):
        """发送 CDP 指令。"""
        if command:
            method = command.get("method", method)
            params = command.get("params", params)
        if method is None:
            raise ValueError("CDP method 不能为空")
        params = params or {}

        if hasattr(self.cdp_session, "send") and callable(self.cdp_session.send):
            return await self.cdp_session.send(method, params)
        return await self.cdp_session(method, params)

    @property
    async def is_closed(self) -> bool:
        """检测 CDP session 是否已关闭。"""
        try:
            await self.send("Runtime.evaluate", {"expression": "1"})
            return False
        except Exception:
            return True

    # NOTE 通过 CDP 获取完整 DOM 树
    async def _get_document(self) -> dict[str, Any]:
        """通过 CDP 获取完整 DOM 树。"""
        return await self.cdp_session.send(**DomCommands.get_document(depth=-1, pierce=True))
    # NOTE 在指定的 DOM 节点（node_id）内部执行 querySelector
    async def query_selector(self, node_id: int, selector: str, ) -> dict[str, Any] | None:
        """
        在指定的 DOM 节点（node_id）内部执行 querySelector。
        """
        session = self.cdp_session
        # 1. 发送 CDP 命令：在 node_id 范围内找 selector
        result = await session.send(
            **DomCommands.query_selector(
                node_id=node_id,
                selector=selector
            )
        )

        found_node_id = result.get("nodeId")
        if not found_node_id:
            return None

        # 2. 拿到这个节点的详细信息（包含 nodeId、localName、attributes 等）
        node_info = await session.send(
            **DomCommands.describe_node(
                node_id=found_node_id,
                depth=1  # depth=1 可以顺便把 contentDocument（iframe内容）带回来
            )
        )
        return node_info.get("node")

    # NOTE 轮询查找 shadow root,返回第一个
    @classmethod
    async def cdp_find_shadow_root(cls, cdp_session, timeout: float = 0, poll_interval: float = 0.3, only_one=True) -> None | list[dict[str, Any]] | dict[str, Any] | Any:
        """轮询查找 shadow root。"""
        start = asyncio.get_event_loop().time()
        while True:
            dom = await cls._get_document(cdp_session)
            shadow_root = cls.dom.find_shadow_roots(dom["root"], deep=True, only_one=only_one)
            if shadow_root is not None:
                if only_one:
                    return shadow_root[0]
                else:
                    return shadow_root
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                return None
            await asyncio.sleep(poll_interval)

    async def find_checkbox(self,checkbox_class,timeout: float = 0,poll_interval: float = 0.3,targe: bool = False,) -> dict[str, Any] | None:
        """轮询查找当前 CDP 目标内的复选框。"""
        start = asyncio.get_event_loop().time()
        while True:
            dom = await self._get_document()
            checkbox = self.dom.find_checkbox(dom["root"], targe=targe,checkbox_class=checkbox_class)
            if checkbox is not None:
                return checkbox
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                return None
            await asyncio.sleep(poll_interval)

    async def click_node(self, node_id: int) -> None:
        """使用 CDP 坐标点击节点，失败时退回 DOM click。"""
        session = self.cdp_session
        try:
            await session.send(**DomCommands.scroll_into_view_if_needed(node_id=node_id))
        except Exception:
            pass

        try:
            box = await session.send(**DomCommands.get_box_model(node_id=node_id))
            quad = box["model"].get("content") or box["model"]["border"]
            x_values = quad[0::2]
            y_values = quad[1::2]
            width = max(x_values) - min(x_values)
            height = max(y_values) - min(y_values)
            x = min(x_values) + width * 0.5 + random.uniform(
                -min(3, width / 4),
                min(3, width / 4),
            )
            y = min(y_values) + height * 0.5 + random.uniform(
                -min(3, height / 4),
                min(3, height / 4),
            )

            await session.send(**InputCommands.dispatch_mouse_event("mouseMoved", x, y))
            await asyncio.sleep(random.uniform(0.08, 0.2))
            await session.send(**InputCommands.dispatch_mouse_event("mousePressed", x, y))
            await asyncio.sleep(random.uniform(0.05, 0.12))
            await session.send(**InputCommands.dispatch_mouse_event("mouseReleased", x, y))
            return
        except Exception:
            pass

        remote = await session.send(**DomCommands.resolve_node(node_id=node_id))
        object_id = remote["object"]["objectId"]
        await session.send(
            **RuntimeCommands.call_function_on(
                object_id=object_id,
                function_declaration="function() { this.click(); }",
            ),
        )

    async def close(self):
            """释放底层 CDP 会话；Playwright 使用 detach，部分实现使用 close。"""
            close_method = getattr(self.cdp_session, "detach", None) or getattr(
                self.cdp_session,
                "close",
                None,
            )
            if close_method is None:
                return
            await close_method()

