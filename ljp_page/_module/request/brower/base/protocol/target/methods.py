from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ..base import Command, EmptyParams, EmptyResponse, Response
from ..browser.types import BrowserContextID, WindowState
from .types import (
    RemoteLocation,
    SessionID,
    TargetFilter,
    TargetID,
    TargetInfo,
)


class TargetMethod(str, Enum):
    """目标域方法名称。"""

    ACTIVATE_TARGET = 'Target.activateTarget'
    ATTACH_TO_TARGET = 'Target.attachToTarget'
    ATTACH_TO_BROWSER_TARGET = 'Target.attachToBrowserTarget'
    CLOSE_TARGET = 'Target.closeTarget'
    EXPOSE_DEV_TOOLS_PROTOCOL = 'Target.exposeDevToolsProtocol'
    CREATE_BROWSER_CONTEXT = 'Target.createBrowserContext'
    GET_BROWSER_CONTEXTS = 'Target.getBrowserContexts'
    CREATE_TARGET = 'Target.createTarget'
    DETACH_FROM_TARGET = 'Target.detachFromTarget'
    DISPOSE_BROWSER_CONTEXT = 'Target.disposeBrowserContext'
    GET_TARGET_INFO = 'Target.getTargetInfo'
    GET_TARGETS = 'Target.getTargets'
    SEND_MESSAGE_TO_TARGET = 'Target.sendMessageToTarget'
    SET_AUTO_ATTACH = 'Target.setAutoAttach'
    AUTO_ATTACH_RELATED = 'Target.autoAttachRelated'
    SET_DISCOVER_TARGETS = 'Target.setDiscoverTargets'
    SET_REMOTE_LOCATIONS = 'Target.setRemoteLocations'
    OPEN_DEV_TOOLS = 'Target.openDevTools'


#参数类型
class ActivateTargetParams(TypedDict):
    """activateTarget 命令的参数。"""

    targetId: TargetID


class AttachToTargetParams(TypedDict):
    """AttachToTarget 命令的参数。"""

    targetId: TargetID
    flatten: NotRequired[bool]


class AttachToBrowserTargetParams(TypedDict):
    """AttachToBrowserTarget 命令的参数。"""

    sessionId: SessionID


class CloseTargetParams(TypedDict):
    """closeTarget 命令的参数。"""

    targetId: TargetID


class ExposeDevToolsProtocolParams(TypedDict):
    """hideDevToolsProtocol 命令的参数。"""

    targetId: TargetID
    bindingName: NotRequired[str]
    inheritPermissions: NotRequired[bool]


class CreateBrowserContextParams(TypedDict):
    """createBrowserContext 命令的参数。"""

    disposeOnDetach: NotRequired[bool]
    proxyServer: NotRequired[str]
    proxyBypassList: NotRequired[str]
    originsWithUniversalNetworkAccess: NotRequired[list[str]]


class CreateTargetParams(TypedDict):
    """createTarget 命令的参数。"""

    url: str
    left: NotRequired[int]
    top: NotRequired[int]
    width: NotRequired[int]
    height: NotRequired[int]
    windowState: NotRequired[WindowState]
    browserContextId: NotRequired[BrowserContextID]
    enableBeginFrameControl: NotRequired[bool]
    newWindow: NotRequired[bool]
    background: NotRequired[bool]
    forTab: NotRequired[bool]
    hidden: NotRequired[bool]


class DetachFromTargetParams(TypedDict):
    """detachFromTarget 命令的参数。"""

    sessionId: NotRequired[SessionID]
    targetId: NotRequired[TargetID]


class DisposeBrowserContextParams(TypedDict):
    """disposeBrowserContext 命令的参数。"""

    browserContextId: BrowserContextID


class GetTargetInfoParams(TypedDict):
    """getTargetInfo 命令的参数。"""

    targetId: NotRequired[TargetID]


class GetTargetsParams(TypedDict):
    """getTargets 命令的参数。"""

    filter: NotRequired[TargetFilter]


class SendMessageToTargetParams(TypedDict):
    """sendMessageToTarget 命令的参数。"""

    message: str
    sessionId: NotRequired[SessionID]
    targetId: NotRequired[TargetID]


class SetAutoAttachParams(TypedDict):
    """setAutoAttach 命令的参数。"""

    autoAttach: bool
    waitForDebuggerOnStart: bool
    flatten: NotRequired[bool]
    filter: NotRequired[TargetFilter]


