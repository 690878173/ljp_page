from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ljp_page._modules.pydoll.protocol.accessibility.methods import (
    AccessibilityMethod,
    GetAXNodeAndAncestorsParams,
    GetChildAXNodesParams,
    GetFullAXTreeParams,
    GetPartialAXTreeParams,
    GetRootAXNodeParams,
    QueryAXTreeParams,
)
from ljp_page._modules.pydoll.protocol.base import Command

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.protocol.accessibility.methods import (
        DisableCommand,
        EnableCommand,
        GetAXNodeAndAncestorsCommand,
        GetChildAXNodesCommand,
        GetFullAXTreeCommand,
        GetPartialAXTreeCommand,
        GetRootAXNodeCommand,
        QueryAXTreeCommand,
    )
    from ljp_page._modules.pydoll.protocol.accessibility.types import AXNodeId


class AccessibilityCommands:
    """针对辅助功能域实施 Chrome DevTools 协议。

    此类提供与可访问性树交互的命令，
    启用对页面上可访问节点的检查和查询。

    请参阅 https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/"""

    @staticmethod
    def disable() -> DisableCommand:
        """禁用可访问域。

        返回：
            DisableCommand：禁用可访问域的 CDP 命令。"""
        return Command(method=AccessibilityMethod.DISABLE)

    @staticmethod
    def enable() -> EnableCommand:
        """启用导致 AXNodeIds 保留的可访问域
        方法调用之间保持一致。

        返回：
            EnableCommand：启用可访问域的 CDP 命令。"""
        return Command(method=AccessibilityMethod.ENABLE)

    @staticmethod
    def get_partial_ax_tree(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        fetch_relatives: Optional[bool] = None,
    ) -> GetPartialAXTreeCommand:
        """为此获取可访问性节点和部分可访问性树
        DOM 节点（如果存在）。

        参数：
            node_id：获取部分可访问性的节点标识符
                树为.
            backend_node_id：获取部分的后端节点的标识符
                的可访问性树。
            object_id：要获取的节点包装器的 JavaScript 对象 id
                部分可访问性树。
            fetch_relatives：是否获取该节点的祖先、兄弟姐妹
                和孩子们。默认为 True。

        返回：
            GetPartialAXTreeCommand：获取部分 AX 树的 CDP 命令。"""
        params = GetPartialAXTreeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if fetch_relatives is not None:
            params['fetchRelatives'] = fetch_relatives
        return Command(method=AccessibilityMethod.GET_PARTIAL_AX_TREE, params=params)

    @staticmethod
    def get_full_ax_tree(
        depth: Optional[int] = None,
        frame_id: Optional[str] = None,
    ) -> GetFullAXTreeCommand:
        """获取根文档的整个辅助功能树。

        参数：
            深度：根节点的后代的最大深度
                应该被检索。如果省略，则返回完整的树。
            frame_id：AX 树应该属于其文档的框架
                检索到。如果省略，则使用根框架。

        返回：
            GetFullAXTreeCommand：获取完整 AX 树的 CDP 命令。"""
        params = GetFullAXTreeParams()
        if depth is not None:
            params['depth'] = depth
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=AccessibilityMethod.GET_FULL_AX_TREE, params=params)

    @staticmethod
    def get_root_ax_node(
        frame_id: Optional[str] = None,
    ) -> GetRootAXNodeCommand:
        """获取文档的可访问性树的根节点。

        参数：
            frame_id：节点所在文档的框架。如果省略，
                使用根框架。

        返回：
            GetRootAXNodeCommand：获取根 AX 节点的 CDP 命令。"""
        params = GetRootAXNodeParams()
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=AccessibilityMethod.GET_ROOT_AX_NODE, params=params)

    @staticmethod
    def get_ax_node_and_ancestors(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> GetAXNodeAndAncestorsCommand:
        """获取一个节点和所有祖先直到并包括根。

        参数：
            node_id：要获取祖先的节点的标识符。
            backend_node_id：要获取祖先的后端节点的标识符。
            object_id：要获取的节点包装器的 JavaScript 对象 id
                祖先为.

        返回：
            GetAXNodeAndAncestorsCommand：获取节点及其祖先的 CDP 命令。"""
        params = GetAXNodeAndAncestorsParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=AccessibilityMethod.GET_AX_NODE_AND_ANCESTORS, params=params)

    @staticmethod
    def get_child_ax_nodes(
        id: AXNodeId,
        frame_id: Optional[str] = None,
    ) -> GetChildAXNodesCommand:
        """通过 AXNodeId 获取特定的可访问性节点。

        参数：
            id：应检索其子节点的 AXNodeId。
            frame_id：节点所在文档的框架。如果省略，
                使用根框架。

        返回：
            GetChildAXNodesCommand：获取子 AX 节点的 CDP 命令。"""
        params = GetChildAXNodesParams(id=id)
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=AccessibilityMethod.GET_CHILD_AX_NODES, params=params)

    @staticmethod
    def query_ax_tree(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        accessible_name: Optional[str] = None,
        role: Optional[str] = None,
    ) -> QueryAXTreeCommand:
        """查询可访问性树中具有以下属性的节点的 DOM 子树：
        名字和/或角色。

        参数：
            node_id：子树根节点的标识符
                搜索进去。
            backend_node_id：根的后端节点的标识符
                要搜索的子树。
            object_id：根节点包装器的 JavaScript 对象 ID
                要搜索的子树的位置。
            accessible_name：查找具有此计算名称的节点。
            角色：查找具有此计算角色的节点。

        返回：
            QueryAXTreeCommand：查询 AX 树的 CDP 命令。"""
        params = QueryAXTreeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if accessible_name is not None:
            params['accessibleName'] = accessible_name
        if role is not None:
            params['role'] = role
        return Command(method=AccessibilityMethod.QUERY_AX_TREE, params=params)
