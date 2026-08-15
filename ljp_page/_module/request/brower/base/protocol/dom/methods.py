from enum import Enum

from typing_extensions import TypedDict

from ..base import Command, EmptyParams, EmptyResponse, Response
from .types import (
    BackendNodeId,
    BoxModel,
    CSSComputedStyleProperty,
    DetachedElementInfo,
    IncludeWhitespace,
    LogicalAxes,
    Node,
    NodeId,
    PhysicalAxes,
    Quad,
    Rect,
    RelationType,
)
from ..page.types import FrameId
from ..runtime.types import (
    ExecutionContextId,
    RemoteObject,
    RemoteObjectId,
    StackTrace,
)


class DomMethod(str, Enum):
    """DOM 域方法名称。"""

    COLLECT_CLASS_NAMES_FROM_SUBTREE = 'DOM.collectClassNamesFromSubtree'
    COPY_TO = 'DOM.copyTo'
    DESCRIBE_NODE = 'DOM.describeNode'
    DISABLE = 'DOM.disable'
    DISCARD_SEARCH_RESULTS = 'DOM.discardSearchResults'
    ENABLE = 'DOM.enable'
    FOCUS = 'DOM.focus'
    FORCE_SHOW_POPOVER = 'DOM.forceShowPopover'
    GET_ANCHOR_ELEMENT = 'DOM.getAnchorElement'
    GET_ATTRIBUTES = 'DOM.getAttributes'
    GET_BOX_MODEL = 'DOM.getBoxModel'
    GET_CONTAINER_FOR_NODE = 'DOM.getContainerForNode'
    GET_CONTENT_QUADS = 'DOM.getContentQuads'
    GET_DETACHED_DOM_NODES = 'DOM.getDetachedDomNodes'
    GET_DOCUMENT = 'DOM.getDocument'
    GET_ELEMENT_BY_RELATION = 'DOM.getElementByRelation'
    GET_FILE_INFO = 'DOM.getFileInfo'
    GET_FLATTENED_DOCUMENT = 'DOM.getFlattenedDocument'
    GET_FRAME_OWNER = 'DOM.getFrameOwner'
    GET_NODE_FOR_LOCATION = 'DOM.getNodeForLocation'
    GET_NODE_STACK_TRACES = 'DOM.getNodeStackTraces'
    GET_NODES_FOR_SUBTREE_BY_STYLE = 'DOM.getNodesForSubtreeByStyle'
    GET_OUTER_HTML = 'DOM.getOuterHTML'
    GET_QUERYING_DESCENDANTS_FOR_CONTAINER = 'DOM.getQueryingDescendantsForContainer'
    GET_RELAYOUT_BOUNDARY = 'DOM.getRelayoutBoundary'
    GET_SEARCH_RESULTS = 'DOM.getSearchResults'
    GET_TOP_LAYER_ELEMENTS = 'DOM.getTopLayerElements'
    HIDE_HIGHLIGHT = 'DOM.hideHighlight'
    HIGHLIGHT_NODE = 'DOM.highlightNode'
    HIGHLIGHT_RECT = 'DOM.highlightRect'
    MARK_UNDOABLE_STATE = 'DOM.markUndoableState'
    MOVE_TO = 'DOM.moveTo'
    PERFORM_SEARCH = 'DOM.performSearch'
    PUSH_NODE_BY_PATH_TO_FRONTEND = 'DOM.pushNodeByPathToFrontend'
    PUSH_NODES_BY_BACKEND_IDS_TO_FRONTEND = 'DOM.pushNodesByBackendIdsToFrontend'
    QUERY_SELECTOR = 'DOM.querySelector'
    QUERY_SELECTOR_ALL = 'DOM.querySelectorAll'
    REDO = 'DOM.redo'
    REMOVE_ATTRIBUTE = 'DOM.removeAttribute'
    REMOVE_NODE = 'DOM.removeNode'
    REQUEST_CHILD_NODES = 'DOM.requestChildNodes'
    REQUEST_NODE = 'DOM.requestNode'
    RESOLVE_NODE = 'DOM.resolveNode'
    SCROLL_INTO_VIEW_IF_NEEDED = 'DOM.scrollIntoViewIfNeeded'
    SET_ATTRIBUTE_VALUE = 'DOM.setAttributeValue'
    SET_ATTRIBUTES_AS_TEXT = 'DOM.setAttributesAsText'
    SET_FILE_INPUT_FILES = 'DOM.setFileInputFiles'
    SET_INSPECTED_NODE = 'DOM.setInspectedNode'
    SET_NODE_NAME = 'DOM.setNodeName'
    SET_NODE_STACK_TRACES_ENABLED = 'DOM.setNodeStackTracesEnabled'
    SET_NODE_VALUE = 'DOM.setNodeValue'
    SET_OUTER_HTML = 'DOM.setOuterHTML'
    UNDO = 'DOM.undo'


