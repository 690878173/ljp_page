from __future__ import annotations

import asyncio
import contextlib
import random
from typing import Any, Awaitable, Callable, Iterator,Protocol, Any, Awaitable, Union

from ljp_page._core.utils.other import f_mark
from ljp_page._core.utils.async_tool import resolve_value
from .dom import DomCommands, InputCommands, RuntimeCommands

CdpSend = Callable[..., Awaitable[dict[str, Any]]]


class FP_targe:  # noqa: N801
    """常用反爬目标域名配置。"""

    CHALLENGE_DOMAIN = "challenges.cloudflare.com"
    INVALID_TITLE_KEYWORDS = (
        "Just a moment",
        "www.cloudflare.com",
        "challenge-platform",
        "Verify you are human",
        "请稍候",
    )


class CDPBaseSession:
    """统一 CDP 会话适配器。

    支持 Playwright 的 CDPSession、具有 send 方法的对象，以及直接传入
    send 协程函数的场景。内部统一暴露 send(method=..., params=...)。
    """

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


class FP_DOM:  # noqa: N801
    """基于 CDP 命令的通用 DOM、shadow root 遍历与点击工具。"""

    _DOMAIN: str = ""
    _CHECKBOX_CLASS: str = ""
    _CDPSession: type[CDPBaseSession] = CDPBaseSession

    @classmethod
    def as_cdp_session(cls, cdp_session) -> CDPBaseSession:
        """将原始 CDP session 或 send 函数统一包装为 CDPBaseSession。"""
        if isinstance(cdp_session, CDPBaseSession):
            return cdp_session
        return cls._CDPSession(cdp_session)

    @staticmethod
    @f_mark("将 CDP 节点的 attributes 列表转换为字典")
    def attrs(node: dict[str, Any]) -> dict[str, str]:
        """将 CDP 节点的 attributes 列表转换为字典。"""
        raw_attrs = node.get("attributes", [])
        return {
            str(raw_attrs[i]): str(raw_attrs[i + 1])
            for i in range(0, len(raw_attrs) - 1, 2)
        }

    @classmethod
    @f_mark("判断当前节点自身信息是否包含目标域名")
    def has_targe_domain(cls, node: dict[str, Any]) -> bool:
        """判断当前节点自身信息是否包含目标域名。"""
        attrs = cls.attrs(node)
        values = [
            node.get("documentURL", ""),
            node.get("baseURL", ""),
            node.get("frameId", ""),
            *attrs.values(),
        ]
        return bool(cls._DOMAIN) and any(cls._DOMAIN in str(value) for value in values)

    @classmethod
    def _iter_nodes(cls,node: dict[str, Any], *,in_targe_tree: bool = False,) -> Iterator[tuple[dict[str, Any], bool]]:
        """深度遍历 DOM、iframe 文档和 shadow root，并保留目标子树状态。"""
        current_in_targe = in_targe_tree or cls.has_targe_domain(node)
        yield node, current_in_targe

        content_document = node.get("contentDocument")
        if content_document:
            yield from cls._iter_nodes(content_document, in_targe_tree=current_in_targe)

        for key in ("shadowRoots", "templateContent", "children"):
            children = node.get(key)
            if isinstance(children, dict):
                yield from cls._iter_nodes(children, in_targe_tree=current_in_targe)
                continue
            for child in children or []:
                yield from cls._iter_nodes(child, in_targe_tree=current_in_targe)

    @classmethod
    @f_mark("找所有影子根，only_one仅返回找到的第一个")
    def find_shadow_roots(cls,root: dict[str, Any],only_one: bool = False,*,deep: bool = False,) -> list[dict[str, Any]] | dict[str, Any] | None:
        """查找 DOM 树中的 shadow root。"""
        shadow_roots: list[dict[str, Any]] = []
        seen: set[int] = set()

        def walk(node: dict[str, Any], in_shadow: bool = False) -> dict[str, Any] | None:
            for shadow_root in node.get("shadowRoots", []) or []:
                shadow_id = id(shadow_root)
                if shadow_id not in seen and (deep or not in_shadow):
                    seen.add(shadow_id)
                    if only_one:
                        return shadow_root
                    shadow_roots.append(shadow_root)

                found = walk(shadow_root, in_shadow=True)
                if found is not None:
                    return found

            content_document = node.get("contentDocument")
            if content_document:
                found = walk(content_document, in_shadow=in_shadow)
                if found is not None:
                    return found

            for child in node.get("children", []) or []:
                found = walk(child, in_shadow=in_shadow)
                if found is not None:
                    return found

            return None

        found_root = walk(root)
        if only_one:
            return found_root
        return shadow_roots

    @classmethod
    @f_mark("判断 CDP 节点是否为目标复选框元素,目标span且class属性为指定类属性")
    def _is_checkbox_node(cls, node: dict[str, Any]) -> bool:
        """判断 CDP 节点是否为目标复选框元素。"""
        attrs = cls.attrs(node)
        class_names = attrs.get("class", "").split()
        local_name = str(node.get("localName", "")).lower()
        return local_name == "span" and cls._CHECKBOX_CLASS in class_names

    @classmethod
    @f_mark("在当前 DOM 树中直接查找复选框节点")
    def find_checkbox(cls, root: dict[str, Any], targe: bool = False) -> dict[str, Any] | None:
        """在当前 DOM 树中直接查找复选框节点。"""
        for node, in_targe_tree in cls._iter_nodes(root):
            if targe and not in_targe_tree:
                continue
            if cls._is_checkbox_node(node):
                return node
        return None

    @classmethod
    @f_mark("通过 CDP 获取完整 DOM 树")
    async def cdp_get_document(cls, cdp_session) -> dict[str, Any]:
        """通过 CDP 获取完整 DOM 树。"""
        session = cls.as_cdp_session(cdp_session)
        return await session.send(**DomCommands.get_document(depth=-1, pierce=True))

    @classmethod
    @f_mark("轮询查找 shadow root")
    async def cdp_find_shadow_root(cls,cdp_session,timeout: float = 0,poll_interval: float = 0.3,) -> dict[str, Any] | None:
        """轮询查找 shadow root。"""
        start = asyncio.get_event_loop().time()
        while True:
            dom = await cls.cdp_get_document(cdp_session)
            shadow_root = cls.find_shadow_roots(dom["root"], deep=True, only_one=True)
            if shadow_root is not None:
                return shadow_root
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                return None
            await asyncio.sleep(poll_interval)

    @classmethod
    async def cdp_find_checkbox(
        cls,
        cdp_session,
        timeout: float = 0,
        poll_interval: float = 0.3,
        targe: bool = False,
    ) -> dict[str, Any] | None:
        """轮询查找当前 CDP 目标内的复选框。"""
        start = asyncio.get_event_loop().time()
        while True:
            dom = await cls.cdp_get_document(cdp_session)
            checkbox = cls.find_checkbox(dom["root"], targe=targe)
            if checkbox is not None:
                return checkbox
            if not timeout or asyncio.get_event_loop().time() - start > timeout:
                return None
            await asyncio.sleep(poll_interval)

    @classmethod
    async def cdp_click_node(cls, cdp_session, node_id: int) -> None:
        """使用 CDP 坐标点击节点，失败时退回 DOM click。"""
        session = cls.as_cdp_session(cdp_session)
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



