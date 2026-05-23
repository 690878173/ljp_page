from enum import Enum

from typing_extensions import TypedDict

from accessibility.types import AXNode
from base import CDPEvent


class AccessibilityEvent(str, Enum):
    """来自 Chrome DevTools 协议的辅助功能域的事件。

    请参阅 https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/"""

    LOAD_COMPLETE = 'Accessibility.loadComplete'
    """
    Mirrors the load complete event sent by the browser to assistive technology
    when the web page has finished loading.

    Args:
        root (AXNode): New document root node.
    """

    NODES_UPDATED = 'Accessibility.nodesUpdated'
    """
    Fired when a node is updated in the accessibility tree.

    Args:
        nodes (list[AXNode]): Updated nodes.
    """


class LoadCompleteEventParams(TypedDict):
    """loadComplete 事件的参数。"""

    root: AXNode


class NodesUpdatedEventParams(TypedDict):
    """NodesUpdated 事件的参数。"""

    nodes: list[AXNode]


LoadCompleteEvent = CDPEvent[LoadCompleteEventParams]
NodesUpdatedEvent = CDPEvent[NodesUpdatedEventParams]
