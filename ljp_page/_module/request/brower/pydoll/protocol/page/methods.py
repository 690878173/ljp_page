from enum import Enum

from typing_extensions import NotRequired, TypedDict

from base import Command, EmptyParams, EmptyResponse, Response
from debugger.types import SearchMatch
from dom.types import Rect
from io.types import StreamHandle
from network.types import LoaderId
from page.types import (
    AdScriptAncestry,
    AppManifestError,
    AppManifestParsedProperties,
    AutoResponseMode,
    CompilationCacheParams,
    FontFamilies,
    FontSizes,
    FrameId,
    FrameResourceTree,
    FrameTree,
    InstallabilityError,
    LayoutViewport,
    NavigationEntry,
    OriginTrial,
    PermissionsPolicyFeatureState,
    ReferrerPolicy,
    ScreencastFormat,
    ScreenshotFormat,
    ScriptFontFamilies,
    ScriptIdentifier,
    TransferMode,
    TransitionType,
    Viewport,
    VisualViewport,
    WebAppManifest,
    WebLifecycleState,
)
from runtime.types import ExecutionContextId


class PageMethod(str, Enum):
    ADD_SCRIPT_TO_EVALUATE_ON_LOAD = 'Page.addScriptToEvaluateOnLoad'
    ADD_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT = 'Page.addScriptToEvaluateOnNewDocument'
    BRING_TO_FRONT = 'Page.bringToFront'
    CAPTURE_SCREENSHOT = 'Page.captureScreenshot'
    CAPTURE_SNAPSHOT = 'Page.captureSnapshot'
    CLEAR_COMPILATION_CACHE = 'Page.clearCompilationCache'
    CLOSE = 'Page.close'
    CRASH = 'Page.crash'
    CREATE_ISOLATED_WORLD = 'Page.createIsolatedWorld'
    DISABLE = 'Page.disable'
    ENABLE = 'Page.enable'
    GENERATE_TEST_REPORT = 'Page.generateTestReport'
    GET_AD_SCRIPT_ANCESTRY_IDS = 'Page.getAdScriptAncestryIds'
    GET_APP_ID = 'Page.getAppId'
    GET_APP_MANIFEST = 'Page.getAppManifest'
    GET_FRAME_TREE = 'Page.getFrameTree'
    GET_INSTALLABILITY_ERRORS = 'Page.getInstallabilityErrors'
    GET_LAYOUT_METRICS = 'Page.getLayoutMetrics'
    GET_MANIFEST_ICONS = 'Page.getManifestIcons'
    GET_NAVIGATION_HISTORY = 'Page.getNavigationHistory'
    GET_ORIGIN_TRIALS = 'Page.getOriginTrials'
    GET_PERMISSIONS_POLICY_STATE = 'Page.getPermissionsPolicyState'
    GET_RESOURCE_CONTENT = 'Page.getResourceContent'
    GET_RESOURCE_TREE = 'Page.getResourceTree'
    HANDLE_JAVASCRIPT_DIALOG = 'Page.handleJavaScriptDialog'
    NAVIGATE = 'Page.navigate'
    NAVIGATE_TO_HISTORY_ENTRY = 'Page.navigateToHistoryEntry'
    PRINT_TO_PDF = 'Page.printToPDF'
    PRODUCE_COMPILATION_CACHE = 'Page.produceCompilationCache'
    RELOAD = 'Page.reload'
    REMOVE_SCRIPT_TO_EVALUATE_ON_LOAD = 'Page.removeScriptToEvaluateOnLoad'
    REMOVE_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT = 'Page.removeScriptToEvaluateOnNewDocument'
    RESET_NAVIGATION_HISTORY = 'Page.resetNavigationHistory'
    SCREENCAST_FRAME_ACK = 'Page.screencastFrameAck'
    SEARCH_IN_RESOURCE = 'Page.searchInResource'
    SET_AD_BLOCKING_ENABLED = 'Page.setAdBlockingEnabled'
    SET_BYPASS_CSP = 'Page.setBypassCSP'
    SET_DOCUMENT_CONTENT = 'Page.setDocumentContent'
    SET_FONT_FAMILIES = 'Page.setFontFamilies'
    SET_FONT_SIZES = 'Page.setFontSizes'
    SET_INTERCEPT_FILE_CHOOSER_DIALOG = 'Page.setInterceptFileChooserDialog'
    SET_LIFECYCLE_EVENTS_ENABLED = 'Page.setLifecycleEventsEnabled'
    SET_PRERENDERING_ALLOWED = 'Page.setPrerenderingAllowed'
    SET_RPH_REGISTRATION_MODE = 'Page.setRPHRegistrationMode'
    SET_SPC_TRANSACTION_MODE = 'Page.setSPCTransactionMode'
    SET_WEB_LIFECYCLE_STATE = 'Page.setWebLifecycleState'
    START_SCREENCAST = 'Page.startScreencast'
    STOP_LOADING = 'Page.stopLoading'
    STOP_SCREENCAST = 'Page.stopScreencast'
    WAIT_FOR_DEBUGGER = 'Page.waitForDebugger'
    ADD_COMPILATION_CACHE = 'Page.addCompilationCache'


