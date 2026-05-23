from enum import Enum

from typing_extensions import NotRequired, TypedDict

TimeSinceEpoch = float


class GestureSourceType(str, Enum):
    """手势源类型。"""

    DEFAULT = 'default'
    TOUCH = 'touch'
    MOUSE = 'mouse'


class MouseButton(str, Enum):
    """鼠标按钮类型。"""

    NONE = 'none'
    LEFT = 'left'
    MIDDLE = 'middle'
    RIGHT = 'right'
    BACK = 'back'
    FORWARD = 'forward'


class DragEventType(str, Enum):
    """拖动事件类型。"""

    DRAG_ENTER = 'dragEnter'
    DRAG_OVER = 'dragOver'
    DROP = 'drop'
    DRAG_CANCEL = 'dragCancel'


class KeyEventType(str, Enum):
    """关键事件类型。"""

    KEY_DOWN = 'keyDown'
    KEY_UP = 'keyUp'
    RAW_KEY_DOWN = 'rawKeyDown'
    CHAR = 'char'


class MouseEventType(str, Enum):
    """鼠标事件类型。"""

    MOUSE_PRESSED = 'mousePressed'
    MOUSE_RELEASED = 'mouseReleased'
    MOUSE_MOVED = 'mouseMoved'
    MOUSE_WHEEL = 'mouseWheel'


class TouchEventType(str, Enum):
    """触摸事件类型。"""

    TOUCH_START = 'touchStart'
    TOUCH_END = 'touchEnd'
    TOUCH_MOVE = 'touchMove'
    TOUCH_CANCEL = 'touchCancel'


class KeyModifier(int, Enum):
    ALT = 1
    CTRL = 2
    META = 4
    SHIFT = 8


class KeyLocation(int, Enum):
    LEFT = 1
    RIGHT = 2


class PointerType(str, Enum):
    """指针类型。"""

    MOUSE = 'mouse'
    PEN = 'pen'


class TouchPoint(TypedDict):
    """触摸点数据。"""

    x: float
    y: float
    radiusX: NotRequired[float]
    radiusY: NotRequired[float]
    rotationAngle: NotRequired[float]
    force: NotRequired[float]
    tangentialPressure: NotRequired[float]
    tiltX: NotRequired[float]
    tiltY: NotRequired[float]
    twist: NotRequired[int]
    id: NotRequired[float]


class DragDataItem(TypedDict):
    """拖动数据项。"""

    mimeType: str
    data: str
    title: NotRequired[str]
    baseURL: NotRequired[str]


class DragData(TypedDict):
    """拖动数据。"""

    items: list[DragDataItem]
    dragOperationsMask: int
    files: NotRequired[list[str]]
