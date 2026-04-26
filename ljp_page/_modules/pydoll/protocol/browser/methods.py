from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ljp_page._modules.pydoll.protocol.base import Command, EmptyParams, EmptyResponse, Response
from ljp_page._modules.pydoll.protocol.browser.types import (
    Bounds,
    BrowserCommandId,
    BrowserContextID,
    DownloadBehavior,
    Histogram,
    PermissionDescriptor,
    PermissionSetting,
    PermissionType,
    PrivacySandboxAPI,
    WindowID,
)


class BrowserMethod(str, Enum):
    """浏览器域方法名称。"""

    ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG = 'Browser.addPrivacySandboxCoordinatorKeyConfig'
    ADD_PRIVACY_SANDBOX_ENROLLMENT_OVERRIDE = 'Browser.addPrivacySandboxEnrollmentOverride'
    CANCEL_DOWNLOAD = 'Browser.cancelDownload'
    CLOSE = 'Browser.close'
    CRASH = 'Browser.crash'
    CRASH_GPU_PROCESS = 'Browser.crashGpuProcess'
    EXECUTE_BROWSER_COMMAND = 'Browser.executeBrowserCommand'
    GET_BROWSER_COMMAND_LINE = 'Browser.getBrowserCommandLine'
    GET_HISTOGRAM = 'Browser.getHistogram'
    GET_HISTOGRAMS = 'Browser.getHistograms'
    GET_VERSION = 'Browser.getVersion'
    GET_WINDOW_BOUNDS = 'Browser.getWindowBounds'
    GET_WINDOW_FOR_TARGET = 'Browser.getWindowForTarget'
    GRANT_PERMISSIONS = 'Browser.grantPermissions'
    RESET_PERMISSIONS = 'Browser.resetPermissions'
    SET_CONTENTS_SIZE = 'Browser.setContentsSize'
    SET_DOCK_TILE = 'Browser.setDockTile'
    SET_DOWNLOAD_BEHAVIOR = 'Browser.setDownloadBehavior'
    SET_PERMISSION = 'Browser.setPermission'
    SET_WINDOW_BOUNDS = 'Browser.setWindowBounds'


class SetPermissionParams(TypedDict):
    """用于设置给定源的权限设置的参数。"""

    permission: PermissionDescriptor
    setting: PermissionSetting
    origin: NotRequired[str]
    browserContextId: NotRequired[BrowserContextID]


class GrantPermissionsParams(TypedDict):
    """用于向给定源授予特定权限的参数。"""

    permissions: list[PermissionType]
    origin: NotRequired[str]
    browserContextId: NotRequired[BrowserContextID]


class ResetPermissionsParams(TypedDict):
    """用于重置所有源的所有权限管理的参数。"""

    browserContextId: NotRequired[BrowserContextID]


class SetDownloadBehaviorParams(TypedDict):
    """用于设置下载文件时的行为的参数。"""

    behavior: DownloadBehavior
    browserContextId: NotRequired[BrowserContextID]
    downloadPath: NotRequired[str]
    eventsEnabled: NotRequired[bool]


class CancelDownloadParams(TypedDict):
    """用于取消正在进行的下载的参数。"""

    guid: str
    browserContextId: NotRequired[BrowserContextID]


class GetHistogramsParams(TypedDict):
    """用于获取 Chrome 直方图的参数。"""

    query: NotRequired[str]
    delta: NotRequired[bool]


class GetHistogramParams(TypedDict):
    """用于按名称获取 Chrome 直方图的参数。"""

    name: str
    delta: NotRequired[bool]


class GetWindowBoundsParams(TypedDict):
    """用于获取浏览器窗口的位置和大小的参数。"""

    windowId: WindowID


class GetWindowForTargetParams(TypedDict):
    """用于获取包含 devtools 目标的浏览器窗口的参数。"""

    targetId: NotRequired[str]  #目标.TargetID


class SetWindowBoundsParams(TypedDict):
    """用于设置浏览器窗口的位置和/或大小的参数。"""

    windowId: WindowID
    bounds: Bounds


class SetContentsSizeParams(TypedDict):
    """用于设置浏览器内容大小的参数。"""

    windowId: WindowID
    width: NotRequired[int]
    height: NotRequired[int]


