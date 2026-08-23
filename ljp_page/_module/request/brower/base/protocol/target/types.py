from typing_extensions import NotRequired, TypedDict

from ..browser.types import BrowserContextID
from ..page.types import FrameId

TargetID = str
SessionID = str


class TargetInfo(TypedDict):
    targetId: TargetID
    type: str
    title: str
    url: str
    attached: bool
    openerId: NotRequired[TargetID]
    canAccessOpener: NotRequired[bool]
    openerFrameId: NotRequired[FrameId]
    browserContextId: NotRequired[BrowserContextID]
    subtype: NotRequired[str]


class FilterEntry(TypedDict, total=False):
    """目标查询/发现/自动附加操作使用的过滤器。"""

    exclude: bool
    type: str


TargetFilter = list[FilterEntry]


class RemoteLocation(TypedDict):
    host: str
    port: int