class AddScriptToEvaluateOnNewDocumentParams(TypedDict):
    """addScriptToEvaluateOnNewDocument 的参数。"""

    source: str
    worldName: NotRequired[str]
    includeCommandLineAPI: NotRequired[bool]
    runImmediately: NotRequired[bool]


class CaptureScreenshotParams(TypedDict, total=False):
    """captureScreenshot 的参数。"""

    format: ScreenshotFormat
    quality: int
    clip: Viewport
    fromSurface: bool
    captureBeyondViewport: bool
    optimizeForSpeed: bool


class CaptureSnapshotParams(TypedDict, total=False):
    """captureSnapshot 的参数。"""

    format: str


class CreateIsolatedWorldParams(TypedDict):
    """createIsolatedWorld 的参数。"""

    frameId: FrameId
    worldName: NotRequired[str]
    grantUniveralAccess: NotRequired[bool]


class GetAppManifestParams(TypedDict, total=False):
    """getAppManifest 的参数。"""

    manifestId: str


class GetAdScriptAncestryParams(TypedDict):
    """getAdScriptAncestry 的参数。"""

    frameId: FrameId


class GetPermissionsPolicyStateParams(TypedDict):
    """getPermissionsPolicyState 的参数。"""

    frameId: FrameId


class GetOriginTrialsParams(TypedDict):
    """getOriginTrials 的参数。"""

    frameId: FrameId


class GetResourceContentParams(TypedDict):
    """getResourceContent 的参数。"""

    frameId: FrameId
    url: str


class HandleJavaScriptDialogParams(TypedDict):
    """handleJavaScriptDialog 的参数。"""

    accept: bool
    promptText: NotRequired[str]


class NavigateParams(TypedDict):
    """用于导航的参数。"""

    url: str
    referrer: NotRequired[str]
    transitionType: NotRequired[TransitionType]
    frameId: NotRequired[FrameId]
    referrerPolicy: NotRequired[ReferrerPolicy]


class NavigateToHistoryEntryParams(TypedDict):
    """navigateToHistoryEntry 的参数。"""

    entryId: int


class EnableParams(TypedDict):
    enableFileChooserOpenedEvent: NotRequired[bool]


class PrintToPDFParams(TypedDict, total=False):
    """printToPDF 的参数。"""

    landscape: bool
    displayHeaderFooter: bool
    printBackground: bool
    scale: float
    paperWidth: float
    paperHeight: float
    marginTop: float
    marginBottom: float
    marginLeft: float
    marginRight: float
    pageRanges: str
    headerTemplate: str
    footerTemplate: str
    preferCSSPageSize: bool
    transferMode: TransferMode
    generateTaggedPDF: bool
    generateDocumentOutline: bool


class ReloadParams(TypedDict, total=False):
    """重新加载的参数。"""

    ignoreCache: bool
    scriptToEvaluateOnLoad: str
    loaderId: LoaderId


class RemoveScriptToEvaluateOnNewDocumentParams(TypedDict):
    """removeScriptToEvaluateOnNewDocument 的参数。"""

    identifier: ScriptIdentifier


class ScreencastFrameAckParams(TypedDict):
    """screencastFrameAck 的参数。"""

    sessionId: int