class CollectClassNamesFromSubtreeParams(TypedDict):
    """用于从子树收集类名的参数。"""

    nodeId: NodeId


class CopyToParams(TypedDict, total=False):
    """用于复制节点的参数。"""

    nodeId: NodeId
    targetNodeId: NodeId
    insertBeforeNodeId: NodeId


class DescribeNodeParams(TypedDict, total=False):
    """用于描述节点的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId
    depth: int
    pierce: bool


class ScrollIntoViewIfNeededParams(TypedDict, total=False):
    """如果需要，用于滚动到视图的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId
    rect: Rect


class DiscardSearchResultsParams(TypedDict):
    """用于丢弃搜索结果的参数。"""

    searchId: str


class EnableParams(TypedDict, total=False):
    """用于启用 DOM 代理的参数。"""

    includeWhitespace: IncludeWhitespace


class FocusParams(TypedDict, total=False):
    """用于聚焦元素的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class GetAttributesParams(TypedDict):
    """用于获取属性的参数。"""

    nodeId: NodeId


class GetBoxModelParams(TypedDict, total=False):
    """获取盒子模型的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class GetContentQuadsParams(TypedDict, total=False):
    """用于获取内容四边形的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class GetDocumentParams(TypedDict, total=False):
    """获取文档的参数。"""

    depth: int
    pierce: bool


class GetFlattenedDocumentParams(TypedDict, total=False):
    """用于获取展平文档的参数。"""

    depth: int
    pierce: bool


class GetNodesForSubtreeByStyleParams(TypedDict, total=False):
    """用于按样式获取节点的参数。"""

    nodeId: NodeId
    computedStyles: list[CSSComputedStyleProperty]
    pierce: bool


class GetNodeForLocationParams(TypedDict, total=False):
    """用于获取节点位置的参数。"""

    x: int
    y: int
    includeUserAgentShadowDOM: bool
    ignorePointerEventsNone: bool


class GetOuterHTMLParams(TypedDict, total=False):
    """用于获取外部 HTML 的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId
    includeShadowDOM: bool


class GetRelayoutBoundaryParams(TypedDict):
    """用于获取重新布局边界的参数。"""

    nodeId: NodeId


class GetSearchResultsParams(TypedDict):
    """用于获取搜索结果的参数。"""

    searchId: str
    fromIndex: int
    toIndex: int


class MoveToParams(TypedDict, total=False):
    """用于移动节点的参数。"""

    nodeId: NodeId
    targetNodeId: NodeId
    insertBeforeNodeId: NodeId


class PerformSearchParams(TypedDict, total=False):
    """用于执行搜索的参数。"""

    query: str
    includeUserAgentShadowDOM: bool


class PushNodeByPathToFrontendParams(TypedDict):
    """用于按路径将节点推送到前端的参数。"""

    path: str


