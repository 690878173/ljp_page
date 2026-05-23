from enum import Enum
from typing import Any

from typing_extensions import NotRequired, TypedDict

AXNodeId = str


class AXValueType(str, Enum):
    """可能的属性类型的枚举。"""

    BOOLEAN = 'boolean'
    TRISTATE = 'tristate'
    BOOLEAN_OR_UNDEFINED = 'booleanOrUndefined'
    IDREF = 'idref'
    IDREF_LIST = 'idrefList'
    INTEGER = 'integer'
    NODE = 'node'
    NODE_LIST = 'nodeList'
    NUMBER = 'number'
    STRING = 'string'
    COMPUTED_STRING = 'computedString'
    TOKEN = 'token'
    TOKEN_LIST = 'tokenList'
    DOM_RELATION = 'domRelation'
    ROLE = 'role'
    INTERNAL_ROLE = 'internalRole'
    VALUE_UNDEFINED = 'valueUndefined'


class AXValueSourceType(str, Enum):
    """可能的属性源的枚举。"""

    ATTRIBUTE = 'attribute'
    IMPLICIT = 'implicit'
    STYLE = 'style'
    CONTENTS = 'contents'
    PLACEHOLDER = 'placeholder'
    RELATED_ELEMENT = 'relatedElement'


class AXValueNativeSourceType(str, Enum):
    """可能的本机属性源的枚举。"""

    DESCRIPTION = 'description'
    FIGCAPTION = 'figcaption'
    LABEL = 'label'
    LABELFOR = 'labelfor'
    LABELWRAPPED = 'labelwrapped'
    LEGEND = 'legend'
    RUBYANNOTATION = 'rubyannotation'
    TABLECAPTION = 'tablecaption'
    TITLE = 'title'
    OTHER = 'other'


class AXPropertyName(str, Enum):
    """AXProperty 名称的值。

    请参阅 https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/#type-AXPropertyName"""

    #州
    BUSY = 'busy'
    DISABLED = 'disabled'
    EDITABLE = 'editable'
    FOCUSABLE = 'focusable'
    FOCUSED = 'focused'
    HIDDEN = 'hidden'
    HIDDEN_ROOT = 'hiddenRoot'
    INVALID = 'invalid'
    KEYSHORTCUTS = 'keyshortcuts'
    SETTABLE = 'settable'
    ROLEDESCRIPTION = 'roledescription'
    #活动区域属性
    LIVE = 'live'
    ATOMIC = 'atomic'
    RELEVANT = 'relevant'
    ROOT = 'root'
    #小部件属性
    AUTOCOMPLETE = 'autocomplete'
    HAS_POPUP = 'hasPopup'
    LEVEL = 'level'
    MULTISELECTABLE = 'multiselectable'
    ORIENTATION = 'orientation'
    MULTILINE = 'multiline'
    READONLY = 'readonly'
    REQUIRED = 'required'
    VALUEMIN = 'valuemin'
    VALUEMAX = 'valuemax'
    VALUETEXT = 'valuetext'
    #小部件状态
    CHECKED = 'checked'
    EXPANDED = 'expanded'
    MODAL = 'modal'
    PRESSED = 'pressed'
    SELECTED = 'selected'
    #关系属性
    ACTIVEDESCENDANT = 'activedescendant'
    CONTROLS = 'controls'
    DESCRIBEDBY = 'describedby'
    DETAILS = 'details'
    ERRORMESSAGE = 'errormessage'
    FLOWTO = 'flowto'
    LABELLEDBY = 'labelledby'
    OWNS = 'owns'
    #额外属性
    ACTIONS = 'actions'
    URL = 'url'
    #隐藏的原因
    ACTIVE_FULLSCREEN_ELEMENT = 'activeFullscreenElement'
    ANCESTOR_DISALLOWS_CHILD = 'ancestorDisallowsChild'
    ANCESTOR_IS_LEAF_NODE = 'ancestorIsLeafNode'
    ARIA_HIDDEN_ELEMENT = 'ariaHiddenElement'
    ARIA_HIDDEN_SUBTREE = 'ariaHiddenSubtree'
    DISPLAY_LOCK = 'displayLock'
    EMPTY_ALT = 'emptyAlt'
    FROM_SUBTREE_HTML = 'fromSubtreeHtml'
    HIDDEN_BY_CHILD_TREE = 'hiddenByChildTree'
    IGNORED_PARENT = 'ignoredParent'
    INLINE_TEXT_BOX = 'inlineTextBox'
    NOT_RENDERED = 'notRendered'
    NOT_VISIBLE = 'notVisible'
    POTENTIALLY_OFFSCREEN = 'potentiallyOffscreen'
    PRESENTATIONAL_ROLE = 'presentationalRole'
    ROLE_PRESENTATION = 'rolePresentation'
    ACTIVE_MODAL_DIALOG = 'activeModalDialog'
    ACTIVE_ARIA_MODAL_DIALOG = 'activeAriaModalDialog'
    EMPTY_TEXT = 'emptyText'
    INERT_ELEMENT = 'inertElement'
    INERT_SUBTREE = 'inertSubtree'
    LABEL_CONTAINER = 'labelContainer'
    LABEL_FOR = 'labelFor'
    PROBABLY_PRESENTATIONAL = 'probablyPresentational'
    INACTIVE_CAROUSEL_TAB_CONTENT = 'inactiveCarouselTabContent'
    UNINTERESTING = 'uninteresting'


class AXRelatedNode(TypedDict):
    """通过可访问性属性与当前节点相关的节点。"""

    backendDOMNodeId: int
    idref: NotRequired[str]
    text: NotRequired[str]


class AXValueSource(TypedDict):
    """计算 AX 属性的单一来源。"""

    type: AXValueSourceType
    value: NotRequired['AXValue']
    attribute: NotRequired[str]
    attributeValue: NotRequired['AXValue']
    superseded: NotRequired[bool]
    nativeSource: NotRequired[AXValueNativeSourceType]
    nativeSourceValue: NotRequired['AXValue']
    invalid: NotRequired[bool]
    invalidReason: NotRequired[str]


class AXValue(TypedDict):
    """单个计算的 AX 属性。"""

    type: AXValueType
    value: NotRequired[Any]
    relatedNodes: NotRequired[list[AXRelatedNode]]
    sources: NotRequired[list[AXValueSource]]


class AXProperty(TypedDict):
    """作为辅助功能属性的名称/值对。"""

    name: AXPropertyName
    value: AXValue


class AXNode(TypedDict):
    """可访问性树中的节点。"""

    nodeId: AXNodeId
    ignored: bool
    ignoredReasons: NotRequired[list[AXProperty]]
    role: NotRequired[AXValue]
    chromeRole: NotRequired[AXValue]
    name: NotRequired[AXValue]
    description: NotRequired[AXValue]
    value: NotRequired[AXValue]
    properties: NotRequired[list[AXProperty]]
    parentId: NotRequired[AXNodeId]
    childIds: NotRequired[list[AXNodeId]]
    backendDOMNodeId: NotRequired[int]
    frameId: NotRequired[str]
