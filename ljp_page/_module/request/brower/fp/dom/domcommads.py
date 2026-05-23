
from typing import Any, Literal, Optional

from .methods import DomMethod


class DomCommands:

    @staticmethod
    def get_document(
        depth: Optional[int] = None,
        pierce: Optional[bool] = None,
    ) -> dict[str, Literal[DomMethod.GET_DOCUMENT] | dict[Any, Any]]:
        """将根 DOM 节点（以及可选的子树）返回给调用者。

        这通常是与 DOM 交互时调用的第一个命令，因为它
        提供对文档根节点的访问。从这个根可以遍历到
        页面上的任何其他元素。该命令隐式启用 DOM 域事件
        对于当前目标，使其成为 DOM 交互的良好起点。

        参数：
            深度：应检索子项的最大深度（默认值为 1）。
                  对整个子树使用 -1 或提供大于 0 的整数。
            pierce：返回时是否应该遍历iframe和shadow root
                  子树（默认为 false）。

        返回：
            命令：返回根 DOM 节点的 CDP 命令。"""
        params = {}
        if depth is not None:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return dict(method=DomMethod.GET_DOCUMENT, params=params)

    @staticmethod
    def describe_node(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        depth: Optional[int] = None,
        pierce: Optional[bool] = None,
    ):
        """返回节点描述，可用于读取 shadowRoots 等结构信息。"""
        params = {}
        if node_id is not None:
            params["nodeId"] = node_id
        if backend_node_id is not None:
            params["backendNodeId"] = backend_node_id
        if object_id is not None:
            params["objectId"] = object_id
        if depth is not None:
            params["depth"] = depth
        if pierce is not None:
            params["pierce"] = pierce
        return dict(method=DomMethod.DESCRIBE_NODE, params=params)

    @staticmethod
    def query_selector(node_id: int, selector: str):
        """在指定节点作用域内执行 CSS querySelector。"""
        return dict(
            method=DomMethod.QUERY_SELECTOR,
            params={"nodeId": node_id, "selector": selector},
        )

    @staticmethod
    def query_selector_all(node_id: int, selector: str):
        """在指定节点作用域内执行 CSS querySelectorAll。"""
        return dict(
            method=DomMethod.QUERY_SELECTOR_ALL,
            params={"nodeId": node_id, "selector": selector},
        )

    @staticmethod
    def get_outer_html(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ):
        """返回指定节点的 HTML。"""
        params = {}
        if node_id is not None:
            params["nodeId"] = node_id
        if backend_node_id is not None:
            params["backendNodeId"] = backend_node_id
        if object_id is not None:
            params["objectId"] = object_id
        return dict(method=DomMethod.GET_OUTER_HTML, params=params)

    @staticmethod
    def resolve_node(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ):
        """将 DOM 节点解析为 Runtime 远程对象。"""
        params = {}
        if node_id is not None:
            params["nodeId"] = node_id
        if backend_node_id is not None:
            params["backendNodeId"] = backend_node_id
        if object_id is not None:
            params["objectId"] = object_id
        return dict(method=DomMethod.RESOLVE_NODE, params=params)

    @staticmethod
    def scroll_into_view_if_needed(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        rect: Optional[dict] = None,
    ):
        """如果指定节点尚不可见，则将其滚动到视图中。

        该命令对于可靠的网络自动化至关重要，因为它确保元素
        在尝试交互之前，它们实际上在视口中可见。现代
        网站通常使用延迟加载并具有较长的可滚动区域，这使得
        对于处理最初可能不可见的元素至关重要的命令。

        参数：
            node_id：节点的标识符。
            backend_node_id：后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。
            矩形：相对于节点边界滚动到视图中的可选矩形。

        返回：
            命令：CDP 命令将元素滚动到视图中。"""
        params = {}
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if rect is not None:
            params['rect'] = rect
        return dict(method=DomMethod.SCROLL_INTO_VIEW_IF_NEEDED, params=params)

    @staticmethod
    def get_box_model(
            node_id: Optional[int] = None,
            backend_node_id: Optional[int] = None,
            object_id: Optional[str] = None,
    ):
        """返回指定节点的盒模型信息。

        盒模型是 CSS 中的一个基本概念，它描述了元素如何
        使用内容、填充、边框和边距进行渲染。该命令提供
        有关这些尺寸和坐标的详细信息，这是非常宝贵的
        用于空间分析以及与页面上的元素的精确交互。

        参数：
            node_id：节点的标识符。
            backend_node_id：后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。

        返回：
            Command：CDP命令，返回节点的盒模型，包括
                    内容、填充、边框和边距框的坐标。"""
        params = {}
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return dict(method=DomMethod.GET_BOX_MODEL, params=params)


class RuntimeCommands:
    """Runtime 域中与通用 DOM 操作相关的命令。"""

    @staticmethod
    def call_function_on(
        object_id: str,
        function_declaration: str,
        arguments: Optional[list[dict[str, Any]]] = None,
        return_by_value: Optional[bool] = None,
    ):
        params: dict[str, Any] = {
            "objectId": object_id,
            "functionDeclaration": function_declaration,
        }
        if arguments is not None:
            params["arguments"] = arguments
        if return_by_value is not None:
            params["returnByValue"] = return_by_value
        return dict(method="Runtime.callFunctionOn", params=params)


class InputCommands:
    """Input 域鼠标事件命令。"""

    @staticmethod
    def dispatch_mouse_event(
        event_type: str,
        x: float,
        y: float,
        button: str = "left",
        click_count: int = 1,
    ):
        params: dict[str, Any] = {"type": event_type, "x": x, "y": y}
        if event_type in {"mousePressed", "mouseReleased"}:
            params["button"] = button
            params["clickCount"] = click_count
        return dict(method="Input.dispatchMouseEvent", params=params)


__all__ = ["DomCommands", "InputCommands", "RuntimeCommands"]