class SearchInResourceParams(TypedDict):
    """searchInResource 的参数。"""

    frameId: FrameId
    url: str
    query: str
    caseSensitive: NotRequired[bool]
    isRegex: NotRequired[bool]


class SetAdBlockingEnabledParams(TypedDict):
    """setAdBlockingEnabled 的参数。"""

    enabled: bool


class SetBypassCSPParams(TypedDict):
    """setBypassCSP 的参数。"""

    enabled: bool


class AddScriptToEvaluateOnLoadParams(TypedDict):
    """addScriptToEvaluateOnLoad 的参数。"""

    scriptSource: str


class SetDocumentContentParams(TypedDict):
    """setDocumentContent 的参数。"""

    frameId: FrameId
    html: str


class SetInterceptFileChooserDialogParams(TypedDict):
    """setInterceptFileChooserDialog 的参数。"""

    enabled: bool
    cancel: NotRequired[bool]


class SetLifecycleEventsEnabledParams(TypedDict):
    """setLifecycleEventsEnabled 的参数。"""

    enabled: bool


class AddCompilationCacheParams(TypedDict):
    """addCompilationCache 的参数。"""

    url: str
    data: str


class GenerateTestReportParams(TypedDict):
    """生成测试报告的参数。"""

    message: str
    group: NotRequired[str]


class GetAdScriptAncestryIdsParams(TypedDict):
    """getAdScriptAncestryIds 的参数。"""

    frameId: FrameId


class GetAppIdParams(TypedDict, total=False):
    """getAppId 的参数。"""

    appId: str
    recommendedId: str


class GetManifestIconsParams(TypedDict):
    """getManifestIcons 的参数。"""

    pass


class RemoveScriptToEvaluateOnLoadParams(TypedDict):
    """removeScriptToEvaluateOnLoad 的参数。"""

    identifier: ScriptIdentifier


class SetFontFamiliesParams(TypedDict):
    """setFontFamilies 的参数。"""

    fontFamilies: FontFamilies
    forScripts: NotRequired[list[ScriptFontFamilies]]


class SetFontSizesParams(TypedDict):
    """setFontSizes 的参数。"""

    fontSizes: FontSizes


class SetPrerenderingAllowedParams(TypedDict):
    """setPrerenderingAllowed 的参数。"""

    isAllowed: bool


class SetRPHRegistrationModeParams(TypedDict):
    """setRPHRegistrationMode 的参数。"""

    mode: AutoResponseMode


class SetSPCTransactionModeParams(TypedDict):
    """setSPCTransactionMode 的参数。"""

    mode: AutoResponseMode


class SetWebLifecycleStateParams(TypedDict):
    """setWebLifecycleState 的参数。"""

    state: WebLifecycleState


class StartScreencastParams(TypedDict, total=False):
    """startScreencast 的参数。"""

    format: ScreencastFormat
    quality: int
    maxWidth: int
    maxHeight: int
    everyNthFrame: int


class ProduceCompilationCacheParams(TypedDict):
    """ProduceCompilationCache 的参数。"""

    scripts: list[CompilationCacheParams]


class AddScriptToEvaluateOnNewDocumentResult(TypedDict):
    identifier: ScriptIdentifier


class CaptureScreenshotResult(TypedDict):
    data: str


class CaptureSnapshotResult(TypedDict):
    data: str


class CreateIsolatedWorldResult(TypedDict):
    executionContextId: ExecutionContextId


class GetAppManifestResult(TypedDict):
    url: str
    errors: list[AppManifestError]
    data: NotRequired[str]
    parsed: NotRequired[AppManifestParsedProperties]
    manifest: NotRequired[WebAppManifest]


class GetInstallabilityErrorsResult(TypedDict):
    installabilityErrors: list[InstallabilityError]


class GetAppIdResult(TypedDict, total=False):
    """getAppId 的结果。"""

    appId: str
    recommendedId: str


class GetAdScriptAncestryResult(TypedDict, total=False):
    adScriptAncestry: AdScriptAncestry


class GetFrameTreeResult(TypedDict):
    frameTree: FrameTree


class GetLayoutMetricsResult(TypedDict):
    layoutViewport: LayoutViewport
    visualViewport: VisualViewport
    contentSize: Rect
    cssLayoutViewport: LayoutViewport
    cssVisualViewport: VisualViewport
    cssContentSize: Rect


