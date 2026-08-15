from enum import Enum

from typing_extensions import NotRequired, TypedDict

from base import Command, EmptyParams, EmptyResponse, Response
from debugger.types import SearchMatch
from emulation.types import UserAgentMetadata
from fetch.types import HeaderEntry, RequestPattern
from network.types import (
    ConnectionType,
    ContentEncoding,
    Cookie,
    CookiePartitionKey,
    CookiePriority,
    CookieSameSite,
    CookieSourceScheme,
    LoadNetworkResourceOptions,
    SecurityIsolationStatus,
)


class NetworkMethod(str, Enum):
    CLEAR_BROWSER_CACHE = 'Network.clearBrowserCache'
    CLEAR_BROWSER_COOKIES = 'Network.clearBrowserCookies'
    DELETE_COOKIES = 'Network.deleteCookies'
    DISABLE = 'Network.disable'
    EMULATE_NETWORK_CONDITIONS = 'Network.emulateNetworkConditions'
    ENABLE = 'Network.enable'
    GET_COOKIES = 'Network.getCookies'
    GET_REQUEST_POST_DATA = 'Network.getRequestPostData'
    GET_RESPONSE_BODY = 'Network.getResponseBody'
    SET_BYPASS_SERVICE_WORKER = 'Network.setBypassServiceWorker'
    SET_CACHE_DISABLED = 'Network.setCacheDisabled'
    SET_COOKIE = 'Network.setCookie'
    SET_COOKIES = 'Network.setCookies'
    SET_EXTRA_HTTP_HEADERS = 'Network.setExtraHTTPHeaders'
    SET_USER_AGENT_OVERRIDE = 'Network.setUserAgentOverride'
    CLEAR_ACCEPTED_ENCODINGS_OVERRIDE = 'Network.clearAcceptedEncodingsOverride'
    ENABLE_REPORTING_API = 'Network.enableReportingApi'
    GET_CERTIFICATE = 'Network.getCertificate'
    GET_RESPONSE_BODY_FOR_INTERCEPTION = 'Network.getResponseBodyForInterception'
    GET_SECURITY_ISOLATION_STATUS = 'Network.getSecurityIsolationStatus'
    LOAD_NETWORK_RESOURCE = 'Network.loadNetworkResource'
    REPLAY_XHR = 'Network.replayXHR'
    SEARCH_IN_RESPONSE_BODY = 'Network.searchInResponseBody'
    SET_ACCEPTED_ENCODINGS = 'Network.setAcceptedEncodings'
    SET_ATTACH_DEBUG_STACK = 'Network.setAttachDebugStack'
    SET_BLOCKED_URLS = 'Network.setBlockedURLs'
    SET_COOKIE_CONTROLS = 'Network.setCookieControls'
    STREAM_RESOURCE_CONTENT = 'Network.streamResourceContent'
    TAKE_RESPONSE_BODY_FOR_INTERCEPTION_AS_STREAM = (
        'Network.takeResponseBodyForInterceptionAsStream'
    )


class DeleteCookiesParams(TypedDict):
    """用于删除浏览器 cookie 的参数。"""

    name: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    partitionKey: NotRequired[CookiePartitionKey]


class EmulateNetworkConditionsParams(TypedDict):
    """用于模拟网络条件的参数。"""

    offline: bool
    latency: float
    downloadThroughput: float
    uploadThroughput: float
    connectionType: NotRequired[ConnectionType]
    packetLoss: NotRequired[float]
    packetQueueLength: NotRequired[int]
    packetReordering: NotRequired[bool]


class NetworkEnableParams(TypedDict):
    """用于启用网络跟踪的参数。"""

    maxTotalBufferSize: NotRequired[int]
    maxResourceBufferSize: NotRequired[int]
    maxPostDataSize: NotRequired[int]


class GetCookiesParams(TypedDict):
    """用于检索浏览器 cookie 的参数。"""

    urls: NotRequired[list[str]]


class GetRequestPostDataParams(TypedDict):
    """用于检索请求 POST 数据的参数。"""

    requestId: str


class GetResponseBodyParams(TypedDict):
    """用于检索响应正文的参数。"""

    requestId: str


class GetCertificateParams(TypedDict):
    """用于检索 DER 编码证书的参数。"""

    origin: str


class GetResponseBodyForInterceptionParams(TypedDict):
    """用于检索拦截请求的响应正文的参数。"""

    interceptionId: str


class SearchInResponseBodyParams(TypedDict):
    """用于在响应内容中搜索的参数。"""

    requestId: str
    query: str
    caseSensitive: NotRequired[bool]
    isRegex: NotRequired[bool]


