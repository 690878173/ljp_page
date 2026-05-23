from enum import Enum

from typing_extensions import TypedDict

from base import Command, EmptyParams, EmptyResponse, Response
from fetch.types import (
    AuthChallengeResponse,
    HeaderEntry,
    RequestPattern,
)
from io.types import StreamHandle
from network.types import ErrorReason


class FetchMethod(str, Enum):
    """获取域方法名称。"""

    CONTINUE_REQUEST = 'Fetch.continueRequest'
    CONTINUE_RESPONSE = 'Fetch.continueResponse'
    CONTINUE_WITH_AUTH = 'Fetch.continueWithAuth'
    DISABLE = 'Fetch.disable'
    ENABLE = 'Fetch.enable'
    FAIL_REQUEST = 'Fetch.failRequest'
    FULFILL_REQUEST = 'Fetch.fulfillRequest'
    GET_RESPONSE_BODY = 'Fetch.getResponseBody'
    TAKE_RESPONSE_BODY_AS_STREAM = 'Fetch.takeResponseBodyAsStream'


RequestId = str


#参数类型
class EnableParams(TypedDict, total=False):
    """用于启用获取域的参数。"""

    patterns: list[RequestPattern]
    handleAuthRequests: bool


class FailRequestParams(TypedDict):
    """请求失败的参数。"""

    requestId: RequestId
    errorReason: ErrorReason


class FulfillRequestParams(TypedDict, total=False):
    """用于满足请求的参数。"""

    requestId: RequestId
    responseCode: int
    responseHeaders: list[HeaderEntry]
    binaryResponseHeaders: str  #\0 分隔的名称:值对 (base64)
    body: str  #Base64 编码
    responsePhrase: str


class ContinueRequestParams(TypedDict, total=False):
    """用于继续请求的参数。"""

    requestId: RequestId
    url: str
    method: str
    postData: str  #Base64 编码
    headers: list[HeaderEntry]
    interceptResponse: bool


class ContinueWithAuthParams(TypedDict):
    """用于通过身份验证继续请求的参数。"""

    requestId: RequestId
    authChallengeResponse: AuthChallengeResponse


class ContinueResponseParams(TypedDict, total=False):
    """用于继续响应的参数。"""

    requestId: RequestId
    responseCode: int
    responsePhrase: str
    responseHeaders: list[HeaderEntry]
    binaryResponseHeaders: str  #\0 分隔的名称:值对 (base64)


class GetResponseBodyParams(TypedDict):
    """用于获取响应主体的参数。"""

    requestId: RequestId


class TakeResponseBodyAsStreamParams(TypedDict):
    """用于将响应主体作为流的参数。"""

    requestId: RequestId


#结果类型
class GetResponseBodyResult(TypedDict):
    """getResponseBody 命令的结果。"""

    body: str
    base64Encoded: bool


class TakeResponseBodyAsStreamResult(TypedDict):
    """takeResponseBodyAsStream 命令的结果。"""

    stream: StreamHandle


#响应类型
GetResponseBodyResponse = Response[GetResponseBodyResult]
TakeResponseBodyAsStreamResponse = Response[TakeResponseBodyAsStreamResult]


#命令类型
ContinueRequestCommand = Command[ContinueRequestParams, Response[EmptyResponse]]
ContinueResponseCommand = Command[ContinueResponseParams, Response[EmptyResponse]]
ContinueWithAuthCommand = Command[ContinueWithAuthParams, Response[EmptyResponse]]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EnableParams, Response[EmptyResponse]]
FailRequestCommand = Command[FailRequestParams, Response[EmptyResponse]]
FulfillRequestCommand = Command[FulfillRequestParams, Response[EmptyResponse]]
GetResponseBodyCommand = Command[GetResponseBodyParams, GetResponseBodyResponse]
TakeResponseBodyAsStreamCommand = Command[
    TakeResponseBodyAsStreamParams, TakeResponseBodyAsStreamResponse
]