class GetNavigationHistoryResult(TypedDict):
    currentIndex: int
    entries: list[NavigationEntry]


class GetPermissionsPolicyStateResult(TypedDict):
    states: list[PermissionsPolicyFeatureState]


class GetOriginTrialsResult(TypedDict):
    originTrials: list[OriginTrial]


class GetResourceContentResult(TypedDict):
    content: str
    base64Encoded: bool


class GetResourceTreeResult(TypedDict):
    frameTree: FrameResourceTree


class PrintToPDFResult(TypedDict):
    data: str
    stream: NotRequired[StreamHandle]


class SearchInResourceResult(TypedDict):
    result: list[SearchMatch]


class NavigateResult(TypedDict):
    """导航结果。"""

    frameId: FrameId
    loaderId: NotRequired[LoaderId]
    errorText: NotRequired[str]
    isDownload: NotRequired[bool]


class AddScriptToEvaluateOnLoadResult(TypedDict):
    """addScriptToEvaluateOnLoad 的结果。"""

    identifier: ScriptIdentifier


class GetManifestIconsResult(TypedDict):
    """getManifestIcons 的结果。"""

    primaryIcon: NotRequired[str]


class GetAdScriptAncestryIdsResult(TypedDict):
    """getAdScriptAncestryIds 的结果。"""

    adScriptAncestry: NotRequired[AdScriptAncestry]


AddScriptToEvaluateOnLoadResponse = Response[AddScriptToEvaluateOnLoadResult]
AddScriptToEvaluateOnNewDocumentResponse = Response[AddScriptToEvaluateOnNewDocumentResult]
CaptureScreenshotResponse = Response[CaptureScreenshotResult]
CaptureSnapshotResponse = Response[CaptureSnapshotResult]
CreateIsolatedWorldResponse = Response[CreateIsolatedWorldResult]
GetAdScriptAncestryIdsResponse = Response[GetAdScriptAncestryIdsResult]
GetAdScriptAncestryResponse = Response[GetAdScriptAncestryResult]
GetAppIdResponse = Response[GetAppIdResult]
GetAppManifestResponse = Response[GetAppManifestResult]
GetFrameTreeResponse = Response[GetFrameTreeResult]
GetInstallabilityErrorsResponse = Response[GetInstallabilityErrorsResult]
GetLayoutMetricsResponse = Response[GetLayoutMetricsResult]
GetManifestIconsResponse = Response[GetManifestIconsResult]
GetNavigationHistoryResponse = Response[GetNavigationHistoryResult]
GetOriginTrialsResponse = Response[GetOriginTrialsResult]
GetPermissionsPolicyStateResponse = Response[GetPermissionsPolicyStateResult]
GetResourceContentResponse = Response[GetResourceContentResult]
GetResourceTreeResponse = Response[GetResourceTreeResult]
NavigateResponse = Response[NavigateResult]
PrintToPDFResponse = Response[PrintToPDFResult]
SearchInResourceResponse = Response[SearchInResourceResult]