class SetBypassServiceWorkerParams(TypedDict):
    """用于切换服务工作线程绕过的参数。"""

    bypass: bool


class SetCacheDisabledParams(TypedDict):
    """用于切换请求缓存的参数。"""

    cacheDisabled: bool


class SetCookieParams(TypedDict):
    """用于设置 cookie 的参数。"""

    name: str
    value: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    secure: NotRequired[bool]
    httpOnly: NotRequired[bool]
    sameSite: NotRequired[CookieSameSite]
    expires: NotRequired[float]
    priority: NotRequired[CookiePriority]
    sameParty: NotRequired[bool]
    sourceScheme: NotRequired[CookieSourceScheme]
    sourcePort: NotRequired[int]
    partitionKey: NotRequired[CookiePartitionKey]


class SetCookiesParams(TypedDict):
    """用于设置多个 cookie 的参数。"""

    cookies: list[SetCookieParams]


class SetExtraHTTPHeadersParams(TypedDict):
    """用于设置额外 HTTP 标头的参数。"""

    headers: list[HeaderEntry]


class SetUserAgentOverrideParams(TypedDict):
    """用于覆盖用户代理字符串的参数。"""

    userAgent: str
    acceptLanguage: NotRequired[str]
    platform: NotRequired[str]
    userAgentMetadata: NotRequired[UserAgentMetadata]


class SetBlockedURLsParams(TypedDict):
    """用于阻止 URL 加载的参数。"""

    urls: list[str]


class SetAcceptedEncodingsParams(TypedDict):
    """用于设置接受的内容编码的参数。"""

    encodings: list[ContentEncoding]


class SetAttachDebugStackParams(TypedDict):
    """用于在请求中附加页面脚本堆栈的参数。"""

    enabled: bool


class SetCookieControlsParams(TypedDict):
    """用于设置第三方 cookie 访问控制的参数。"""

    enableThirdPartyCookieRestriction: bool
    disableThirdPartyCookieMetadata: NotRequired[bool]
    disableThirdPartyCookieHeuristics: NotRequired[bool]


class StreamResourceContentParams(TypedDict):
    """用于启用响应流的参数。"""

    requestId: str


class TakeResponseBodyForInterceptionAsStreamParams(TypedDict):
    """用于将响应主体作为流进行拦截的参数。"""

    interceptionId: str


class SetRequestInterceptionParams(TypedDict):
    """用于设置请求拦截模式的参数。"""

    patterns: list[RequestPattern]


class AuthChallengeResponseParams(TypedDict):
    """用于响应身份验证质询的参数。"""

    response: str
    username: NotRequired[str]
    password: NotRequired[str]


class EnableReportingApiParams(TypedDict):
    """用于启用报告 API 的参数。"""

    enabled: bool


class GetSecurityIsolationStatusParams(TypedDict):
    frameId: NotRequired[str]


class LoadNetworkResourceParams(TypedDict):
    """用于加载网络资源的参数。"""

    url: str
    options: LoadNetworkResourceOptions
    frameId: NotRequired[str]


class ReplayXHRParams(TypedDict):
    """用于重放 XMLHttpRequest 的参数。"""

    requestId: str


class GetCookiesResult(TypedDict):
    """getCookies 命令的响应结果。"""

    cookies: list[Cookie]


class GetRequestPostDataResult(TypedDict):
    """getRequestPostData 命令的响应结果。"""

    postData: str


class GetResponseBodyResult(TypedDict):
    """getResponseBody 命令的响应结果。"""

    body: str
    base64Encoded: bool


class GetResponseBodyForInterceptionResult(TypedDict):
    """getResponseBodyForInterception 命令的响应结果。"""

    body: str
    base64Encoded: bool


class GetCertificateResult(TypedDict):
    """getCertificate 命令的响应结果。"""

    tableNames: list[str]


class SearchInResponseBodyResult(TypedDict):
    """searchInResponseBody 命令的响应结果。"""

    result: list[SearchMatch]


class SetCookieResult(TypedDict):
    """setCookie 命令的响应结果。"""

    success: bool


class StreamResourceContentResult(TypedDict):
    """StreamResourceContent 命令的响应结果。"""

    bufferedData: str


class TakeResponseBodyForInterceptionAsStreamResult(TypedDict):
    """takeResponseBodyForInterceptionAsStream 命令的响应结果。"""

    stream: str


class CanClearBrowserCacheResult(TypedDict):
    """canClearBrowserCache 命令的响应结果。"""

    result: bool


class CanClearBrowserCookiesResult(TypedDict):
    """canClearBrowserCookies 命令的响应结果。"""

    result: bool


