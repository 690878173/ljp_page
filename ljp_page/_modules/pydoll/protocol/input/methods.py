from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ljp_page._modules.pydoll.protocol.base import Command, EmptyParams, EmptyResponse, Response
from ljp_page._modules.pydoll.protocol.input.types import (
    DragData,
    DragEventType,
    GestureSourceType,
    KeyEventType,
    MouseButton,
    MouseEventType,
    PointerType,
    TimeSinceEpoch,
    TouchEventType,
    TouchPoint,
)


class InputMethod(str, Enum):
    CANCEL_DRAGGING = 'Input.cancelDragging'
    DISPATCH_KEY_EVENT = 'Input.dispatchKeyEvent'
    DISPATCH_MOUSE_EVENT = 'Input.dispatchMouseEvent'
    DISPATCH_TOUCH_EVENT = 'Input.dispatchTouchEvent'
    SET_IGNORE_INPUT_EVENTS = 'Input.setIgnoreInputEvents'
    DISPATCH_DRAG_EVENT = 'Input.dispatchDragEvent'
    EMULATE_TOUCH_FROM_MOUSE_EVENT = 'Input.emulateTouchFromMouseEvent'
    IME_SET_COMPOSITION = 'Input.imeSetComposition'
    INSERT_TEXT = 'Input.insertText'
    SET_INTERCEPT_DRAGS = 'Input.setInterceptDrags'
    SYNTHESIZE_PINCH_GESTURE = 'Input.synthesizePinchGesture'
    SYNTHESIZE_SCROLL_GESTURE = 'Input.synthesizeScrollGesture'
    SYNTHESIZE_TAP_GESTURE = 'Input.synthesizeTapGesture'


class CancelDraggingParams(TypedDict):
    """cancelDragging 命令的参数。"""

    pass


class DispatchDragEventParams(TypedDict):
    """dispatchDragEvent 命令的参数。"""

    type: DragEventType
    x: float
    y: float
    data: DragData
    modifiers: NotRequired[int]


class DispatchKeyEventParams(TypedDict):
    """dispatchKeyEvent 命令的参数。"""

    type: KeyEventType
    modifiers: NotRequired[int]
    timestamp: NotRequired[TimeSinceEpoch]
    text: NotRequired[str]
    unmodifiedText: NotRequired[str]
    keyIdentifier: NotRequired[str]
    code: NotRequired[str]
    key: NotRequired[str]
    windowsVirtualKeyCode: NotRequired[int]
    nativeVirtualKeyCode: NotRequired[int]
    autoRepeat: NotRequired[bool]
    isKeypad: NotRequired[bool]
    isSystemKey: NotRequired[bool]
    location: NotRequired[int]
    commands: NotRequired[list[str]]


class DispatchMouseEventParams(TypedDict):
    """dispatchMouseEvent 命令的参数。"""

    type: MouseEventType
    x: float
    y: float
    modifiers: NotRequired[int]
    timestamp: NotRequired[TimeSinceEpoch]
    button: NotRequired[MouseButton]
    buttons: NotRequired[int]
    clickCount: NotRequired[int]
    force: NotRequired[float]
    tangentialPressure: NotRequired[float]
    tiltX: NotRequired[float]
    tiltY: NotRequired[float]
    twist: NotRequired[int]
    deltaX: NotRequired[float]
    deltaY: NotRequired[float]
    pointerType: NotRequired[PointerType]


class DispatchTouchEventParams(TypedDict):
    """dispatchTouchEvent 命令的参数。"""

    type: TouchEventType
    touchPoints: list[TouchPoint]
    modifiers: NotRequired[int]
    timestamp: NotRequired[TimeSinceEpoch]


class EmulateTouchFromMouseEventParams(TypedDict):
    """emulateTouchFromMouseEvent 命令的参数。"""

    type: MouseEventType
    x: int
    y: int
    button: MouseButton
    timestamp: NotRequired[TimeSinceEpoch]
    deltaX: NotRequired[float]
    deltaY: NotRequired[float]
    modifiers: NotRequired[int]
    clickCount: NotRequired[int]


class ImeSetCompositionParams(TypedDict):
    """imeSetComposition 命令的参数。"""

    text: str
    selectionStart: int
    selectionEnd: int
    replacementStart: NotRequired[int]
    replacementEnd: NotRequired[int]


class InsertTextParams(TypedDict):
    """insertText 命令的参数。"""

    text: str


class SetIgnoreInputEventsParams(TypedDict):
    """setIgnoreInputEvents 命令的参数。"""

    ignore: bool


class SetInterceptDragsParams(TypedDict):
    """setInterceptDrags 命令的参数。"""

    enabled: bool


class SynthesizePinchGestureParams(TypedDict):
    """SynthesizePinchGesture 命令的参数。"""

    x: float
    y: float
    scaleFactor: float
    relativeSpeed: NotRequired[int]
    gestureSourceType: NotRequired[GestureSourceType]


class SynthesizeScrollGestureParams(TypedDict):
    """SynthesizeScrollGesture 命令的参数。"""

    x: float
    y: float
    xDistance: NotRequired[float]
    yDistance: NotRequired[float]
    xOverscroll: NotRequired[float]
    yOverscroll: NotRequired[float]
    preventFling: NotRequired[bool]
    speed: NotRequired[int]
    gestureSourceType: NotRequired[GestureSourceType]
    repeatCount: NotRequired[int]
    repeatDelayMs: NotRequired[int]
    interactionMarkerName: NotRequired[str]


class SynthesizeTapGestureParams(TypedDict):
    """SynthesizeTapGesture 命令的参数。"""

    x: float
    y: float
    duration: NotRequired[int]
    tapCount: NotRequired[int]
    gestureSourceType: NotRequired[GestureSourceType]


#命令类型
CancelDraggingCommand = Command[EmptyParams, Response[EmptyResponse]]
DispatchDragEventCommand = Command[DispatchDragEventParams, Response[EmptyResponse]]
DispatchKeyEventCommand = Command[DispatchKeyEventParams, Response[EmptyResponse]]
DispatchMouseEventCommand = Command[DispatchMouseEventParams, Response[EmptyResponse]]
DispatchTouchEventCommand = Command[DispatchTouchEventParams, Response[EmptyResponse]]
EmulateTouchFromMouseEventCommand = Command[
    EmulateTouchFromMouseEventParams, Response[EmptyResponse]
]
ImeSetCompositionCommand = Command[ImeSetCompositionParams, Response[EmptyResponse]]
InsertTextCommand = Command[InsertTextParams, Response[EmptyResponse]]
SetIgnoreInputEventsCommand = Command[SetIgnoreInputEventsParams, Response[EmptyResponse]]
SetInterceptDragsCommand = Command[SetInterceptDragsParams, Response[EmptyResponse]]
SynthesizePinchGestureCommand = Command[SynthesizePinchGestureParams, Response[EmptyResponse]]
SynthesizeScrollGestureCommand = Command[SynthesizeScrollGestureParams, Response[EmptyResponse]]
SynthesizeTapGestureCommand = Command[SynthesizeTapGestureParams, Response[EmptyResponse]]