class PushNodesByBackendIdsToFrontendParams(TypedDict):
    """用于通过后端ID将节点推送到前端的参数。"""

    backendNodeIds: list[BackendNodeId]


class QuerySelectorParams(TypedDict):
    """查询选择器的参数。"""

    nodeId: NodeId
    selector: str


class QuerySelectorAllParams(TypedDict):
    """querySelectorAll 的参数。"""

    nodeId: NodeId
    selector: str


class GetElementByRelationParams(TypedDict):
    """通过关系获取元素的参数。"""

    nodeId: NodeId
    relation: RelationType


class RemoveAttributeParams(TypedDict):
    """用于删除属性的参数。"""

    nodeId: NodeId
    name: str


class RemoveNodeParams(TypedDict):
    """用于删除节点的参数。"""

    nodeId: NodeId


class RequestChildNodesParams(TypedDict, total=False):
    """请求子节点的参数。"""

    nodeId: NodeId
    depth: int
    pierce: bool


class RequestNodeParams(TypedDict):
    """请求节点的参数。"""

    objectId: RemoteObjectId


class ResolveNodeParams(TypedDict, total=False):
    """解析节点的参数。"""

    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectGroup: str
    executionContextId: ExecutionContextId


class SetAttributeValueParams(TypedDict):
    """用于设置属性值的参数。"""

    nodeId: NodeId
    name: str
    value: str


class SetAttributesAsTextParams(TypedDict, total=False):
    """用于将属性设置为文本的参数。"""

    nodeId: NodeId
    text: str
    name: str


class SetFileInputFilesParams(TypedDict, total=False):
    """用于设置文件输入文件的参数。"""

    files: list[str]
    nodeId: NodeId
    backendNodeId: BackendNodeId
    objectId: RemoteObjectId


class SetNodeStackTracesEnabledParams(TypedDict):
    """已启用用于设置节点堆栈跟踪的参数。"""

    enable: bool


class GetNodeStackTracesParams(TypedDict):
    """用于获取节点堆栈跟踪的参数。"""

    nodeId: NodeId


class GetFileInfoParams(TypedDict):
    """用于获取文件信息的参数。"""

    objectId: RemoteObjectId


class SetInspectedNodeParams(TypedDict):
    """用于设置检查节点的参数。"""

    nodeId: NodeId


class SetNodeNameParams(TypedDict):
    """用于设置节点名称的参数。"""

    nodeId: NodeId
    name: str


class SetNodeValueParams(TypedDict):
    """用于设置节点值的参数。"""

    nodeId: NodeId
    value: str


class SetOuterHTMLParams(TypedDict):
    """用于设置外部 HTML 的参数。"""

    nodeId: NodeId
    outerHTML: str


class GetFrameOwnerParams(TypedDict):
    """用于获取帧所有者的参数。"""

    frameId: FrameId


class GetContainerForNodeParams(TypedDict, total=False):
    """用于获取节点容器的参数。"""

    nodeId: NodeId
    containerName: str
    physicalAxes: PhysicalAxes
    logicalAxes: LogicalAxes
    queriesScrollState: bool
    queriesAnchored: bool


class GetQueryingDescendantsForContainerParams(TypedDict):
    """用于获取查询容器后代的参数。"""

    nodeId: NodeId


class GetAnchorElementParams(TypedDict, total=False):
    """用于获取锚元素的参数。"""

    nodeId: NodeId
    anchorSpecifier: str


class ForceShowPopoverParams(TypedDict):
    """用于强制显示弹出窗口的参数。"""

    nodeId: NodeId
    enable: bool


#结果类型
class CollectClassNamesFromSubtreeResult(TypedDict):
    """collectClassNamesFromSubtree 命令的结果。"""

    classNames: list[str]


class CopyToResult(TypedDict):
    """copyTo 命令的结果。"""

    nodeId: NodeId


class DescribeNodeResult(TypedDict):
    """描述节点命令的结果。"""

    node: Node