class CanEmulateNetworkConditionsResult(TypedDict):
    """canEmulateNetworkConditions 命令的响应结果。"""

    result: bool


class GetSecurityIsolationStatusResult(TypedDict):
    """getSecurityIsolationStatus 命令的响应结果。"""

    status: SecurityIsolationStatus


class LoadNetworkResourceResult(TypedDict):
    """loadNetworkResource 命令的响应结果。"""

    success: bool
    netError: NotRequired[float]
    netErrorName: NotRequired[str]
    httpStatusCode: NotRequired[float]
    stream: NotRequired[str]
    headers: NotRequired[list[HeaderEntry]]


GetCookiesResponse = Response[GetCookiesResult]
SetCookieResponse = Response[SetCookieResult]
GetRequestPostDataResponse = Response[GetRequestPostDataResult]
GetResponseBodyResponse = Response[GetResponseBodyResult]
GetResponseBodyForInterceptionResponse = Response[GetResponseBodyForInterceptionResult]
SearchInResponseBodyResponse = Response[SearchInResponseBodyResult]
StreamResourceContentResponse = Response[StreamResourceContentResult]
TakeResponseBodyForInterceptionAsStreamResponse = Response[
    TakeResponseBodyForInterceptionAsStreamResult
]
GetCertificateResponse = Response[GetCertificateResult]
CanClearBrowserCacheResponse = Response[CanClearBrowserCacheResult]
CanClearBrowserCookiesResponse = Response[CanClearBrowserCookiesResult]
CanEmulateNetworkConditionsResponse = Response[CanEmulateNetworkConditionsResult]
GetSecurityIsolationStatusResponse = Response[GetSecurityIsolationStatusResult]
LoadNetworkResourceResponse = Response[LoadNetworkResourceResult]


ClearBrowserCacheCommand = Command[EmptyParams, Response[EmptyResponse]]
ClearBrowserCookiesCommand = Command[EmptyParams, Response[EmptyResponse]]
ClearCookiesCommand = Command[DeleteCookiesParams, Response[EmptyResponse]]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
EmulateNetworkConditionsCommand = Command[EmulateNetworkConditionsParams, Response[EmptyResponse]]
EnableCommand = Command[NetworkEnableParams, Response[EmptyResponse]]
GetCookiesCommand = Command[GetCookiesParams, GetCookiesResponse]
GetRequestPostDataCommand = Command[GetRequestPostDataParams, GetRequestPostDataResponse]
GetResponseBodyCommand = Command[GetResponseBodyParams, GetResponseBodyResponse]
SetCacheDisabledCommand = Command[SetCacheDisabledParams, Response[EmptyResponse]]
SetCookieCommand = Command[SetCookieParams, SetCookieResponse]
SetCookiesCommand = Command[SetCookiesParams, Response[EmptyResponse]]
SetExtraHTTPHeadersCommand = Command[SetExtraHTTPHeadersParams, Response[EmptyResponse]]
SetUserAgentOverrideCommand = Command[SetUserAgentOverrideParams, Response[EmptyResponse]]
ClearAcceptedEncodingsOverrideCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableReportingApiCommand = Command[EnableReportingApiParams, Response[EmptyResponse]]
SearchInResponseBodyCommand = Command[SearchInResponseBodyParams, SearchInResponseBodyResponse]
SetBlockedURLsCommand = Command[SetBlockedURLsParams, Response[EmptyResponse]]
SetBypassServiceWorkerCommand = Command[SetBypassServiceWorkerParams, Response[EmptyResponse]]
GetCertificateCommand = Command[GetCertificateParams, GetCertificateResponse]
GetResponseBodyForInterceptionCommand = Command[
    GetResponseBodyForInterceptionParams, GetResponseBodyForInterceptionResponse
]
SetAcceptedEncodingsCommand = Command[SetAcceptedEncodingsParams, Response[EmptyResponse]]
SetAttachDebugStackCommand = Command[SetAttachDebugStackParams, Response[EmptyResponse]]
SetCookieControlsCommand = Command[SetCookieControlsParams, Response[EmptyResponse]]
StreamResourceContentCommand = Command[StreamResourceContentParams, StreamResourceContentResponse]
TakeResponseBodyForInterceptionAsStreamCommand = Command[
    TakeResponseBodyForInterceptionAsStreamParams, TakeResponseBodyForInterceptionAsStreamResponse
]
GetSecurityIsolationStatusCommand = Command[
    GetSecurityIsolationStatusParams, GetSecurityIsolationStatusResponse
]
LoadNetworkResourceCommand = Command[LoadNetworkResourceParams, LoadNetworkResourceResponse]
ReplayXHRCommand = Command[ReplayXHRParams, Response[EmptyResponse]]
