from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from base import Command
from dom.methods import (
    CollectClassNamesFromSubtreeParams,
    CopyToParams,
    DescribeNodeParams,
    DiscardSearchResultsParams,
    DomMethod,
    EnableParams,
    FocusParams,
    GetAnchorElementParams,
    GetAttributesParams,
    GetBoxModelParams,
    GetContainerForNodeParams,
    GetContentQuadsParams,
    GetDocumentParams,
    GetElementByRelationParams,
    GetFileInfoParams,
    GetFrameOwnerParams,
    GetNodeForLocationParams,
    GetNodesForSubtreeByStyleParams,
    GetNodeStackTracesParams,
    GetOuterHTMLParams,
    GetQueryingDescendantsForContainerParams,
    GetRelayoutBoundaryParams,
    GetSearchResultsParams,
    MoveToParams,
    PerformSearchParams,
    PushNodeByPathToFrontendParams,
    PushNodesByBackendIdsToFrontendParams,
    QuerySelectorAllParams,
    QuerySelectorParams,
    RemoveAttributeParams,
    RemoveNodeParams,
    RequestChildNodesParams,
    RequestNodeParams,
    ResolveNodeParams,
    ScrollIntoViewIfNeededParams,
    SetAttributesAsTextParams,
    SetAttributeValueParams,
    SetFileInputFilesParams,
    SetInspectedNodeParams,
    SetNodeNameParams,
    SetNodeStackTracesEnabledParams,
    SetNodeValueParams,
    SetOuterHTMLParams,
)

if TYPE_CHECKING:
    from dom.methods import (
        CollectClassNamesFromSubtreeCommand,
        CopyToCommand,
        CSSComputedStyleProperty,
        DescribeNodeCommand,
        DisableCommand,
        DiscardSearchResultsCommand,
        EnableCommand,
        FocusCommand,
        GetAnchorElementCommand,
        GetAttributesCommand,
        GetBoxModelCommand,
        GetContainerForNodeCommand,
        GetContentQuadsCommand,
        GetDetachedDomNodesCommand,
        GetDocumentCommand,
        GetElementByRelationCommand,
        GetFileInfoCommand,
        GetFrameOwnerCommand,
        GetNodeForLocationCommand,
        GetNodesForSubtreeByStyleCommand,
        GetNodeStackTracesCommand,
        GetOuterHTMLCommand,
        GetQueryingDescendantsForContainerCommand,
        GetRelayoutBoundaryCommand,
        GetSearchResultsCommand,
        GetTopLayerElementsCommand,
        HideHighlightCommand,
        HighlightNodeCommand,
        HighlightRectCommand,
        MarkUndoableStateCommand,
        MoveToCommand,
        PerformSearchCommand,
        PushNodeByPathToFrontendCommand,
        PushNodesByBackendIdsToFrontendCommand,
        QuerySelectorAllCommand,
        QuerySelectorCommand,
        Rect,
        RedoCommand,
        RemoveAttributeCommand,
        RemoveNodeCommand,
        RequestChildNodesCommand,
        RequestNodeCommand,
        ResolveNodeCommand,
        ScrollIntoViewIfNeededCommand,
        SetAttributesAsTextCommand,
        SetAttributeValueCommand,
        SetFileInputFilesCommand,
        SetInspectedNodeCommand,
        SetNodeNameCommand,
        SetNodeStackTracesEnabledCommand,
        SetNodeValueCommand,
        SetOuterHTMLCommand,
        UndoCommand,
    )
    from dom.types import (
        IncludeWhitespace,
        LogicalAxes,
        PhysicalAxes,
        RelationType,
    )