class GetAttributesResult(TypedDict):
    """getAttributes 命令的结果。"""

    attributes: list[str]


class GetBoxModelResult(TypedDict):
    """getBoxModel 命令的结果。"""

    model: BoxModel


class GetContentQuadsResult(TypedDict):
    """getContentQuads 命令的结果。"""

    quads: list[Quad]


class GetDocumentResult(TypedDict):
    """getDocument 命令的结果。"""

    root: Node


class GetFlattenedDocumentResult(TypedDict):
    """getFlattenedDocument 命令的结果。"""

    nodes: list[Node]


class GetNodesForSubtreeByStyleResult(TypedDict):
    """getNodesForSubtreeByStyle 命令的结果。"""

    nodeIds: list[NodeId]


class GetNodeForLocationResult(TypedDict, total=False):
    """getNodeForLocation 命令的结果。"""

    backendNodeId: BackendNodeId
    frameId: FrameId
    nodeId: NodeId


class GetOuterHTMLResult(TypedDict):
    """getOuterHTML 命令的结果。"""

    outerHTML: str


class GetRelayoutBoundaryResult(TypedDict):
    """getRelayoutBoundary 命令的结果。"""

    nodeId: NodeId


class GetSearchResultsResult(TypedDict):
    """getSearchResults 命令的结果。"""

    nodeIds: list[NodeId]


class GetTopLayerElementsResult(TypedDict):
    """getTopLayerElements 命令的结果。"""

    nodeIds: list[NodeId]


class GetElementByRelationResult(TypedDict):
    """getElementByRelation 命令的结果。"""

    nodeId: NodeId


class MoveToResult(TypedDict):
    """moveTo 命令的结果。"""

    nodeId: NodeId


class PerformSearchResult(TypedDict):
    """PerformSearch 命令的结果。"""

    searchId: str
    resultCount: int


class PushNodeByPathToFrontendResult(TypedDict):
    """PushNodeByPathToFrontend 命令的结果。"""

    nodeId: NodeId


class PushNodesByBackendIdsToFrontendResult(TypedDict):
    """PushNodesByBackendIdsToFrontend 命令的结果。"""

    nodeIds: list[NodeId]


class QuerySelectorResult(TypedDict):
    """querySelector 命令的结果。"""

    nodeId: NodeId


class QuerySelectorAllResult(TypedDict):
    """querySelectorAll 命令的结果。"""

    nodeIds: list[NodeId]


class RequestNodeResult(TypedDict):
    """requestNode 命令的结果。"""

    nodeId: NodeId


class ResolveNodeResult(TypedDict):
    """resolveNode 命令的结果。"""

    object: RemoteObject


class SetNodeNameResult(TypedDict):
    """setNodeName 命令的结果。"""

    nodeId: NodeId


class GetNodeStackTracesResult(TypedDict, total=False):
    """getNodeStackTraces 命令的结果。"""

    creation: StackTrace


class GetFileInfoResult(TypedDict):
    """getFileInfo 命令的结果。"""

    path: str


class GetDetachedDomNodesResult(TypedDict):
    """getDetachedDomNodes 命令的结果。"""

    detachedNodes: list[DetachedElementInfo]


class GetFrameOwnerResult(TypedDict, total=False):
    """getFrameOwner 命令的结果。"""

    backendNodeId: BackendNodeId
    nodeId: NodeId


class GetContainerForNodeResult(TypedDict, total=False):
    """getContainerForNode 命令的结果。"""

    nodeId: NodeId


class GetQueryingDescendantsForContainerResult(TypedDict):
    """getQueryingDescendantsForContainer 命令的结果。"""

    nodeIds: list[NodeId]


class GetAnchorElementResult(TypedDict):
    """getAnchorElement 命令的结果。"""

    nodeId: NodeId


class ForceShowPopoverResult(TypedDict):
    """forceShowPopover 命令的结果。"""

    nodeIds: list[NodeId]