AddCompilationCacheCommand = Command[AddCompilationCacheParams, Response[EmptyResponse]]
AddScriptToEvaluateOnLoadCommand = Command[
    AddScriptToEvaluateOnLoadParams, AddScriptToEvaluateOnLoadResponse
]
AddScriptToEvaluateOnNewDocumentCommand = Command[
    AddScriptToEvaluateOnNewDocumentParams, AddScriptToEvaluateOnNewDocumentResponse
]
BringToFrontCommand = Command[EmptyParams, Response[EmptyResponse]]
CaptureScreenshotCommand = Command[CaptureScreenshotParams, CaptureScreenshotResponse]
CaptureSnapshotCommand = Command[CaptureSnapshotParams, CaptureSnapshotResponse]
ClearCompilationCacheCommand = Command[EmptyParams, Response[EmptyResponse]]
CloseCommand = Command[EmptyParams, Response[EmptyResponse]]
CrashCommand = Command[EmptyParams, Response[EmptyResponse]]
CreateIsolatedWorldCommand = Command[CreateIsolatedWorldParams, CreateIsolatedWorldResponse]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EnableParams, Response[EmptyResponse]]
GenerateTestReportCommand = Command[GenerateTestReportParams, Response[EmptyResponse]]
GetAdScriptAncestryCommand = Command[GetAdScriptAncestryParams, GetAdScriptAncestryResponse]
GetAdScriptAncestryIdsCommand = Command[
    GetAdScriptAncestryIdsParams, GetAdScriptAncestryIdsResponse
]
GetAppIdCommand = Command[GetAppIdParams, GetAppIdResponse]
GetAppManifestCommand = Command[GetAppManifestParams, GetAppManifestResponse]
GetFrameTreeCommand = Command[EmptyParams, GetFrameTreeResponse]
GetInstallabilityErrorsCommand = Command[EmptyParams, GetInstallabilityErrorsResponse]
GetLayoutMetricsCommand = Command[EmptyParams, GetLayoutMetricsResponse]
GetManifestIconsCommand = Command[EmptyParams, GetManifestIconsResponse]
GetNavigationHistoryCommand = Command[EmptyParams, GetNavigationHistoryResponse]
GetOriginTrialsCommand = Command[GetOriginTrialsParams, GetOriginTrialsResponse]
GetPermissionsPolicyStateCommand = Command[
    GetPermissionsPolicyStateParams, GetPermissionsPolicyStateResponse
]
GetResourceContentCommand = Command[GetResourceContentParams, GetResourceContentResponse]
GetResourceTreeCommand = Command[EmptyParams, GetResourceTreeResponse]
HandleJavaScriptDialogCommand = Command[HandleJavaScriptDialogParams, Response[EmptyResponse]]
NavigateCommand = Command[NavigateParams, NavigateResponse]
NavigateToHistoryEntryCommand = Command[NavigateToHistoryEntryParams, Response[EmptyResponse]]
PrintToPDFCommand = Command[PrintToPDFParams, PrintToPDFResponse]
ProduceCompilationCacheCommand = Command[ProduceCompilationCacheParams, Response[EmptyResponse]]
ReloadCommand = Command[ReloadParams, Response[EmptyResponse]]
RemoveScriptToEvaluateOnLoadCommand = Command[
    RemoveScriptToEvaluateOnLoadParams, Response[EmptyResponse]
]
RemoveScriptToEvaluateOnNewDocumentCommand = Command[
    RemoveScriptToEvaluateOnNewDocumentParams, Response[EmptyResponse]
]
ResetNavigationHistoryCommand = Command[EmptyParams, Response[EmptyResponse]]
ScreencastFrameAckCommand = Command[ScreencastFrameAckParams, Response[EmptyResponse]]
SearchInResourceCommand = Command[SearchInResourceParams, SearchInResourceResponse]
SetAdBlockingEnabledCommand = Command[SetAdBlockingEnabledParams, Response[EmptyResponse]]
SetBypassCSPCommand = Command[SetBypassCSPParams, Response[EmptyResponse]]
SetDocumentContentCommand = Command[SetDocumentContentParams, Response[EmptyResponse]]
SetFontFamiliesCommand = Command[SetFontFamiliesParams, Response[EmptyResponse]]
SetFontSizesCommand = Command[SetFontSizesParams, Response[EmptyResponse]]
SetInterceptFileChooserDialogCommand = Command[
    SetInterceptFileChooserDialogParams, Response[EmptyResponse]
]
SetLifecycleEventsEnabledCommand = Command[SetLifecycleEventsEnabledParams, Response[EmptyResponse]]
SetPrerenderingAllowedCommand = Command[SetPrerenderingAllowedParams, Response[EmptyResponse]]
SetRPHRegistrationModeCommand = Command[SetRPHRegistrationModeParams, Response[EmptyResponse]]
SetSPCTransactionModeCommand = Command[SetSPCTransactionModeParams, Response[EmptyResponse]]
SetWebLifecycleStateCommand = Command[SetWebLifecycleStateParams, Response[EmptyResponse]]
StartScreencastCommand = Command[StartScreencastParams, Response[EmptyResponse]]
StopLoadingCommand = Command[EmptyParams, Response[EmptyResponse]]
StopScreencastCommand = Command[EmptyParams, Response[EmptyResponse]]
WaitForDebuggerCommand = Command[EmptyParams, Response[EmptyResponse]]
