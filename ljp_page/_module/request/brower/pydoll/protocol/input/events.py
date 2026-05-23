from enum import Enum

from typing_extensions import TypedDict

from base import CDPEvent
from input.types import DragData


class InputEvent(str, Enum):
    """来自 Chrome DevTools 协议输入域的事件。

    该枚举包含与输入相关的事件的名称，这些事件可以是
    从 Chrome DevTools 协议收到。这些事件提供了信息
    关于可以拦截或模拟的用户输入交互。"""

    DRAG_INTERCEPTED = 'Input.dragIntercepted'
    """
    Emitted only when Input.setInterceptDrags is enabled. Use this data with
    Input.dispatchDragEvent to restore normal drag and drop behavior.

    Args:
        data (DragData): Contains information about the dragged data.
    """


class DragInterceptedEventParams(TypedDict):
    """DragIntercepted 事件的参数。"""

    data: DragData


DragInterceptedEvent = CDPEvent[DragInterceptedEventParams]
