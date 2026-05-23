from enum import Enum

from typing_extensions import TypedDict

BrowserContextID = str
WindowID = int


class WindowState(str, Enum):
    """浏览器窗口的状态。"""

    NORMAL = 'normal'
    MINIMIZED = 'minimized'
    MAXIMIZED = 'maximized'
    FULLSCREEN = 'fullscreen'


class DownloadBehavior(str, Enum):
    """下载行为选项。"""

    DENY = 'deny'
    ALLOW = 'allow'
    ALLOW_AND_NAME = 'allowAndName'
    DEFAULT = 'default'


class DownloadProgressState(str, Enum):
    """下载进度状态。"""

    IN_PROGRESS = 'inProgress'
    COMPLETED = 'completed'
    CANCELED = 'canceled'


class Bounds(TypedDict, total=False):
    """浏览器窗口边界信息。"""

    left: int  #从屏幕左边缘到窗口的偏移量（以像素为单位）。
    top: int  #从屏幕上边缘到窗口的偏移量（以像素为单位）。
    width: int  #窗口宽度（以像素为单位）。
    height: int  #窗口高度（以像素为单位）。
    windowState: WindowState  #窗口状态。默认为正常。


class PermissionType(str, Enum):
    """权限类型。"""

    AR = 'ar'
    AUDIO_CAPTURE = 'audioCapture'
    AUTOMATIC_FULLSCREEN = 'automaticFullscreen'
    BACKGROUND_FETCH = 'backgroundFetch'
    BACKGROUND_SYNC = 'backgroundSync'
    CAMERA_PAN_TILT_ZOOM = 'cameraPanTiltZoom'
    CAPTURED_SURFACE_CONTROL = 'capturedSurfaceControl'
    CLIPBOARD_READ_WRITE = 'clipboardReadWrite'
    CLIPBOARD_SANITIZED_WRITE = 'clipboardSanitizedWrite'
    DISPLAY_CAPTURE = 'displayCapture'
    DURABLE_STORAGE = 'durableStorage'
    GEOLOCATION = 'geolocation'
    HAND_TRACKING = 'handTracking'
    IDLE_DETECTION = 'idleDetection'
    KEYBOARD_LOCK = 'keyboardLock'
    LOCAL_FONTS = 'localFonts'
    LOCAL_NETWORK_ACCESS = 'localNetworkAccess'
    MIDI = 'midi'
    MIDI_SYSEX = 'midiSysex'
    NFC = 'nfc'
    NOTIFICATIONS = 'notifications'
    PAYMENT_HANDLER = 'paymentHandler'
    PERIODIC_BACKGROUND_SYNC = 'periodicBackgroundSync'
    POINTER_LOCK = 'pointerLock'
    PROTECTED_MEDIA_IDENTIFIER = 'protectedMediaIdentifier'
    SENSORS = 'sensors'
    SMART_CARD = 'smartCard'
    SPEAKER_SELECTION = 'speakerSelection'
    STORAGE_ACCESS = 'storageAccess'
    TOP_LEVEL_STORAGE_ACCESS = 'topLevelStorageAccess'
    VIDEO_CAPTURE = 'videoCapture'
    VR = 'vr'
    WAKE_LOCK_SCREEN = 'wakeLockScreen'
    WAKE_LOCK_SYSTEM = 'wakeLockSystem'
    WEB_APP_INSTALLATION = 'webAppInstallation'
    WEB_PRINTING = 'webPrinting'
    WINDOW_MANAGEMENT = 'windowManagement'


class PermissionSetting(str, Enum):
    """权限设置值。"""

    GRANTED = 'granted'
    DENIED = 'denied'
    PROMPT = 'prompt'


class PermissionDescriptor(TypedDict, total=False):
    """Permissions API 中定义的 PermissionDescriptor 的定义。

    请参阅 https://w3c.github.io/permissions/#dom-permissiondescriptor。"""

    name: str  #权限名称。
    sysex: bool  #对于“midi”权限，还可以指定sysex 控制。
    userVisibleOnly: bool  #对于“推送”权限，可以指定 userVisibleOnly。
    allowWithoutSanitization: (
        bool  #对于“剪贴板”权限，可以指定allowWithoutSanitization。
    )
    allowWithoutGesture: bool  #对于“全屏”权限，必须指定allowWithoutGesture:true。
    panTiltZoom: bool  #对于“相机”权限，可以指定 panTiltZoom。


class BrowserCommandId(str, Enum):
    """executeBrowserCommand 使用的浏览器命令 ID。"""

    OPEN_TAB_SEARCH = 'openTabSearch'
    CLOSE_TAB_SEARCH = 'closeTabSearch'
    OPEN_GLIC = 'openGlic'


class Bucket(TypedDict):
    """Chrome 直方图桶。"""

    low: int  #最小值（含）。
    high: int  #最大值（不含）。
    count: int  #样本数量。


class Histogram(TypedDict):
    """Chrome 直方图。"""

    name: str  #名字。
    sum: int  #样本值的总和。
    count: int  #样本总数。
    buckets: list['Bucket']  #水桶。


class PrivacySandboxAPI(str, Enum):
    """隐私沙箱 API 类型。"""

    BIDDING_AND_AUCTION_SERVICES = 'BiddingAndAuctionServices'
    TRUSTED_KEY_VALUE = 'TrustedKeyValue'
