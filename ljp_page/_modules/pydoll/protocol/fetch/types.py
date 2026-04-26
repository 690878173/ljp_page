from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ljp_page._modules.pydoll.protocol.network.types import ResourceType


class RequestStage(str, Enum):
    """请求处理的阶段。"""

    REQUEST = 'Request'
    RESPONSE = 'Response'


class AuthChallengeSource(str, Enum):
    """身份验证质询的来源。"""

    SERVER = 'Server'
    PROXY = 'Proxy'


class AuthChallengeResponseType(str, Enum):
    """决定如何应对授权挑战。"""

    DEFAULT = 'Default'
    CANCEL_AUTH = 'CancelAuth'
    PROVIDE_CREDENTIALS = 'ProvideCredentials'


class RequestPattern(TypedDict, total=False):
    """请求拦截的模式。"""

    urlPattern: str  #允许使用通配符。省略相当于“*”。
    resourceType: ResourceType
    requestStage: RequestStage


class HeaderEntry(TypedDict):
    """响应 HTTP 标头条目。"""

    name: str
    value: str


class AuthChallenge(TypedDict):
    """HTTP 状态代码 401 或 407 的授权质询。"""

    source: NotRequired[AuthChallengeSource]
    origin: str
    scheme: str  #例如基础、摘要
    realm: str


class AuthChallengeResponse(TypedDict):
    """对 AuthChallenge 的响应。"""

    response: AuthChallengeResponseType
    username: NotRequired[str]
    password: NotRequired[str]
