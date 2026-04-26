from enum import Enum
from typing import Annotated, Any

from typing_extensions import TypedDict

NodeId = int
BackendNodeId = int
Quad = Annotated[list[float], 'Format: [x1, y1, x2, y2, x3, y3, x4, y4]']


class PseudoType(str, Enum):
    """伪元素类型。"""

    FIRST_LINE = 'first-line'
    FIRST_LETTER = 'first-letter'
    CHECKMARK = 'checkmark'
    BEFORE = 'before'
    AFTER = 'after'
    PICKER_ICON = 'picker-icon'
    MARKER = 'marker'
    BACKDROP = 'backdrop'
    COLUMN = 'column'
    SELECTION = 'selection'
    SEARCH_TEXT = 'search-text'
    TARGET_TEXT = 'target-text'
    SPELLING_ERROR = 'spelling-error'
    GRAMMAR_ERROR = 'grammar-error'
    HIGHLIGHT = 'highlight'
    FIRST_LINE_INHERITED = 'first-line-inherited'
    SCROLL_MARKER = 'scroll-marker'
    SCROLL_MARKER_GROUP = 'scroll-marker-group'
    SCROLL_BUTTON = 'scroll-button'
    SCROLLBAR = 'scrollbar'
    SCROLLBAR_THUMB = 'scrollbar-thumb'
    SCROLLBAR_BUTTON = 'scrollbar-button'
    SCROLLBAR_TRACK = 'scrollbar-track'
    SCROLLBAR_TRACK_PIECE = 'scrollbar-track-piece'
    SCROLLBAR_CORNER = 'scrollbar-corner'
    RESIZER = 'resizer'
    INPUT_LIST_BUTTON = 'input-list-button'
    VIEW_TRANSITION = 'view-transition'
    VIEW_TRANSITION_GROUP = 'view-transition-group'
    VIEW_TRANSITION_IMAGE_PAIR = 'view-transition-image-pair'
    VIEW_TRANSITION_GROUP_CHILDREN = 'view-transition-group-children'
    VIEW_TRANSITION_OLD = 'view-transition-old'
    VIEW_TRANSITION_NEW = 'view-transition-new'
    PLACEHOLDER = 'placeholder'
    FILE_SELECTOR_BUTTON = 'file-selector-button'
    DETAILS_CONTENT = 'details-content'
    PICKER = 'picker'
    PERMISSION_ICON = 'permission-icon'


class ShadowRootType(str, Enum):
    """影根型。"""

    USER_AGENT = 'user-agent'
    OPEN = 'open'
    CLOSED = 'closed'


class CompatibilityMode(str, Enum):
    """文档兼容模式。"""

    QUIRKS_MODE = 'QuirksMode'
    LIMITED_QUIRKS_MODE = 'LimitedQuirksMode'
    NO_QUIRKS_MODE = 'NoQuirksMode'


class PhysicalAxes(str, Enum):
    """ContainerSelector 物理轴。"""

    HORIZONTAL = 'Horizontal'
    VERTICAL = 'Vertical'
    BOTH = 'Both'


class LogicalAxes(str, Enum):
    """ContainerSelector 逻辑轴。"""

    INLINE = 'Inline'
    BLOCK = 'Block'
    BOTH = 'Both'


class ScrollOrientation(str, Enum):
    """物理滚动方向。"""

    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'


class IncludeWhitespace(str, Enum):
    """包括空白选项。"""

    NONE = 'none'
    ALL = 'all'


class RelationType(str, Enum):
    """元素关系类型。"""

    POPOVER_TARGET = 'PopoverTarget'
    INTEREST_TARGET = 'InterestTarget'
    COMMAND_FOR = 'CommandFor'


class BackendNode(TypedDict):
    """具有友好名称的后端节点。"""

    nodeType: int
    nodeName: str
    backendNodeId: BackendNodeId


class Node(TypedDict, total=False):
    """DOM 交互是通过代表实际 DOM 的镜像对象来实现的
    节点。"""

    nodeId: NodeId
    parentId: NodeId
    backendNodeId: BackendNodeId
    nodeType: int
    nodeName: str
    localName: str
    nodeValue: str
    childNodeCount: int
    children: list['Node']
    attributes: list[str]
    documentURL: str
    baseURL: str
    publicId: str
    systemId: str
    internalSubset: str
    xmlVersion: str
    name: str
    value: str
    pseudoType: PseudoType
    pseudoIdentifier: str
    shadowRootType: ShadowRootType
    frameId: str
    contentDocument: 'Node'
    shadowRoots: list['Node']
    templateContent: 'Node'
    pseudoElements: list['Node']
    importedDocument: 'Node'  #已弃用
    distributedNodes: list[BackendNode]
    isSVG: bool
    compatibilityMode: CompatibilityMode
    assignedSlot: BackendNode
    isScrollable: bool


class DetachedElementInfo(TypedDict):
    """用于保存分离树的顶级节点及其保留数组的结构
    后代。"""

    treeNode: Node
    retainedNodeIds: list[NodeId]


class RGBA(TypedDict, total=False):
    """保存 RGBA 颜色的结构。"""

    r: int  #红色分量，范围为 [0-255]。
    g: int  #绿色分量，范围为 [0-255]。
    b: int  #蓝色分量，范围为 [0-255]。
    a: float  #alpha 分量，范围为 [0-1]（默认值：1）。


class BoxModel(TypedDict, total=False):
    """盒子模型。"""

    content: Quad
    padding: Quad
    border: Quad
    margin: Quad
    width: int
    height: int
    shapeOutside: 'ShapeOutsideInfo'


class ShapeOutsideInfo(TypedDict):
    """CSS 形状外部细节。"""

    bounds: Quad
    shape: list[Any]
    marginShape: list[Any]


class Rect(TypedDict):
    """矩形。"""

    x: float
    y: float
    width: float
    height: float


class CSSComputedStyleProperty(TypedDict):
    """CSS 计算样式属性。"""

    name: str
    value: str