class AutoAttachRelatedParams(TypedDict):
    """autoAttachRelated 命令的参数。"""

    targetId: TargetID
    waitForDebuggerOnStart: bool
    filter: NotRequired[TargetFilter]


class SetDiscoverTargetsParams(TypedDict):
    """setDiscoverTargets 命令的参数。"""

    discover: bool
    filter: NotRequired[TargetFilter]


class SetRemoteLocationsParams(TypedDict):
    """setRemoteLocations 命令的参数。"""

    locations: list[RemoteLocation]


class OpenDevToolsParams(TypedDict):
    """openDevTools 命令的参数。"""

    targetId: TargetID


#结果类型
class AttachToTargetResult(TypedDict):
    """AttachToTarget 命令的结果。"""

    sessionId: SessionID


class AttachToBrowserTargetResult(TypedDict):
    """AttachToBrowserTarget 命令的结果。"""

    sessionId: SessionID


class CloseTargetResult(TypedDict):
    """closeTarget 命令的结果。"""

    success: bool


class CreateBrowserContextResult(TypedDict):
    """createBrowserContext 命令的结果。"""

    browserContextId: BrowserContextID


class GetBrowserContextsResult(TypedDict):
    """getBrowserContexts 命令的结果。"""

    browserContextIds: list[BrowserContextID]


class CreateTargetResult(TypedDict):
    """createTarget 命令的结果。"""

    targetId: TargetID


class GetTargetInfoResult(TypedDict):
    """getTargetInfo 命令的结果。"""

    targetInfo: TargetInfo


class GetTargetsResult(TypedDict):
    """getTargets 命令的结果。"""

    targetInfos: list[TargetInfo]


class OpenDevToolsResult(TypedDict):
    """openDevTools 命令的结果。"""

    targetId: TargetID


#响应类型
AttachToTargetResponse = Response[AttachToTargetResult]
AttachToBrowserTargetResponse = Response[AttachToBrowserTargetResult]
CloseTargetResponse = Response[CloseTargetResult]
CreateBrowserContextResponse = Response[CreateBrowserContextResult]
GetBrowserContextsResponse = Response[GetBrowserContextsResult]
CreateTargetResponse = Response[CreateTargetResult]
GetTargetInfoResponse = Response[GetTargetInfoResult]
GetTargetsResponse = Response[GetTargetsResult]
OpenDevToolsResponse = Response[OpenDevToolsResult]


#命令类型
ActivateTargetCommand = Command[ActivateTargetParams, Response[EmptyResponse]]
AttachToTargetCommand = Command[AttachToTargetParams, AttachToTargetResponse]
AttachToBrowserTargetCommand = Command[EmptyParams, AttachToBrowserTargetResponse]
CloseTargetCommand = Command[CloseTargetParams, CloseTargetResponse]
ExposeDevToolsProtocolCommand = Command[ExposeDevToolsProtocolParams, Response[EmptyResponse]]
CreateBrowserContextCommand = Command[CreateBrowserContextParams, CreateBrowserContextResponse]
GetBrowserContextsCommand = Command[EmptyParams, GetBrowserContextsResponse]
CreateTargetCommand = Command[CreateTargetParams, CreateTargetResponse]
DetachFromTargetCommand = Command[DetachFromTargetParams, Response[EmptyResponse]]
DisposeBrowserContextCommand = Command[DisposeBrowserContextParams, Response[EmptyResponse]]
GetTargetInfoCommand = Command[GetTargetInfoParams, GetTargetInfoResponse]
GetTargetsCommand = Command[GetTargetsParams, GetTargetsResponse]
SendMessageToTargetCommand = Command[SendMessageToTargetParams, Response[EmptyResponse]]
SetAutoAttachCommand = Command[SetAutoAttachParams, Response[EmptyResponse]]
AutoAttachRelatedCommand = Command[AutoAttachRelatedParams, Response[EmptyResponse]]
SetDiscoverTargetsCommand = Command[SetDiscoverTargetsParams, Response[EmptyResponse]]
SetRemoteLocationsCommand = Command[SetRemoteLocationsParams, Response[EmptyResponse]]
OpenDevToolsCommand = Command[OpenDevToolsParams, OpenDevToolsResponse]
