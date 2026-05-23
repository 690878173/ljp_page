from enum import Enum

from typing_extensions import NotRequired, TypedDict


class ScreenOrientationType(str, Enum):
    """定向类型。"""

    PORTRAIT_PRIMARY = 'portraitPrimary'
    PORTRAIT_SECONDARY = 'portraitSecondary'
    LANDSCAPE_PRIMARY = 'landscapePrimary'
    LANDSCAPE_SECONDARY = 'landscapeSecondary'


class DisplayFeatureOrientation(str, Enum):
    """显示功能相对于屏幕的方向。"""

    VERTICAL = 'vertical'
    HORIZONTAL = 'horizontal'


class DevicePostureType(str, Enum):
    """设备的当前姿势。"""

    CONTINUOUS = 'continuous'
    FOLDED = 'folded'


class VirtualTimePolicy(str, Enum):
    """advance：如果调度程序耗尽了立即工作，虚拟时基可能会快进
    允许下一个延迟任务（如果有）运行；暂停：虚拟时基可能不会提前；
    暂停IfNetworkFetchesPending：如果有任何未决的，虚拟时基可能不会提前
    资源获取。"""

    ADVANCE = 'advance'
    PAUSE = 'pause'
    PAUSE_IF_NETWORK_FETCHES_PENDING = 'pauseIfNetworkFetchesPending'


class SensorType(str, Enum):
    """用于指定要模拟的传感器类型。
    有关更多信息，请参阅 https://w3c.github.io/sensors/#automation。"""

    ABSOLUTE_ORIENTATION = 'absolute-orientation'
    ACCELEROMETER = 'accelerometer'
    AMBIENT_LIGHT = 'ambient-light'
    GRAVITY = 'gravity'
    GYROSCOPE = 'gyroscope'
    LINEAR_ACCELERATION = 'linear-acceleration'
    MAGNETOMETER = 'magnetometer'
    RELATIVE_ORIENTATION = 'relative-orientation'


class PressureSource(str, Enum):
    """压力源类型。"""

    CPU = 'cpu'


class PressureState(str, Enum):
    """压力状态。"""

    NOMINAL = 'nominal'
    FAIR = 'fair'
    SERIOUS = 'serious'
    CRITICAL = 'critical'


class DisabledImageType(str, Enum):
    """可以禁用的图像类型的枚举。"""

    AVIF = 'avif'
    WEBP = 'webp'


class SafeAreaInsets(TypedDict, total=False):
    """安全区域插入配置。"""

    top: int  #覆盖安全区域插入顶部
    topMax: int  #覆盖安全区域最大插入顶部
    left: int  #覆盖左侧安全区域插入
    leftMax: int  #覆盖安全区域最大插入左侧
    bottom: int  #覆盖安全区域插入底部
    bottomMax: int  #覆盖安全区域最大插入底部
    right: int  #覆盖右侧安全区域插入
    rightMax: int  #覆盖 safe-area-max-inset-right


class ScreenOrientation(TypedDict):
    """屏幕方向。"""

    type: ScreenOrientationType  #定向类型
    angle: int  #方位角


class DisplayFeature(TypedDict):
    """显示功能配置。"""

    #显示特征相对于屏幕的方向
    orientation: DisplayFeatureOrientation
    #x 或 y 方向距屏幕原点的偏移量
    offset: int
    #显示功能可能会屏蔽内容，使其不会物理显示
    #该长度和偏移量描述了该区域。仅拆分显示功能
    #内容的 mask_length 为 0
    maskLength: int


class DevicePosture(TypedDict):
    """设备姿态配置。"""

    type: DevicePostureType  #设备当前姿态


class MediaFeature(TypedDict):
    """媒体功能配置。"""

    name: str
    value: str


class UserAgentBrandVersion(TypedDict):
    """用于指定要模拟的用户代理客户端提示。
    请参阅 https://wicg.github.io/ua-client-hints"""

    brand: str
    version: str


class UserAgentMetadata(TypedDict):
    """用于指定要模拟的用户代理客户端提示。
    请参阅 https://wicg.github.io/ua-client-hints
    缺失的可选值将由目标用其通常使用的值来填充。"""

    platform: str
    platformVersion: str
    architecture: str
    model: str
    mobile: bool
    brands: NotRequired[list[UserAgentBrandVersion]]  #Sec-CH-UA 中出现的品牌
    fullVersionList: NotRequired[
        list[UserAgentBrandVersion]
    ]  #出现在 Sec-CH-UA-Full-Version-List 中的品牌
    fullVersion: NotRequired[str]  #已弃用
    bitness: NotRequired[str]
    wow64: NotRequired[bool]
    formFactors: NotRequired[list[str]]  #用于指定用户代理外形值。
    #请参阅 https://wicg.github.io/ua-client-hints/#sec-ch-ua-form-factors


class SensorMetadata(TypedDict, total=False):
    """传感器元数据配置。"""

    available: bool
    minimumFrequency: float
    maximumFrequency: float


class SensorReadingSingle(TypedDict):
    """单个传感器读数值。"""

    value: float


class SensorReadingXYZ(TypedDict):
    """XYZ 传感器读数值。"""

    x: float
    y: float
    z: float


class SensorReadingQuaternion(TypedDict):
    """四元数传感器读数值。"""

    x: float
    y: float
    z: float
    w: float


class SensorReading(TypedDict, total=False):
    """传感器读取配置。"""

    single: 'SensorReadingSingle'
    xyz: 'SensorReadingXYZ'
    quaternion: 'SensorReadingQuaternion'


class PressureMetadata(TypedDict, total=False):
    """压力元数据配置。"""

    available: bool
