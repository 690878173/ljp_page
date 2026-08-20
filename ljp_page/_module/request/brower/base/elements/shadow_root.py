from __future__ import annotations

from typing import TYPE_CHECKING

from ljp_page._module.request.brower.base.commands import DomCommands
from ljp_page._module.request.brower.base.connection import ConnectionHandler
from ljp_page._module.request.brower.base.elements.mixins import FindElementsMixin
from ljp_page._module.request.brower.base.protocol.dom.types import ShadowRootType

__all__ = ['ShadowRoot']

if TYPE_CHECKING:
    from ljp_page._module.request.brower.base.elements.web_element import WebElement
    from ljp_page._module.request.brower.base.protocol.dom.methods import GetOuterHTMLResponse

from ljp_page.logger import loguru_logger


class ShadowRoot(FindElementsMixin):
    """用于影子 DOM 遍历的影子根包装器。

    提供影子 DOM 边界内的元素查找功能
    将 query() 与 CSS 选择器结合使用。使用 query() 而不是 find() —
    影子根内部不支持 find() 和 XPath。

    用途：
        Shadow_host =等待tab.find(id='我的组件')
        Shadow_root = 等待shadow_host.get_shadow_root()
        按钮=等待shadow_root.query('#internal-button')
        等待按钮.click()"""

    _css_only = True

    def __init__(
        self,
        object_id: str,
        connection_handler: ConnectionHandler,
        mode: ShadowRootType = ShadowRootType.OPEN,
        host_element: WebElement | None = None,
    ):
        """初始化影子根包装器。

        参数：
            object_id：影子根节点的 CDP 对象 ID。
            connection_handler：CDP 命令的浏览器连接。
            mode：影子根模式（开放、封闭或用户代理）。
            host_element：对影子宿主元素的引用。"""
        self._object_id = object_id
        self._connection_handler = connection_handler
        self._mode = mode
        self._host_element = host_element

        #从宿主元素继承 iframe/路由上下文（如果存在）
        if host_element:
            self._iframe_context = getattr(host_element, '_iframe_context', None)
            self._routing_session_handler = getattr(host_element, '_routing_session_handler', None)
            self._routing_session_id = getattr(host_element, '_routing_session_id', None)
            self._routing_parent_frame_id = getattr(host_element, '_routing_parent_frame_id', None)

        loguru_logger.debug(
            f'ShadowRoot initialized: object_id={self._object_id}, mode={self._mode.value}'
        )

    @property
    def mode(self) -> ShadowRootType:
        """影子根模式（开放、封闭或用户代理）。"""
        return self._mode

    @property
    def host_element(self) -> WebElement | None:
        """对影子宿主元素的引用（如果有）。"""
        return self._host_element

    @property
    async def inner_html(self) -> str:
        """影子根的 HTML 内容。"""
        response: GetOuterHTMLResponse = await self._execute_command(
            DomCommands.get_outer_html(object_id=self._object_id)
        )
        return response['result']['outerHTML']

    def __repr__(self) -> str:
        return f'ShadowRoot(mode={self._mode.value}, object_id={self._object_id})'

    def __str__(self) -> str:
        return f'ShadowRoot({self._mode.value})'
