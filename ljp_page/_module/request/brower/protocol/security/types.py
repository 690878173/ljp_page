from enum import Enum


class MixedContentType(str, Enum):
    """请求的混合内容类型。"""

    BLOCKABLE = 'blockable'
    OPTIONALLY_BLOCKABLE = 'optionally-blockable'
    NONE = 'none'


class SecurityState(str, Enum):
    """页面的安全状态。"""

    UNKNOWN = 'unknown'
    NEUTRAL = 'neutral'
    SAFE = 'safe'
    INSECURE = 'insecure'
    SECURE = 'secure'
    INFO = 'info'
    INSECURE_BROKEN = 'insecure-broken'