#响应类型
CollectClassNamesFromSubtreeResponse = Response[CollectClassNamesFromSubtreeResult]
CopyToResponse = Response[CopyToResult]
DescribeNodeResponse = Response[DescribeNodeResult]
GetAttributesResponse = Response[GetAttributesResult]
GetBoxModelResponse = Response[GetBoxModelResult]
GetContentQuadsResponse = Response[GetContentQuadsResult]
GetDocumentResponse = Response[GetDocumentResult]
GetFlattenedDocumentResponse = Response[GetFlattenedDocumentResult]
GetNodesForSubtreeByStyleResponse = Response[GetNodesForSubtreeByStyleResult]
GetNodeForLocationResponse = Response[GetNodeForLocationResult]
GetOuterHTMLResponse = Response[GetOuterHTMLResult]
GetRelayoutBoundaryResponse = Response[GetRelayoutBoundaryResult]
GetSearchResultsResponse = Response[GetSearchResultsResult]
GetTopLayerElementsResponse = Response[GetTopLayerElementsResult]
GetElementByRelationResponse = Response[GetElementByRelationResult]
MoveToResponse = Response[MoveToResult]
PerformSearchResponse = Response[PerformSearchResult]
PushNodeByPathToFrontendResponse = Response[PushNodeByPathToFrontendResult]
PushNodesByBackendIdsToFrontendResponse = Response[PushNodesByBackendIdsToFrontendResult]
QuerySelectorResponse = Response[QuerySelectorResult]
QuerySelectorAllResponse = Response[QuerySelectorAllResult]
RequestNodeResponse = Response[RequestNodeResult]
ResolveNodeResponse = Response[ResolveNodeResult]
SetNodeNameResponse = Response[SetNodeNameResult]
GetNodeStackTracesResponse = Response[GetNodeStackTracesResult]
GetFileInfoResponse = Response[GetFileInfoResult]
GetDetachedDomNodesResponse = Response[GetDetachedDomNodesResult]
GetFrameOwnerResponse = Response[GetFrameOwnerResult]
GetContainerForNodeResponse = Response[GetContainerForNodeResult]
GetQueryingDescendantsForContainerResponse = Response[GetQueryingDescendantsForContainerResult]
GetAnchorElementResponse = Response[GetAnchorElementResult]
ForceShowPopoverResponse = Response[ForceShowPopoverResult]


