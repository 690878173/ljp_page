from enum import Enum

from typing_extensions import NotRequired, TypedDict

from base import CDPEvent
from browser.types import DownloadProgressState


class BrowserEvent(str, Enum):
    """来自 Chrome DevTools 协议的浏览器域的事件。

    此枚举包含与浏览器相关的事件的名称，这些事件可以是
    从 Chrome DevTools 协议收到。这些事件提供了信息
    关于浏览器活动和状态变化。"""

    DOWNLOAD_PROGRESS = 'Browser.downloadProgress'
    """
    Fired when download makes progress. The last call has |done| == true.

    Args:
        guid (str): Global unique identifier of the download.
        totalBytes (int): Total expected bytes to download.
        receivedBytes (int): Total bytes received.
        state (str): Download status.
            Allowed values: 'inProgress', 'completed', 'canceled'
    """

    DOWNLOAD_WILL_BEGIN = 'Browser.downloadWillBegin'
    """
    Fired when page is about to start a download.

    Args:
        frameId (str): Id of the frame that caused the download to begin.
        guid (str): Global unique identifier of the download.
        url (str): URL of the resource being downloaded.
        suggestedFilename (str): Suggested file name of the resource
            (the actual name of the file saved on disk may differ).
    """


class DownloadProgressEventParams(TypedDict):
    guid: str
    totalBytes: float
    receivedBytes: float
    state: DownloadProgressState
    filePath: NotRequired[str]


class DownloadWillBeginEventParams(TypedDict):
    frameId: str
    guid: str
    url: str
    suggestedFilename: str


DownloadProgressEvent = CDPEvent[DownloadProgressEventParams]
DownloadWillBeginEvent = CDPEvent[DownloadWillBeginEventParams]