class PageHost(Protocol):
    """FP_Find 需要的宿主能力"""

    @property
    async def title(self) -> Union[str, Awaitable[str]]: ...

    @property
    def frames(self) -> Union[list, Awaitable[list]]: ...

    @property
    async def cookies(self) -> Union[list, Awaitable[list]]: ...

    async def get_cdp_session(self, own=None) -> Any: ...


    def info(self, msg: str) -> None: ...

    def error(self, msg: str) -> None: ...
    # 还可以加上 warning 等

class FP_Find:  # noqa: N801
    """通用验证页查找/点击流程基类。"""

    _DOM: type[FP_DOM] = FP_DOM
    _STR: type[FP_targe] = FP_targe

    def __init__(self,host: PageHost) -> None:
        self._host = host

    async def _get_title(self) -> str:
        return await resolve_value(self._host.title)

    async def _get_frames(self):
        return await resolve_value(self._host.frames)

    async def _get_cookies(self):
        return await resolve_value(self._host.cookies)

    async def has_cookie(self) -> bool:
        return bool(await self._get_cookies())

    async def check_fp(self) -> bool:
        """返回当前是否仍处于验证页；子类可按具体站点覆盖。"""
        return await self.is_challenge_page()

    async def is_challenge_page(self) -> bool:
        """判断当前页面是否仍存在目标验证 iframe。"""
        title = await self._get_title()
        if any(keyword in title for keyword in self._STR.INVALID_TITLE_KEYWORDS):
            return True
        frames = await self._get_frames()
        return any(self._DOM._DOMAIN in item.url for item in frames)


    async def _get_cdp_session(self, own=None):
        return self._DOM.as_cdp_session(await self._host.get_cdp_session(own))

    async def get_frame_session(self):
        frame = await self.find_frame()
        return await self._get_cdp_session(frame)

    async def find_frame(self,timeout: float = 10) -> Any:
        """通用的 frame 查找器，匹配不同域名。"""
        start = asyncio.get_event_loop().time()
        while True:
            frames = await self._get_frames()
            frame = next((item for item in frames if self._DOM._DOMAIN in item.url), None)
            if frame is not None:
                return frame
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError("找不到符合条件的 iframe")
            await asyncio.sleep(0.3)

    async def cdp_find_shadow_root(self, timeout: float = 10):
        session = await self._get_cdp_session()
        shadow_root = await self._DOM.cdp_find_shadow_root(session, timeout=timeout)
        if shadow_root is None:
            raise TimeoutError("找不到目标 Shadow Root")
        return shadow_root

    async def cdp_find_checkbox(self, timeout: float = 10):
        session = await self.get_frame_session()
        checkbox = await self._DOM.cdp_find_checkbox(session, timeout=timeout)
        if checkbox is None:
            raise TimeoutError("在目标 iframe 内找不到复选框")
        return session, checkbox

    async def _cf(self, timeout: float = 10):
        timeout = float(timeout)
        session = None
        try:
            await self.cdp_find_shadow_root(timeout=timeout)
            session, checkbox = await self.cdp_find_checkbox(timeout=timeout)
            print(f"找到的目标 Checkbox: {checkbox}")
            await self._DOM.cdp_click_node(cdp_session=session, node_id=checkbox["nodeId"])
            self._host.info("目标 iframe 内点击已执行")
            return await self.wait_result(timeout=max(timeout * 4, 20))
        except Exception as e:
            self._host.error(f"iframe CDP 处理验证失败: {e}")
            return False
        finally:
            if session is not None:
                with contextlib.suppress(Exception):
                    await session.close()

    async def wait_result(self,timeout: float = 15,poll_interval: float = 1,) -> bool:
        """点击验证框后等待页面完成后续校验。"""
        start = asyncio.get_event_loop().time()
        while True:
            if await self.has_cookie():
                return True
            if not await self.is_challenge_page():
                return True
            if asyncio.get_event_loop().time() - start > timeout:
                return False
            await asyncio.sleep(poll_interval)


__all__ = ["CDPBaseSession", "CdpSend", "FP_DOM", "FP_Find", "FP_targe"]