class SetDockTileParams(TypedDict):
    """用于设置停靠图块详细信息的参数，特定于平台。"""

    badgeLabel: NotRequired[str]
    image: NotRequired[str]  #PNG编码图像（base64）


class ExecuteBrowserCommandParams(TypedDict):
    """用于调用遥测使用的自定义浏览器命令的参数。"""

    commandId: BrowserCommandId


class AddPrivacySandboxEnrollmentOverrideParams(TypedDict):
    """用于允许站点无需注册即可使用隐私沙箱功能的参数。"""

    url: str


class AddPrivacySandboxCoordinatorKeyConfigParams(TypedDict):
    """用于配置隐私沙箱 API 加密密钥的参数。"""

    api: PrivacySandboxAPI
    coordinatorOrigin: str
    keyConfig: str
    browserContextId: NotRequired[BrowserContextID]


#结果类型
class GetVersionResult(TypedDict):
    """getVersion 命令的结果。"""

    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str


class GetBrowserCommandLineResult(TypedDict):
    """getBrowserCommandLine 命令的结果。"""

    arguments: list[str]


class GetHistogramsResult(TypedDict):
    """getHistograms 命令的结果。"""

    histograms: list[Histogram]


class GetHistogramResult(TypedDict):
    """getHistogram 命令的结果。"""

    histogram: Histogram


class GetWindowBoundsResult(TypedDict):
    """getWindowBounds 命令的结果。"""

    bounds: Bounds


class GetWindowForTargetResult(TypedDict):
    """getWindowForTarget 命令的结果。"""

    windowId: WindowID
    bounds: Bounds


#响应类型
GetVersionResponse = Response[GetVersionResult]
GetBrowserCommandLineResponse = Response[GetBrowserCommandLineResult]
GetHistogramsResponse = Response[GetHistogramsResult]
GetHistogramResponse = Response[GetHistogramResult]
GetWindowBoundsResponse = Response[GetWindowBoundsResult]
GetWindowForTargetResponse = Response[GetWindowForTargetResult]


#命令类型
AddPrivacySandboxCoordinatorKeyConfigCommand = Command[
    AddPrivacySandboxCoordinatorKeyConfigParams, Response[EmptyResponse]
]
AddPrivacySandboxEnrollmentOverrideCommand = Command[
    AddPrivacySandboxEnrollmentOverrideParams, Response[EmptyResponse]
]
CancelDownloadCommand = Command[CancelDownloadParams, Response[EmptyResponse]]
CloseCommand = Command[EmptyParams, Response[EmptyResponse]]
CrashCommand = Command[EmptyParams, Response[EmptyResponse]]
CrashGpuProcessCommand = Command[EmptyParams, Response[EmptyResponse]]
ExecuteBrowserCommandCommand = Command[ExecuteBrowserCommandParams, Response[EmptyResponse]]
GetBrowserCommandLineCommand = Command[EmptyParams, GetBrowserCommandLineResponse]
GetHistogramCommand = Command[GetHistogramParams, GetHistogramResponse]
GetHistogramsCommand = Command[GetHistogramsParams, GetHistogramsResponse]
GetVersionCommand = Command[EmptyParams, GetVersionResponse]
GetWindowBoundsCommand = Command[GetWindowBoundsParams, GetWindowBoundsResponse]
GetWindowForTargetCommand = Command[GetWindowForTargetParams, GetWindowForTargetResponse]
GrantPermissionsCommand = Command[GrantPermissionsParams, Response[EmptyResponse]]
ResetPermissionsCommand = Command[ResetPermissionsParams, Response[EmptyResponse]]
SetContentsSizeCommand = Command[SetContentsSizeParams, Response[EmptyResponse]]
SetDockTileCommand = Command[SetDockTileParams, Response[EmptyResponse]]
SetDownloadBehaviorCommand = Command[SetDownloadBehaviorParams, Response[EmptyResponse]]
SetPermissionCommand = Command[SetPermissionParams, Response[EmptyResponse]]
SetWindowBoundsCommand = Command[SetWindowBoundsParams, Response[EmptyResponse]]