#命令类型
CollectClassNamesFromSubtreeCommand = Command[
    CollectClassNamesFromSubtreeParams, CollectClassNamesFromSubtreeResponse
]
CopyToCommand = Command[CopyToParams, CopyToResponse]
DescribeNodeCommand = Command[DescribeNodeParams, DescribeNodeResponse]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
DiscardSearchResultsCommand = Command[DiscardSearchResultsParams, Response[EmptyResponse]]
EnableCommand = Command[EnableParams, Response[EmptyResponse]]
FocusCommand = Command[FocusParams, Response[EmptyResponse]]
ForceShowPopoverCommand = Command[ForceShowPopoverParams, ForceShowPopoverResponse]
GetAnchorElementCommand = Command[GetAnchorElementParams, GetAnchorElementResponse]
GetAttributesCommand = Command[GetAttributesParams, GetAttributesResponse]
GetBoxModelCommand = Command[GetBoxModelParams, GetBoxModelResponse]
GetContainerForNodeCommand = Command[GetContainerForNodeParams, GetContainerForNodeResponse]
GetContentQuadsCommand = Command[GetContentQuadsParams, GetContentQuadsResponse]
GetDetachedDomNodesCommand = Command[EmptyParams, Response[GetDetachedDomNodesResponse]]
GetDocumentCommand = Command[GetDocumentParams, GetDocumentResponse]
GetElementByRelationCommand = Command[GetElementByRelationParams, GetElementByRelationResponse]
GetFileInfoCommand = Command[GetFileInfoParams, GetFileInfoResponse]
GetFlattenedDocumentCommand = Command[GetFlattenedDocumentParams, GetFlattenedDocumentResponse]
GetFrameOwnerCommand = Command[GetFrameOwnerParams, GetFrameOwnerResponse]
GetNodeForLocationCommand = Command[GetNodeForLocationParams, GetNodeForLocationResponse]
GetNodeStackTracesCommand = Command[GetNodeStackTracesParams, GetNodeStackTracesResponse]
GetNodesForSubtreeByStyleCommand = Command[
    GetNodesForSubtreeByStyleParams, GetNodesForSubtreeByStyleResponse
]
GetOuterHTMLCommand = Command[GetOuterHTMLParams, GetOuterHTMLResponse]
GetQueryingDescendantsForContainerCommand = Command[
    GetQueryingDescendantsForContainerParams, GetQueryingDescendantsForContainerResponse
]
GetRelayoutBoundaryCommand = Command[GetRelayoutBoundaryParams, GetRelayoutBoundaryResponse]
GetSearchResultsCommand = Command[GetSearchResultsParams, GetSearchResultsResponse]
GetTopLayerElementsCommand = Command[EmptyParams, GetTopLayerElementsResponse]
HideHighlightCommand = Command[EmptyParams, Response[EmptyResponse]]
HighlightNodeCommand = Command[EmptyParams, Response[EmptyResponse]]  #重定向到叠加层
HighlightRectCommand = Command[EmptyParams, Response[EmptyResponse]]  #重定向到叠加层
MarkUndoableStateCommand = Command[EmptyParams, Response[EmptyResponse]]
MoveToCommand = Command[MoveToParams, MoveToResponse]
PerformSearchCommand = Command[PerformSearchParams, PerformSearchResponse]
PushNodeByPathToFrontendCommand = Command[
    PushNodeByPathToFrontendParams, PushNodeByPathToFrontendResponse
]
PushNodesByBackendIdsToFrontendCommand = Command[
    PushNodesByBackendIdsToFrontendParams, PushNodesByBackendIdsToFrontendResponse
]
QuerySelectorCommand = Command[QuerySelectorParams, QuerySelectorResponse]
QuerySelectorAllCommand = Command[QuerySelectorAllParams, QuerySelectorAllResponse]
RedoCommand = Command[EmptyParams, Response[EmptyResponse]]
RemoveAttributeCommand = Command[RemoveAttributeParams, Response[EmptyResponse]]
RemoveNodeCommand = Command[RemoveNodeParams, Response[EmptyResponse]]
RequestChildNodesCommand = Command[RequestChildNodesParams, Response[EmptyResponse]]
RequestNodeCommand = Command[RequestNodeParams, RequestNodeResponse]
ResolveNodeCommand = Command[ResolveNodeParams, ResolveNodeResponse]
ScrollIntoViewIfNeededCommand = Command[ScrollIntoViewIfNeededParams, Response[EmptyResponse]]
SetAttributeValueCommand = Command[SetAttributeValueParams, Response[EmptyResponse]]
SetAttributesAsTextCommand = Command[SetAttributesAsTextParams, Response[EmptyResponse]]
SetFileInputFilesCommand = Command[SetFileInputFilesParams, Response[EmptyResponse]]
SetInspectedNodeCommand = Command[SetInspectedNodeParams, Response[EmptyResponse]]
SetNodeNameCommand = Command[SetNodeNameParams, SetNodeNameResponse]
SetNodeStackTracesEnabledCommand = Command[SetNodeStackTracesEnabledParams, Response[EmptyResponse]]
SetNodeValueCommand = Command[SetNodeValueParams, Response[EmptyResponse]]
SetOuterHTMLCommand = Command[SetOuterHTMLParams, Response[EmptyResponse]]
UndoCommand = Command[EmptyParams, Response[EmptyResponse]]