class DomCommands:
    """针对 DOM 域的 Chrome DevTools 协议的实现。

    此类提供与文档对象模型 (DOM) 交互的命令
    浏览器，允许访问和操作网页中的元素结构。
    Chrome DevTools 协议中的 DOM 域公开了读写操作
    DOM，它是浏览器自动化、测试和调试的基础。

    每个 DOM 元素都由具有唯一 ID 的镜像对象表示。这个ID可以用
    收集有关节点的附加信息，将其解析为 JavaScript 对象包装器，
    操纵属性，并对 DOM 结构执行各种其他操作。"""

    @staticmethod
    def describe_node(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        depth: Optional[int] = None,
        pierce: Optional[bool] = None,
    ) -> DescribeNodeCommand:
        """描述由其 ID 标识的 DOM 节点，无需启用域。

        该describe_node命令在需要快速了解的场景下特别有用
        收集有关特定元素的信息，而不订阅 DOM 更改事件，
        使其更轻量级，适合孤立元件检查操作。

        参数：
            node_id：客户端已知的节点的标识符。
            backend_node_id：浏览器内部使用的后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。
            深度：应检索子项的最大深度（默认值为 1）。
                  对整个子树使用 -1 或提供大于 0 的整数。
            pierce：返回时是否应该遍历iframe和shadow root
                   子树（默认为 false）。

        返回：
            命令：CDP 命令，返回有关所请求节点的详细信息。"""
        params = DescribeNodeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if depth:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.DESCRIBE_NODE, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """禁用当前页面的 DOM 代理。

        禁用 DOM 域会阻止 CDP 发送 DOM 相关事件，并且
        阻止进一步的 DOM 操作操作，直到再次启用域。
        当您使用完 DOM 后，这对于优化性能非常重要
        操作并希望尽量减少后台处理。

        返回：
            命令：禁用 DOM 域的 CDP 命令。"""
        return Command(method=DomMethod.DISABLE)

    @staticmethod
    def enable(include_whitespace: Optional['IncludeWhitespace'] = None) -> EnableCommand:
        """为当前页面启用 DOM 代理。

        启用 DOM 域是接收 DOM 事件和使用大多数 DOM 的前提
        操纵方法。 DOM 事件包括 DOM 树结构的更改，
        属性修改等等。如果不先启用该域，
        许多 DOM 操作会失败或提供不完整的信息。

        参数：
            include_whitespace：是否在文件中包含仅空白的文本节点
                               返回节点的子数组。允许值：“无”、“全部”。

        返回：
            命令：启用 DOM 域的 CDP 命令。"""
        params = EnableParams()
        if include_whitespace:
            params['includeWhitespace'] = include_whitespace
        return Command(method=DomMethod.ENABLE, params=params)

    @staticmethod
    def focus(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> FocusCommand:
        """聚焦给定元素。

        焦点命令对于模拟真实的用户交互至关重要，因为许多
        事件（如键盘输入）要求元素首先具有焦点。这也是
        对于测试网页的正确 Tab 键顺序和键盘可访问性非常重要。

        参数：
            node_id：要关注的节点的标识符。
            backend_node_id：要关注的后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。

        返回：
            命令：CDP 命令聚焦于指定元素。"""
        params = FocusParams()
        if node_id:
            params['nodeId'] = node_id
        if backend_node_id:
            params['backendNodeId'] = backend_node_id
        if object_id:
            params['objectId'] = object_id
        return Command(method=DomMethod.FOCUS, params=params)

    @staticmethod
    def get_attributes(node_id: int) -> GetAttributesCommand:
        """返回指定节点的属性。

        属性信息在 Web 测试和自动化中至关重要，因为属性
        通常包含有关元素状态、行为和元数据的重要信息。
        该命令提供了一种访问元素所有属性的有效方法
        无需解析 HTML 或使用 JavaScript 评估。

        参数：
            node_id：要检索属性的节点的 ID。

        返回：
            命令：返回节点属性交错数组的 CDP 命令
                    名称和值 [name1, value1, name2, value2, ...]。"""
        params = GetAttributesParams(nodeId=node_id)
        return Command(method=DomMethod.GET_ATTRIBUTES, params=params)

    @staticmethod
    def get_box_model(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> GetBoxModelCommand:
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
        params = GetBoxModelParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.GET_BOX_MODEL, params=params)

    @staticmethod
    def get_document(
        depth: Optional[int] = None, pierce: Optional[bool] = None
    ) -> GetDocumentCommand:
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
        params = GetDocumentParams()
        if depth is not None:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.GET_DOCUMENT, params=params)

    @staticmethod
    def get_node_for_location(
        x: int,
        y: int,
        include_user_agent_shadow_dom: Optional[bool] = None,
        ignore_pointer_events_none: Optional[bool] = None,
    ) -> GetNodeForLocationCommand:
        """返回页面上给定位置的节点 ID。

        此命令对于弥合视觉/基于像素之间的差距特别有用
        信息和 DOM 结构。它允许您将屏幕坐标转换为
        实际的 DOM 元素，这对于创建检查工具或测试至关重要
        面向空间的交互。

        参数：
            x：相对于主框架视口的 X 坐标。
            y：相对于主框架视口的 Y 坐标。
            include_user_agent_shadow_dom：是否在用户代理影子根中包含节点。
            ignore_pointer_events_none：是否忽略pointer-events:none和测试元素
                                       在他们下面。

        返回：
            Command：CDP命令，返回给定位置的节点，包括
                   框架信息（如果可用）。"""
        params = GetNodeForLocationParams(x=x, y=y)
        if include_user_agent_shadow_dom is not None:
            params['includeUserAgentShadowDOM'] = include_user_agent_shadow_dom
        if ignore_pointer_events_none is not None:
            params['ignorePointerEventsNone'] = ignore_pointer_events_none
        return Command(method=DomMethod.GET_NODE_FOR_LOCATION, params=params)

    @staticmethod
    def get_outer_html(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> GetOuterHTMLCommand:
        """返回节点的 HTML 标记，包括节点本身及其所有子节点。

        此命令提供了一种访问完整 HTML 表示的方法
        元素，当您需要提取、分析或验证时，它很有价值
        HTML 内容。它比仅仅获取文本内容更全面
        保留完整的标记结构，包括标签、属性和子元素。

        参数：
            node_id：节点的标识符。
            backend_node_id：后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。

        返回：
            命令：返回节点外部 HTML 标记的 CDP 命令。"""
        params = GetOuterHTMLParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.GET_OUTER_HTML, params=params)

    @staticmethod
    def hide_highlight() -> HideHighlightCommand:
        """隐藏任何 DOM 元素突出显示。

        此命令在多个元素的自动化工作流程中特别有用
        按顺序高亮显示，需要先清除之前的高亮显示
        继续进行下一个元素以避免视觉混乱或干扰。

        返回：
            命令：隐藏 DOM 元素高亮显示的 CDP 命令。"""
        return Command(method=DomMethod.HIDE_HIGHLIGHT)

    @staticmethod
    def highlight_node() -> HighlightNodeCommand:
        """突出显示 DOM 节点。

        在开发和调试会话期间突出显示节点特别有价值
        直观地确认选择器或坐标选择了哪些元素。

        返回：
            命令：突出显示 DOM 节点的 CDP 命令。"""
        return Command(method=DomMethod.HIGHLIGHT_NODE)

    @staticmethod
    def highlight_rect() -> HighlightRectCommand:
        """突出显示给定的矩形。

        与节点突出显示不同，矩形突出显示允许任意突出显示
        页面的区域，这对于突出显示计算区域或
        不直接对应 DOM 元素的区域。

        返回：
            命令：CDP命令突出显示矩形区域。"""
        return Command(method=DomMethod.HIGHLIGHT_RECT)

    @staticmethod
    def move_to(
        node_id: int,
        target_node_id: int,
        insert_before_node_id: Optional[int] = None,
    ) -> MoveToCommand:
        """将节点移动到新容器中，将其放置在给定锚点之前。

        该命令允许比简单属性或更复杂的 DOM 重组
        内容发生变化。当测试涉及以下内容的应用程序时，它特别有用
        重新排列元素，例如可排序列表、看板或拖放界面。

        参数：
            node_id：要移动的节点的 ID。
            target_node_id：要将移动的节点放入其中的元素的 ID。
            insert_before_node_id：删除此节点之前的节点（如果不存在，则移动的节点
                                 成为 target_node_id 的最后一个子节点）。

        返回：
            命令：CDP命令移动节点，返回移动节点的新id。"""
        params = MoveToParams(nodeId=node_id, targetNodeId=target_node_id)
        if insert_before_node_id is not None:
            params['insertBeforeNodeId'] = insert_before_node_id
        return Command(method=DomMethod.MOVE_TO, params=params)

    @staticmethod
    def query_selector(
        node_id: int,
        selector: str,
    ) -> QuerySelectorCommand:
        """在给定节点上执行 querySelector。

        该方法是元素定位最基本的工具之一，允许
        使用标准 CSS 选择器在 DOM 中查找元素。与 JavaScript 不同
        querySelector，这可以在任何节点（不仅仅是文档）上执行，从而启用
        页面特定部分内的范围搜索。

        参数：
            node_id：要查询的节点的 ID。
            选择器：CSS 选择器字符串。

        返回：
            命令：CDP 命令，返回与选择器匹配的第一个元素。"""
        params = QuerySelectorParams(nodeId=node_id, selector=selector)
        return Command(method=DomMethod.QUERY_SELECTOR, params=params)

    @staticmethod
    def query_selector_all(
        node_id: int,
        selector: str,
    ) -> QuerySelectorAllCommand:
        """在给定节点上执行 querySelectorAll。

        此方法通过返回所有匹配元素而不是仅仅返回来扩展 querySelector
        第一个。这对于需要处理多个元素的操作至关重要，
        例如从表格、列表或网格中提取数据，或验证正确的
        存在的元素数量。

        参数：
            node_id：要查询的节点的 ID。
            选择器：CSS 选择器字符串。

        返回：
            命令：CDP 命令，返回与选择器匹配的所有元素。"""
        params = QuerySelectorAllParams(nodeId=node_id, selector=selector)
        return Command(method=DomMethod.QUERY_SELECTOR_ALL, params=params)

    @staticmethod
    def remove_attribute(
        node_id: int,
        name: str,
    ) -> RemoveAttributeCommand:
        """从具有给定 id 的元素中删除具有给定名称的属性。

        该命令允许直接操作元素属性，而无需使用 JavaScript
        在页面上下文中。它对于测试元素在特定情况下的行为非常有用
        属性被删除或为特定测试条件准备元素。

        参数：
            node_id：要从中删除属性的元素的 ID。
            name：要删除的属性的名称。

        返回：
            命令：删除指定属性的CDP命令。"""
        params = RemoveAttributeParams(nodeId=node_id, name=name)
        return Command(method=DomMethod.REMOVE_ATTRIBUTE, params=params)

    @staticmethod
    def remove_node(node_id: int) -> RemoveNodeCommand:
        """删除具有给定 id 的节点。

        此命令允许直接删除 DOM 元素，这在以下情况下很有用：
        测试应用程序如何响应缺失元素或简化时
        重点测试场景的页面。

        参数：
            node_id：要删除的节点的 ID。

        返回：
            Command：删除指定节点的CDP命令。"""
        params = RemoveNodeParams(nodeId=node_id)
        return Command(method=DomMethod.REMOVE_NODE, params=params)

    @staticmethod
    def request_child_nodes(
        node_id: int,
        depth: Optional[int] = None,
        pierce: Optional[bool] = None,
    ) -> RequestChildNodesCommand:
        """请求将具有给定 id 的节点的子节点返回给调用者。

        该方法在处理大型 DOM 树时特别有用，因为它允许
        通过按需加载子项而不是加载来更有效地探索
        一次整棵树。子节点作为 setChildNodes 事件返回。

        参数：
            node_id：要获取子节点的节点的 ID。
            深度：应检索儿童的最大深度，
                  默认为 1。对整个子树使用 -1。
            pierce：是否应该遍历 iframe 和影子根。

        返回：
            Command：请求子节点的CDP命令。"""
        params = RequestChildNodesParams(nodeId=node_id)
        if depth is not None:
            params['depth'] = depth
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.REQUEST_CHILD_NODES, params=params)

    @staticmethod
    def request_node(
        object_id: str,
    ) -> RequestNodeCommand:
        """请求将节点发送给给定 JavaScript 节点对象引用的调用者。

        此方法弥合了页面上下文中的 JavaScript 对象与页面上下文中的 JavaScript 对象之间的差距。
        CDP 的节点表示系统，允许自动化处理以下元素
        可能只能作为 JavaScript 引用使用（例如，来自事件处理程序）。

        参数：
            object_id：要转换为 Node 的 JavaScript 对象 id。

        返回：
            命令：返回给定对象的节点 ID 的 CDP 命令。"""
        params = RequestNodeParams(objectId=object_id)
        return Command(method=DomMethod.REQUEST_NODE, params=params)

    @staticmethod
    def resolve_node(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_group: Optional[str] = None,
        execution_context_id: Optional[int] = None,
    ) -> ResolveNodeCommand:
        """解析给定 NodeId 或 BackendNodeId 的 JavaScript 节点对象。

        此方法提供了与 requestNode 相反的功能 - 而不是获取
        从 JavaScript 对象获取 CDP 节点，它从 CDP 节点获取 JavaScript 对象。
        这使得能够在通过 CDP 识别的节点上执行 JavaScript 操作。

        参数：
            node_id：要解析的节点的 ID。
            backend_node_id：要解析的节点的后端 id。
            object_group：符号组名，可用于释放多个对象。
            execution_context_id：解析节点的执行上下文。

        返回：
            命令：返回节点的 JavaScript 对象包装器的 CDP 命令。"""
        params = ResolveNodeParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_group is not None:
            params['objectGroup'] = object_group
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id
        return Command(method=DomMethod.RESOLVE_NODE, params=params)

    @staticmethod
    def scroll_into_view_if_needed(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        rect: Optional[Rect] = None,
    ) -> ScrollIntoViewIfNeededCommand:
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
        params = ScrollIntoViewIfNeededParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        if rect is not None:
            params['rect'] = rect
        return Command(method=DomMethod.SCROLL_INTO_VIEW_IF_NEEDED, params=params)

    @staticmethod
    def set_attributes_as_text(
        node_id: int,
        text: str,
        name: Optional[str] = None,
    ) -> SetAttributesAsTextCommand:
        """使用文本表示设置具有给定 id 的元素的属性。

        该命令允许比 set_attribute_value 更复杂的属性操作，
        因为它接受可以定义多个属性的文本表示
        或包含特殊格式。当尝试复制时它特别有用
        属性在 HTML 源代码中的确切定义方式。

        参数：
            node_id：要为其设置属性的元素的 ID。
            text：具有新属性值的文本。
            name：要替换为新文本值的属性名称。

        返回：
            命令：将属性设置为文本的 CDP 命令。"""
        params = SetAttributesAsTextParams(nodeId=node_id, text=text)
        if name is not None:
            params['name'] = name
        return Command(method=DomMethod.SET_ATTRIBUTES_AS_TEXT, params=params)

    @staticmethod
    def set_attribute_value(
        node_id: int,
        name: str,
        value: str,
    ) -> SetAttributeValueCommand:
        """设置具有给定 id 的元素的属性。

        此命令无需使用 JavaScript 即可直接控制元素属性，
        这对于测试应用程序如何响应属性更改或
        通过直接控制元素属性来设置特定的测试条件。

        参数：
            node_id：要为其设置属性的元素的 ID。
            名称：属性名称。
            value：属性值。

        返回：
            命令：用于设置属性值的 CDP 命令。"""
        params = SetAttributeValueParams(nodeId=node_id, name=name, value=value)
        return Command(method=DomMethod.SET_ATTRIBUTE_VALUE, params=params)

    @staticmethod
    def set_file_input_files(
        files: list[str],
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> SetFileInputFilesCommand:
        """设置给定文件输入元素的文件。

        该命令解决了最具挑战性的自动化问题之一：
        文件输入。它绕过了通常在单击时出现的操作系统级文件对话框
        文件输入，允许自动化测试以编程方式提供文件。

        参数：
            files：要设置的文件路径列表。
            node_id：节点的标识符。
            backend_node_id：后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。

        返回：
            命令：用于为文件输入元素设置文件的 CDP 命令。"""
        params = SetFileInputFilesParams(files=files)
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.SET_FILE_INPUT_FILES, params=params)

    @staticmethod
    def set_node_name(
        node_id: int,
        name: str,
    ) -> SetNodeNameCommand:
        """设置具有给定 id 的节点的节点名称。

        此命令允许更改元素的实际标签名称，这可能很有用
        用于测试应用程序如何处理不同类型的元素或测试
        语义 HTML 选择对可访问性和行为的影响。

        参数：
            node_id：要为其设置名称的节点的 ID。
            name：新节点名称。

        返回：
            命令：CDP 命令，返回名称更改后的新节点 ID。"""
        params = SetNodeNameParams(nodeId=node_id, name=name)
        return Command(method=DomMethod.SET_NODE_NAME, params=params)

    @staticmethod
    def set_node_value(
        node_id: int,
        value: str,
    ) -> SetNodeValueCommand:
        """设置具有给定 id 的节点的节点值。

        该命令对于更新文本节点的内容特别有用
        注释，允许直接操作文本内容而不改变
        周围的 HTML 结构。

        参数：
            node_id：要为其设置值的节点的 ID。
            value：新节点值。

        返回：
            命令：用于设置节点值的 CDP 命令。"""
        params = SetNodeValueParams(nodeId=node_id, value=value)
        return Command(method=DomMethod.SET_NODE_VALUE, params=params)

    @staticmethod
    def set_outer_html(
        node_id: int,
        outer_html: str,
    ) -> SetOuterHTMLCommand:
        """设置节点 HTML 标记，替换现有标记。

        这是最强大的 DOM 操作命令之一，因为它完全允许
        用新的 HTML 替换元素及其所有子元素。这对于制作很有用
        对页面进行重大结构更改或测试应用程序如何处理
        动态插入的内容。

        参数：
            node_id：要为其设置外部 HTML 的节点的 ID。
            external_html：要设置的 HTML 标记。

        返回：
            命令：用于设置节点外部 HTML 的 CDP 命令。"""
        params = SetOuterHTMLParams(nodeId=node_id, outerHTML=outer_html)
        return Command(method=DomMethod.SET_OUTER_HTML, params=params)

    @staticmethod
    def collect_class_names_from_subtree(
        node_id: int,
    ) -> CollectClassNamesFromSubtreeCommand:
        """收集具有给定 id 的节点及其所有子节点的类名称。

        这种方法对于理解页面的样式景观很有价值，
        尤其是在可能存在多个 CSS 框架的复杂应用程序中
        在使用中或动态应用类的地方。

        参数：
            node_id：要为其收集类名的节点的 ID。

        返回：
            命令：CDP 命令，返回子树中所有唯一类名称的列表。"""
        params = CollectClassNamesFromSubtreeParams(nodeId=node_id)
        return Command(method=DomMethod.COLLECT_CLASS_NAMES_FROM_SUBTREE, params=params)

    @staticmethod
    def copy_to(
        node_id: int,
        target_node_id: int,
        insert_before_node_id: Optional[int] = None,
    ) -> CopyToCommand:
        """创建指定节点的深层副本并将其放入目标容器中。

        与 move_to 不同，此命令创建节点的副本，保持原始节点不变。
        当您想要复制内容而不是移动内容时（例如当
        测试同一组件的多个实例的行为方式。

        参数：
            node_id：要复制的节点的 ID。
            target_node_id：要将副本放入的元素的 ID。
            insert_before_node_id：删除此节点之前的副本（如果不存在，则该副本将变为
                                 target_node_id 的最后一个子节点）。

        返回：
            命令：返回新副本 ID 的 CDP 命令。"""
        params = CopyToParams(nodeId=node_id, targetNodeId=target_node_id)
        if insert_before_node_id is not None:
            params['insertBeforeNodeId'] = insert_before_node_id
        return Command(method=DomMethod.COPY_TO, params=params)

    @staticmethod
    def discard_search_results(
        search_id: str,
    ) -> DiscardSearchResultsCommand:
        """丢弃具有给定 ID 的会话的搜索结果。

        此方法有助于在执行多次搜索时管理资源
        一个会话，允许显式清理不再需要的搜索结果。

        参数：
            search_id：唯一的搜索会话标识符。

        返回：
            命令：CDP 命令丢弃搜索结果。"""
        params = DiscardSearchResultsParams(searchId=search_id)
        return Command(method=DomMethod.DISCARD_SEARCH_RESULTS, params=params)

    @staticmethod
    def get_anchor_element(
        node_id: int,
        anchor_specifier: Optional[str] = None,
    ) -> GetAnchorElementCommand:
        """查找作为给定节点的锚元素的最近祖先节点。

        当处理链接内的内容或需要时，此方法非常有用
        查找文本或其他元素的封闭链接元素。这在某些情况下有帮助
        您可以在其中找到文本，但需要找到它周围的实际链接。

        参数：
            node_id：要搜索周围锚点的节点的 ID。
            anchor_specifier：锚标记属性的可选说明符。

        返回：
            Command：返回锚元素节点信息的CDP命令。"""
        params = GetAnchorElementParams(nodeId=node_id)
        if anchor_specifier is not None:
            params['anchorSpecifier'] = anchor_specifier
        return Command(method=DomMethod.GET_ANCHOR_ELEMENT, params=params)

    @staticmethod
    def get_container_for_node(
        node_id: int,
        container_name: Optional[str] = None,
        physical_axes: Optional['PhysicalAxes'] = None,
        logical_axes: Optional['LogicalAxes'] = None,
        queries_scroll_state: Optional[bool] = None,
    ) -> GetContainerForNodeCommand:
        """根据指定参数查找给定节点的包含元素。

        这种方法有助于理解元素的结构和布局上下文，
        特别是在使用 CSS 功能（如 Flexbox、网格）的复杂布局中，或者当
        处理可滚动容器。

        参数：
            node_id：要查找容器的节点的 ID。
            container_name：要查找的容器的名称（例如，“scrollable”、“flex”）。
            physical_axes：要考虑的物理轴（水平、垂直、两者）。
            逻辑轴：要考虑的逻辑轴（内联轴、块轴、两者）。
            querys_scroll_state：是否查询滚动状态。

        返回：
            命令：返回有关包含元素的信息的 CDP 命令。"""
        params = GetContainerForNodeParams(nodeId=node_id)
        if container_name is not None:
            params['containerName'] = container_name
        if physical_axes is not None:
            params['physicalAxes'] = physical_axes
        if logical_axes is not None:
            params['logicalAxes'] = logical_axes
        if queries_scroll_state is not None:
            params['queriesScrollState'] = queries_scroll_state
        return Command(method=DomMethod.GET_CONTAINER_FOR_NODE, params=params)

    @staticmethod
    def get_content_quads(
        node_id: Optional[int] = None,
        backend_node_id: Optional[int] = None,
        object_id: Optional[str] = None,
    ) -> GetContentQuadsCommand:
        """返回描述页面上节点位置的四边形。

        此方法提供有关元素位置的详细几何信息
        在页面上，考虑任何转换、旋转或其他 CSS 效果。
        对于复杂的布局，这比 getBoxModel 更精确。

        参数：
            node_id：节点的标识符。
            backend_node_id：后端节点的标识符。
            object_id：节点包装器的 JavaScript 对象 ID。

        返回：
            命令：CDP 命令，返回描述节点位置的四边形。"""
        params = GetContentQuadsParams()
        if node_id is not None:
            params['nodeId'] = node_id
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        if object_id is not None:
            params['objectId'] = object_id
        return Command(method=DomMethod.GET_CONTENT_QUADS, params=params)

    @staticmethod
    def get_detached_dom_nodes() -> GetDetachedDomNodesCommand:
        """返回有关分离的 DOM 树元素的信息。

        此方法主要用于调试与 DOM 相关的内存问题，
        作为分离的 DOM 节点（文档中不再存在但仍被引用的节点）
        JavaScript）是 Web 应用程序中内存泄漏的常见原因。

        返回：
            命令：CDP 命令，返回有关分离的 DOM 节点的信息。"""
        return Command(method=DomMethod.GET_DETACHED_DOM_NODES)

    @staticmethod
    def get_element_by_relation(
        node_id: int,
        relation: RelationType,
    ) -> GetElementByRelationCommand:
        """以指定方式检索与给定元素相关的元素。

        此方法提供了一种根据元素与其他元素的关系来查找元素的方法
        元素，例如在给定元素之后查找下一个可聚焦元素。这是
        对于模拟键盘导航或分析元素关系很有用。

        参数：
            node_id：参考节点的Id。
            关系：关系类型（例如，nextSibling、previousSibling、firstChild）。

        返回：
            Command：返回相关元素节点的CDP命令。"""
        params = GetElementByRelationParams(nodeId=node_id, relation=relation)
        return Command(method=DomMethod.GET_ELEMENT_BY_RELATION, params=params)

    @staticmethod
    def get_file_info(
        object_id: str,
    ) -> GetFileInfoCommand:
        """返回给定 File 对象的文件信息。

        当使用文件输入和文件 API 时，此方法非常有用，提供
        访问文件元数据，例如所选文件的名称、大小和 MIME 类型
        文件输入元素或以编程方式创建。

        参数：
            object_id：要获取信息的 File 对象的 JavaScript 对象 ID。

        返回：
            Command：返回文件信息的CDP命令。"""
        params = GetFileInfoParams(objectId=object_id)
        return Command(method=DomMethod.GET_FILE_INFO, params=params)

    @staticmethod
    def get_frame_owner(
        frame_id: str,
    ) -> GetFrameOwnerCommand:
        """返回拥有给定框架的 iframe 元素。

        在处理包含 iframe 的页面时，此方法至关重要，因为它
        允许框架 ID（在 CDP 中使用）和实际 iframe 元素之间进行映射
        在父文档中。

        参数：
            frame_id：要获取其所有者元素的框架的 ID。

        返回：
            命令：返回帧所有者元素的 CDP 命令。"""
        params = GetFrameOwnerParams(frameId=frame_id)
        return Command(method=DomMethod.GET_FRAME_OWNER, params=params)

    @staticmethod
    def get_nodes_for_subtree_by_style(
        node_id: int,
        computed_styles: list[CSSComputedStyleProperty],
        pierce: Optional[bool] = None,
    ) -> GetNodesForSubtreeByStyleCommand:
        """在子树中查找具有给定计算样式的节点。

        此方法允许根据计算的样式查找元素，而不仅仅是
        结构或属性。这对于测试页面的视觉方面非常有用，或者
        用于查找符合特定视觉标准的元素。

        参数：
            node_id：开始搜索的节点。
            Computed_styles：要匹配的计算样式属性列表。
            pierce：是否应该遍历 iframe 和影子根。

        返回：
            命令：返回与指定样式匹配的节点的 CDP 命令。"""
        params = GetNodesForSubtreeByStyleParams(nodeId=node_id, computedStyles=computed_styles)
        if pierce is not None:
            params['pierce'] = pierce
        return Command(method=DomMethod.GET_NODES_FOR_SUBTREE_BY_STYLE, params=params)

    @staticmethod
    def get_node_stack_traces(
        node_id: int,
    ) -> GetNodeStackTracesCommand:
        """获取与特定节点关联的堆栈跟踪。

        此方法对于调试非常强大，因为它揭示了 JavaScript 执行路径
        这导致了特定 DOM 元素的创建，帮助开发人员理解
        他们的代码和生成的 DOM 结构之间的关系。

        参数：
            node_id：要获取堆栈跟踪的节点的 ID。

        返回：
            命令：CDP 命令，返回与节点相关的堆栈跟踪。"""
        params = GetNodeStackTracesParams(nodeId=node_id)
        return Command(method=DomMethod.GET_NODE_STACK_TRACES, params=params)

    @staticmethod
    def get_querying_descendants_for_container(
        node_id: int,
    ) -> GetQueryingDescendantsForContainerCommand:
        """返回容器的查询后代。

        此方法对于使用 CSS 容器查询特别有用，有助于
        识别哪些后代元素受特定影响或查询特定元素
        容器元素。

        参数：
            node_id：要查找其查询后代的容器节点的 ID。

        返回：
            命令：返回查询后代信息的CDP命令。"""
        params = GetQueryingDescendantsForContainerParams(nodeId=node_id)
        return Command(method=DomMethod.GET_QUERYING_DESCENDANTS_FOR_CONTAINER, params=params)

    @staticmethod
    def get_relayout_boundary(
        node_id: int,
    ) -> GetRelayoutBoundaryCommand:
        """返回给定节点的重新布局边界的根。

        此方法有助于通过识别边界来了解布局性能
        当特定元素发生变化时布局重新计算。这对于
        优化渲染性能。

        参数：
            node_id：要为其查找重新布局边界的节点的 ID。

        返回：
            命令：返回重新布局边界节点的 CDP 命令。"""
        params = GetRelayoutBoundaryParams(nodeId=node_id)
        return Command(method=DomMethod.GET_RELAYOUT_BOUNDARY, params=params)

    @staticmethod
    def get_search_results(
        search_id: str,
        from_index: int,
        to_index: int,
    ) -> GetSearchResultsCommand:
        """从搜索中返回从给定“fromIndex”到给定“toIndex”的搜索结果。

        该方法与performSearch结合使用来检索搜索结果
        批量处理，这在处理可能会出现的大型结果集时至关重要
        一次性全部转移效率低下。

        参数：
            search_id：performSearch 中的唯一搜索会话标识符。
            from_index：从中检索结果的起始索引。
            to_index：检索结果的结束索引（不包括）。

        返回：
            命令：返回请求的搜索结果的 CDP 命令。"""
        params = GetSearchResultsParams(searchId=search_id, fromIndex=from_index, toIndex=to_index)
        return Command(method=DomMethod.GET_SEARCH_RESULTS, params=params)

    @staticmethod
    def get_top_layer_elements() -> GetTopLayerElementsCommand:
        """返回文档中的所有顶层元素。

        此方法对于使用广泛使用的现代 Web UI 非常有价值
        覆盖层、模态框、下拉菜单和其他需要出现在上方的元素
        正常的文档流程。

        返回：
            Command：返回顶层元素信息的CDP命令。"""
        return Command(method=DomMethod.GET_TOP_LAYER_ELEMENTS)

    @staticmethod
    def mark_undoable_state() -> MarkUndoableStateCommand:
        """标记最后一个可撤消状态。

        此方法有助于管理 DOM 操作状态，允许创建
        可以使用撤消命令恢复到的保存点。这对于
        应将其视为一个单元的复杂 DOM 操作序列。

        返回：
            命令：CDP 命令将当前状态标记为可撤消。"""
        return Command(method=DomMethod.MARK_UNDOABLE_STATE)

    @staticmethod
    def perform_search(
        query: str,
        include_user_agent_shadow_dom: Optional[bool] = None,
    ) -> PerformSearchCommand:
        """在 DOM 树中搜索给定字符串。

        该方法发起跨 DOM 树的搜索，支持纯文本，
        CSS 选择器或 XPath 表达式。这是查找元素的有效方法
        或整个文档的内容而不知道确切的结构。

        参数：
            查询：纯文本或查询选择器或 XPath 搜索查询。
            include_user_agent_shadow_dom：如果为 True，则在搜索中包含用户代理影子 DOM。

        返回：
            命令：返回搜索结果标识符和计数的 CDP 命令。"""
        params = PerformSearchParams(query=query)
        if include_user_agent_shadow_dom is not None:
            params['includeUserAgentShadowDOM'] = include_user_agent_shadow_dom
        return Command(method=DomMethod.PERFORM_SEARCH, params=params)

    @staticmethod
    def push_node_by_path_to_frontend(
        path: str,
    ) -> PushNodeByPathToFrontendCommand:
        """请求将节点发送给给定路径的调用者。

        当节点 ID 不存在时，此方法提供了一种引用节点的替代方法
        可用，而是使用路径表达式。这在集成时很有用
        使用通过路径而不是 ID 来识别元素的系统。

        参数：
            path：专有格式的节点路径。

        返回：
            命令：返回节点的节点 ID 的 CDP 命令。"""
        params = PushNodeByPathToFrontendParams(path=path)
        return Command(method=DomMethod.PUSH_NODE_BY_PATH_TO_FRONTEND, params=params)

    @staticmethod
    def push_nodes_by_backend_ids_to_frontend(
        backend_node_ids: list[int],
    ) -> PushNodesByBackendIdsToFrontendCommand:
        """请求将一批节点发送给给定后端节点 ID 的调用者。

        当您有多个后端时，此方法可以实现高效的批处理
        节点ID，需要将其转换为前端节点ID以进行进一步的操作。

        参数：
            backend_node_ids：后端节点 ID 数组。

        返回：
            命令：返回节点 ID 数组的 CDP 命令。"""
        params = PushNodesByBackendIdsToFrontendParams(backendNodeIds=backend_node_ids)
        return Command(method=DomMethod.PUSH_NODES_BY_BACKEND_IDS_TO_FRONTEND, params=params)

    @staticmethod
    def redo() -> RedoCommand:
        """重新执行上次撤消的操作。

        此方法与 undo 和 markUndoableState 结合使用以提供
        DOM 操作的事务性方法，允许后退和
        通过一系列的变化。

        返回：
            命令：CDP 命令重做上次撤消的操作。"""
        return Command(method=DomMethod.REDO)

    @staticmethod
    def set_inspected_node(
        node_id: int,
    ) -> SetInspectedNodeCommand:
        """使控制台能够通过 $x 命令行 API 引用具有给定 id 的节点。

        此方法在自动化测试/脚本编写和手动控制台之间建立了一座桥梁
        交互，可以轻松引用控制台中的特定节点
        调试或实验。

        参数：
            node_id：可通过 $x 命令行 API 访问的 DOM 节点 ID。

        返回：
            命令：CDP命令设置检查节点。"""
        params = SetInspectedNodeParams(nodeId=node_id)
        return Command(method=DomMethod.SET_INSPECTED_NODE, params=params)

    @staticmethod
    def set_node_stack_traces_enabled(
        enable: bool,
    ) -> SetNodeStackTracesEnabledCommand:
        """设置是否应捕获节点的堆栈跟踪。

        此方法启用或禁用 DOM 节点时堆栈跟踪的收集
        创建，这对于调试复杂的应用程序非常有价值
        了解特定 DOM 元素的创建位置和原因。

        参数：
            启用：启用或禁用堆栈跟踪收集。

        返回：
            命令：用于启用或禁用节点堆栈跟踪的 CDP 命令。"""
        params = SetNodeStackTracesEnabledParams(enable=enable)
        return Command(method=DomMethod.SET_NODE_STACK_TRACES_ENABLED, params=params)

    @staticmethod
    def undo() -> UndoCommand:
        """撤消上次执行的操作。

        此方法与 redo 和 markUndoableState 结合使用以提供
        对 DOM 操作的事务控制，允许恢复更改
        当需要时。

        返回：
            命令：CDP 命令用于撤消上次执行的操作。"""
        return Command(method=DomMethod.UNDO)
