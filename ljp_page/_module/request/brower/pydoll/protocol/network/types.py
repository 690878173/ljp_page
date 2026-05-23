from enum import Enum

from typing_extensions import NotRequired, TypedDict

from runtime.types import StackTrace
from security.types import MixedContentType, SecurityState


class ResourceType(str, Enum):
    """渲染引擎感知的资源类型。"""

    DOCUMENT = 'Document'
    STYLESHEET = 'Stylesheet'
    IMAGE = 'Image'
    MEDIA = 'Media'
    FONT = 'Font'
    SCRIPT = 'Script'
    TEXT_TRACK = 'TextTrack'
    XHR = 'XHR'
    FETCH = 'Fetch'
    PREFETCH = 'Prefetch'
    EVENT_SOURCE = 'EventSource'
    WEB_SOCKET = 'WebSocket'
    MANIFEST = 'Manifest'
    SIGNED_EXCHANGE = 'SignedExchange'
    PING = 'Ping'
    CSP_VIOLATION_REPORT = 'CSPViolationReport'
    PREFLIGHT = 'Preflight'
    FED_CM = 'FedCM'
    OTHER = 'Other'


LoaderId = str
RequestId = str
InterceptionId = str


class ErrorReason(str, Enum):
    """网络级获取失败原因。"""

    FAILED = 'Failed'
    ABORTED = 'Aborted'
    TIMED_OUT = 'TimedOut'
    ACCESS_DENIED = 'AccessDenied'
    CONNECTION_CLOSED = 'ConnectionClosed'
    CONNECTION_RESET = 'ConnectionReset'
    CONNECTION_REFUSED = 'ConnectionRefused'
    CONNECTION_ABORTED = 'ConnectionAborted'
    CONNECTION_FAILED = 'ConnectionFailed'
    NAME_NOT_RESOLVED = 'NameNotResolved'
    INTERNET_DISCONNECTED = 'InternetDisconnected'
    ADDRESS_UNREACHABLE = 'AddressUnreachable'
    BLOCKED_BY_CLIENT = 'BlockedByClient'
    BLOCKED_BY_RESPONSE = 'BlockedByResponse'


TimeSinceEpoch = float
MonotonicTime = float
Headers = dict[str, str]


class RequestMethod(str, Enum):
    """HTTP 请求方法。"""

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'


class ConnectionType(str, Enum):
    """浏览器应该使用的底层连接技术。"""

    NONE = 'none'
    CELLULAR2G = 'cellular2g'
    CELLULAR3G = 'cellular3g'
    CELLULAR4G = 'cellular4g'
    BLUETOOTH = 'bluetooth'
    ETHERNET = 'ethernet'
    WIFI = 'wifi'
    WIMAX = 'wimax'
    OTHER = 'other'


class CookieSameSite(str, Enum):
    """代表 cookie 的“SameSite”状态"""

    STRICT = 'Strict'
    LAX = 'Lax'
    NONE = 'None'


class CookiePriority(str, Enum):
    """代表 cookie 的“优先”状态"""

    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'


class CookieSourceScheme(str, Enum):
    """表示最初设置cookie的源的源方案。
    “Unset”值允许协议客户端模拟该方案的旧 cookie 范围。
    这是暂时的能力，将来会被删除。"""

    UNSET = 'Unset'
    NON_SECURE = 'NonSecure'
    SECURE = 'Secure'


class ResourceTiming(TypedDict):
    """请求的时间信息。"""

    requestTime: float
    proxyStart: float
    proxyEnd: float
    dnsStart: float
    dnsEnd: float
    connectStart: float
    connectEnd: float
    sslStart: float
    sslEnd: float
    workerStart: float
    workerReady: float
    workerFetchStart: float
    workerRespondWithSettled: float
    workerRouterEvaluationStart: NotRequired[float]
    workerCacheLookupStart: NotRequired[float]
    sendStart: float
    sendEnd: float
    pushStart: float
    pushEnd: float
    receiveHeadersStart: float
    receiveHeadersEnd: float


class ResourcePriority(str, Enum):
    """资源请求的加载优先级。"""

    VERY_LOW = 'VeryLow'
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    VERY_HIGH = 'VeryHigh'


class PostDataEntry(TypedDict):
    """HTTP 请求的 Post 数据输入"""

    bytes: NotRequired[str]


class Request(TypedDict):
    """HTTP 请求数据。"""

    url: str
    urlFragment: NotRequired[str]
    method: str
    headers: 'Headers'
    postData: NotRequired[str]
    hasPostData: NotRequired[bool]
    postDataEntries: NotRequired[list['PostDataEntry']]
    mixedContentType: NotRequired['MixedContentType']
    initialPriority: 'ResourcePriority'
    referrerPolicy: str
    isLinkPreload: NotRequired[bool]
    trustTokenParams: NotRequired['TrustTokenParams']
    isSameSite: NotRequired[bool]


class SignedCertificateTimestamp(TypedDict):
    """签名证书时间戳 (SCT) 的详细信息。"""

    status: str
    origin: str
    logDescription: str
    logId: str
    timestamp: float
    hashAlgorithm: str
    signatureAlgorithm: str
    signatureData: str


class SecurityDetails(TypedDict):
    """有关请求的安全详细信息。"""

    protocol: str
    keyExchange: str
    keyExchangeGroup: NotRequired[str]
    cipher: str
    mac: NotRequired[str]
    certificateId: int
    subjectName: str
    sanList: list[str]
    issuer: str
    validFrom: 'TimeSinceEpoch'
    validTo: 'TimeSinceEpoch'
    signedCertificateTimestampList: list['SignedCertificateTimestamp']
    certificateTransparencyCompliance: 'CertificateTransparencyCompliance'
    serverSignatureAlgorithm: NotRequired[int]
    encryptedClientHello: bool


class CertificateTransparencyCompliance(str, Enum):
    """请求是否符合证书透明度政策。"""

    UNKNOWN = 'unknown'
    NOT_COMPLIANT = 'not-compliant'
    COMPLIANT = 'compliant'


class BlockedReason(str, Enum):
    """请求被阻止的原因。"""

    OTHER = 'other'
    CSP = 'csp'
    MIXED_CONTENT = 'mixed-content'
    ORIGIN = 'origin'
    INSPECTOR = 'inspector'
    INTEGRITY = 'integrity'
    SUBRESOURCE_FILTER = 'subresource-filter'
    CONTENT_TYPE = 'content-type'
    COEP_FRAME_RESOURCE_NEEDS_COEP_HEADER = 'coep-frame-resource-needs-coep-header'
    COOP_SANDBOXED_IFRAME_CANNOT_NAVIGATE_TO_COOP_PAGE = (
        'coop-sandboxed-iframe-cannot-navigate-to-coop-page'
    )
    CORP_NOT_SAME_ORIGIN = 'corp-not-same-origin'
    CORP_NOT_SAME_ORIGIN_AFTER_DEFAULTED_TO_SAME_ORIGIN_BY_COEP = (
        'corp-not-same-origin-after-defaulted-to-same-origin-by-coep'
    )
    CORP_NOT_SAME_ORIGIN_AFTER_DEFAULTED_TO_SAME_ORIGIN_BY_DIP = (
        'corp-not-same-origin-after-defaulted-to-same-origin-by-dip'
    )
    CORP_NOT_SAME_ORIGIN_AFTER_DEFAULTED_TO_SAME_ORIGIN_BY_COEP_AND_DIP = (
        'corp-not-same-origin-after-defaulted-to-same-origin-by-coep-and-dip'
    )
    CORP_NOT_SAME_SITE = 'corp-not-same-site'
    SRI_MESSAGE_SIGNATURE_MISMATCH = 'sri-message-signature-mismatch'


class CorsError(str, Enum):
    """请求被阻止的原因。"""

    DISALLOWED_BY_MODE = 'DisallowedByMode'
    INVALID_RESPONSE = 'InvalidResponse'
    WILDCARD_ORIGIN_NOT_ALLOWED = 'WildcardOriginNotAllowed'
    MISSING_ALLOW_ORIGIN_HEADER = 'MissingAllowOriginHeader'
    MULTIPLE_ALLOW_ORIGIN_VALUES = 'MultipleAllowOriginValues'
    INVALID_ALLOW_ORIGIN_VALUE = 'InvalidAllowOriginValue'
    ALLOW_ORIGIN_MISMATCH = 'AllowOriginMismatch'
    INVALID_ALLOW_CREDENTIALS = 'InvalidAllowCredentials'
    CORS_DISABLED_SCHEME = 'CorsDisabledScheme'
    PREFLIGHT_INVALID_STATUS = 'PreflightInvalidStatus'
    PREFLIGHT_DISALLOWED_REDIRECT = 'PreflightDisallowedRedirect'
    PREFLIGHT_WILDCARD_ORIGIN_NOT_ALLOWED = 'PreflightWildcardOriginNotAllowed'
    PREFLIGHT_MISSING_ALLOW_ORIGIN_HEADER = 'PreflightMissingAllowOriginHeader'
    PREFLIGHT_MULTIPLE_ALLOW_ORIGIN_VALUES = 'PreflightMultipleAllowOriginValues'
    PREFLIGHT_INVALID_ALLOW_ORIGIN_VALUE = 'PreflightInvalidAllowOriginValue'
    PREFLIGHT_ALLOW_ORIGIN_MISMATCH = 'PreflightAllowOriginMismatch'
    PREFLIGHT_INVALID_ALLOW_CREDENTIALS = 'PreflightInvalidAllowCredentials'
    PREFLIGHT_MISSING_ALLOW_EXTERNAL = 'PreflightMissingAllowExternal'
    PREFLIGHT_INVALID_ALLOW_EXTERNAL = 'PreflightInvalidAllowExternal'
    PREFLIGHT_MISSING_ALLOW_PRIVATE_NETWORK = 'PreflightMissingAllowPrivateNetwork'
    PREFLIGHT_INVALID_ALLOW_PRIVATE_NETWORK = 'PreflightInvalidAllowPrivateNetwork'
    INVALID_ALLOW_METHODS_PREFLIGHT_RESPONSE = 'InvalidAllowMethodsPreflightResponse'
    INVALID_ALLOW_HEADERS_PREFLIGHT_RESPONSE = 'InvalidAllowHeadersPreflightResponse'
    METHOD_DISALLOWED_BY_PREFLIGHT_RESPONSE = 'MethodDisallowedByPreflightResponse'
    HEADER_DISALLOWED_BY_PREFLIGHT_RESPONSE = 'HeaderDisallowedByPreflightResponse'
    REDIRECT_CONTAINS_CREDENTIALS = 'RedirectContainsCredentials'
    INSECURE_PRIVATE_NETWORK = 'InsecurePrivateNetwork'
    INVALID_PRIVATE_NETWORK_ACCESS = 'InvalidPrivateNetworkAccess'
    UNEXPECTED_PRIVATE_NETWORK_ACCESS = 'UnexpectedPrivateNetworkAccess'
    NO_CORS_REDIRECT_MODE_NOT_FOLLOW = 'NoCorsRedirectModeNotFollow'
    PREFLIGHT_MISSING_PRIVATE_NETWORK_ACCESS_ID = 'PreflightMissingPrivateNetworkAccessId'
    PREFLIGHT_MISSING_PRIVATE_NETWORK_ACCESS_NAME = 'PreflightMissingPrivateNetworkAccessName'
    PRIVATE_NETWORK_ACCESS_PERMISSION_UNAVAILABLE = 'PrivateNetworkAccessPermissionUnavailable'
    PRIVATE_NETWORK_ACCESS_PERMISSION_DENIED = 'PrivateNetworkAccessPermissionDenied'
    LOCAL_NETWORK_ACCESS_PERMISSION_DENIED = 'LocalNetworkAccessPermissionDenied'


class CorsErrorStatus(TypedDict):
    corsError: CorsError
    failedParameter: str


class ServiceWorkerResponseSource(str, Enum):
    """ServiceWorker 响应的来源。"""

    CACHE_STORAGE = 'cache-storage'
    HTTP_CACHE = 'http-cache'
    FALLBACK_CODE = 'fallback-code'
    NETWORK = 'network'


class TrustTokenParams(TypedDict):
    """确定执行什么类型的信任令牌操作，并根据类型，
    一些附加参数。这些值在中指定
    Third_party/blink/renderer/core/fetch/trust_token.idl。"""

    operation: 'TrustTokenOperationType'
    refreshPolicy: str
    issuers: NotRequired[list[str]]


class TrustTokenOperationType(str, Enum):
    ISSUANCE = 'Issuance'
    REDEMPTION = 'Redemption'
    SIGNING = 'Signing'


class AlternateProtocolUsage(str, Enum):
    """Chrome之所以使用特定的传输协议来实现HTTP语义。"""

    ALTERNATIVE_JOB_WON_WITHOUT_RACE = 'alternativeJobWonWithoutRace'
    ALTERNATIVE_JOB_WON_RACE = 'alternativeJobWonRace'
    MAIN_JOB_WON_RACE = 'mainJobWonRace'
    MAPPING_MISSING = 'mappingMissing'
    BROKEN = 'broken'
    DNS_ALPN_H3_JOB_WON_WITHOUT_RACE = 'dnsAlpnH3JobWonWithoutRace'
    DNS_ALPN_H3_JOB_WON_RACE = 'dnsAlpnH3JobWonRace'
    UNSPECIFIED_REASON = 'unspecifiedReason'


class ServiceWorkerRouterSource(str, Enum):
    """Service Worker 路由器的来源。"""

    NETWORK = 'network'
    CACHE = 'cache'
    FETCH_EVENT = 'fetch-event'
    RACE_NETWORK_AND_FETCH_HANDLER = 'race-network-and-fetch-handler'


class ServiceWorkerRouterInfo(TypedDict):
    ruleIdMatched: NotRequired[int]
    matchedSourceType: NotRequired['ServiceWorkerRouterSource']
    actualSourceType: NotRequired['ServiceWorkerRouterSource']


class Response(TypedDict):
    """HTTP 响应数据。"""

    url: str
    status: int
    statusText: str
    headers: 'Headers'
    headersText: NotRequired[str]
    mimeType: str
    charset: str
    requestHeaders: NotRequired['Headers']
    requestHeadersText: NotRequired[str]
    connectionReused: bool
    connectionId: float
    remoteIPAddress: NotRequired[str]
    remotePort: NotRequired[int]
    fromDiskCache: NotRequired[bool]
    fromServiceWorker: NotRequired[bool]
    fromPrefetchCache: NotRequired[bool]
    fromEarlyHints: NotRequired[bool]
    serviceWorkerRouterInfo: NotRequired['ServiceWorkerRouterInfo']
    encodedDataLength: float
    timing: NotRequired['ResourceTiming']
    serviceWorkerResponseSource: NotRequired[ServiceWorkerResponseSource]
    responseTime: NotRequired['TimeSinceEpoch']
    cacheStorageCacheName: NotRequired[str]
    protocol: NotRequired[str]
    alternateProtocolUsage: NotRequired[AlternateProtocolUsage]
    securityState: SecurityState
    securityDetails: NotRequired['SecurityDetails']
    isIpProtectionUsed: NotRequired[bool]


class WebSocketRequest(TypedDict):
    """WebSocket 请求数据。"""

    headers: 'Headers'


class WebSocketResponse(TypedDict):
    """WebSocket 响应数据。"""

    status: int
    statusText: str
    headers: 'Headers'
    headersText: NotRequired[str]
    requestHeaders: NotRequired['Headers']
    requestHeadersText: NotRequired[str]


class WebSocketFrame(TypedDict):
    """WebSocket 消息数据。这代表整个 WebSocket 消息，
    不仅仅是顾名思义的一个支离破碎的框架。"""

    opcode: float
    mask: bool
    payloadData: str


class CachedResource(TypedDict):
    """有关缓存资源的信息。"""

    url: str
    type: ResourceType
    response: NotRequired['Response']
    bodySize: float


class Initiator(TypedDict):
    """有关请求发起者的信息。"""

    type: str
    stack: NotRequired[StackTrace]
    url: NotRequired[str]
    lineNumber: NotRequired[float]
    columnNumber: NotRequired[float]
    requestId: NotRequired[RequestId]


class CookiePartitionKey(TypedDict):
    """cookiePartitionKey 对象。所创建密钥的组成部分的表示
    通过 net/cookies/cookie_partition_key.h 中包含的 cookiePartitionKey 类。"""

    topLevelSite: str
    hasCrossSiteAncestor: bool


class Cookie(TypedDict):
    """Cookie 对象"""

    name: str
    value: str
    domain: str
    path: str
    expires: float
    size: int
    httpOnly: bool
    secure: bool
    session: bool
    sameSite: NotRequired[CookieSameSite]
    priority: NotRequired[CookiePriority]
    sameParty: NotRequired[bool]
    sourceScheme: NotRequired[CookieSourceScheme]
    sourcePort: int
    partitionKey: NotRequired['CookiePartitionKey']


class SetCookieBlockedReason(str, Enum):
    """无法从响应中存储 cookie 的原因类型。"""

    SECURE_ONLY = 'SecureOnly'
    SAME_SITE_STRICT = 'SameSiteStrict'
    SAME_SITE_LAX = 'SameSiteLax'
    SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SameSiteUnspecifiedTreatedAsLax'
    SAME_SITE_NONE_INSECURE = 'SameSiteNoneInsecure'
    USER_PREFERENCES = 'UserPreferences'
    THIRD_PARTY_PHASEOUT = 'ThirdPartyPhaseout'
    THIRD_PARTY_BLOCKED_IN_FIRST_PARTY_SET = 'ThirdPartyBlockedInFirstPartySet'
    SYNTAX_ERROR = 'SyntaxError'
    SCHEME_NOT_SUPPORTED = 'SchemeNotSupported'
    OVERWRITE_SECURE = 'OverwriteSecure'
    INVALID_DOMAIN = 'InvalidDomain'
    INVALID_PREFIX = 'InvalidPrefix'
    UNKNOWN_ERROR = 'UnknownError'
    SCHEMEFUL_SAME_SITE_STRICT = 'SchemefulSameSiteStrict'
    SCHEMEFUL_SAME_SITE_LAX = 'SchemefulSameSiteLax'
    SCHEMEFUL_SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SchemefulSameSiteUnspecifiedTreatedAsLax'
    SAME_PARTY_FROM_CROSS_PARTY_CONTEXT = 'SamePartyFromCrossPartyContext'
    SAME_PARTY_CONFLICTS_WITH_OTHER_ATTRIBUTES = 'SamePartyConflictsWithOtherAttributes'
    NAME_VALUE_PAIR_EXCEEDS_MAX_SIZE = 'NameValuePairExceedsMaxSize'
    DISALLOWED_CHARACTER = 'DisallowedCharacter'
    NO_COOKIE_CONTENT = 'NoCookieContent'


class CookieBlockedReason(str, Enum):
    """cookie 不能与请求一起发送的原因类型。"""

    SECURE_ONLY = 'SecureOnly'
    NOT_ON_PATH = 'NotOnPath'
    DOMAIN_MISMATCH = 'DomainMismatch'
    SAME_SITE_STRICT = 'SameSiteStrict'
    SAME_SITE_LAX = 'SameSiteLax'
    SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SameSiteUnspecifiedTreatedAsLax'
    SAME_SITE_NONE_INSECURE = 'SameSiteNoneInsecure'
    USER_PREFERENCES = 'UserPreferences'
    THIRD_PARTY_PHASEOUT = 'ThirdPartyPhaseout'
    THIRD_PARTY_BLOCKED_IN_FIRST_PARTY_SET = 'ThirdPartyBlockedInFirstPartySet'
    UNKNOWN_ERROR = 'UnknownError'
    SCHEMEFUL_SAME_SITE_STRICT = 'SchemefulSameSiteStrict'
    SCHEMEFUL_SAME_SITE_LAX = 'SchemefulSameSiteLax'
    SCHEMEFUL_SAME_SITE_UNSPECIFIED_TREATED_AS_LAX = 'SchemefulSameSiteUnspecifiedTreatedAsLax'
    SAME_PARTY_FROM_CROSS_PARTY_CONTEXT = 'SamePartyFromCrossPartyContext'
    NAME_VALUE_PAIR_EXCEEDS_MAX_SIZE = 'NameValuePairExceedsMaxSize'
    PORT_MISMATCH = 'PortMismatch'
    SCHEME_MISMATCH = 'SchemeMismatch'
    ANONYMOUS_CONTEXT = 'AnonymousContext'


class CookieExemptionReason(str, Enum):
    """Cookie 本应被 3PCD 阻止但请求豁免的原因类型。"""

    NONE = 'None'
    USER_SETTING = 'UserSetting'
    TPCD_METADATA = 'TPCDMetadata'
    TPCD_DEPRECATION_TRIAL = 'TPCDDeprecationTrial'
    TOP_LEVEL_TPCD_DEPRECATION_TRIAL = 'TopLevelTPCDDeprecationTrial'
    TPCD_HEURISTICS = 'TPCDHeuristics'
    ENTERPRISE_POLICY = 'EnterprisePolicy'
    STORAGE_ACCESS = 'StorageAccess'
    TOP_LEVEL_STORAGE_ACCESS = 'TopLevelStorageAccess'
    SCHEME = 'Scheme'
    SAME_SITE_NONE_COOKIES_IN_SANDBOX = 'SameSiteNoneCookiesInSandbox'


class BlockedSetCookieWithReason(TypedDict):
    """由于相应原因而未从响应中存储的 cookie。"""

    blockedReasons: list[SetCookieBlockedReason]
    cookieLine: str
    cookie: NotRequired['Cookie']


class ExemptedSetCookieWithReason(TypedDict):
    """cookie 应该被 3PCD 阻止，但可以从响应中豁免并存储
    相应的原因。 Cookie 最多只能有一个豁免原因。"""

    exemptionReason: CookieExemptionReason
    cookieLine: str
    cookie: 'Cookie'


class AssociatedCookie(TypedDict):
    """与请求关联的 cookie，可能会也可能不会随请求一起发送。
    包括 cookie 本身以及阻止或豁免的原因。"""

    cookie: 'Cookie'
    blockedReasons: list[CookieBlockedReason]
    exemptionReason: NotRequired[CookieExemptionReason]


class CookieParam(TypedDict):
    """Cookie参数对象"""

    name: str
    value: str
    url: NotRequired[str]
    domain: NotRequired[str]
    path: NotRequired[str]
    secure: NotRequired[bool]
    httpOnly: NotRequired[bool]
    sameSite: NotRequired[CookieSameSite]
    expires: NotRequired['TimeSinceEpoch']
    priority: NotRequired[CookiePriority]
    sameParty: NotRequired[bool]
    sourceScheme: NotRequired[CookieSourceScheme]
    sourcePort: NotRequired[int]
    partitionKey: NotRequired['CookiePartitionKey']


class AuthChallenge(TypedDict):
    """HTTP 状态代码 401 或 407 的授权质询。"""

    source: NotRequired[str]
    origin: str
    scheme: str
    realm: str


class AuthChallengeResponse(TypedDict):
    """对 AuthChallenge 的响应。"""

    response: str
    username: NotRequired[str]
    password: NotRequired[str]


class InterceptionStage(str, Enum):
    """拦截阶段开始拦截。 request会在请求之前拦截
    已发送。收到响应后将拦截响应。"""

    REQUEST = 'Request'
    HEADERS_RECEIVED = 'HeadersReceived'


class RequestPattern(TypedDict):
    """拦截的请求模式。"""

    urlPattern: NotRequired[str]
    resourceType: NotRequired[ResourceType]
    interceptionStage: NotRequired[InterceptionStage]


class SignedExchangeSignature(TypedDict):
    """有关已签名交换签名的信息。"""

    label: str
    signature: str
    integrity: str
    certUrl: NotRequired[str]
    certSha256: NotRequired[str]
    validityUrl: str
    date: int
    expires: int
    certificates: NotRequired[list[str]]


class SignedExchangeHeader(TypedDict):
    """有关签名交换标头的信息。"""

    requestUrl: str
    responseCode: int
    responseHeaders: 'Headers'
    signatures: list[SignedExchangeSignature]
    headerIntegrity: str


class SignedExchangeErrorField(str, Enum):
    """签名交换相关错误的字段类型。"""

    SIGNATURE_SIG = 'signatureSig'
    SIGNATURE_INTEGRITY = 'signatureIntegrity'
    SIGNATURE_CERT_URL = 'signatureCertUrl'
    SIGNATURE_CERT_SHA256 = 'signatureCertSha256'
    SIGNATURE_VALIDITY_URL = 'signatureValidityUrl'
    SIGNATURE_TIMESTAMPS = 'signatureTimestamps'


class SignedExchangeError(TypedDict):
    """有关已签名交换响应的信息。"""

    message: str
    signatureIndex: NotRequired[int]
    errorField: NotRequired[SignedExchangeErrorField]


class SignedExchangeInfo(TypedDict):
    """有关已签名交换响应的信息。"""

    outerResponse: 'Response'
    hasExtraInfo: bool
    header: NotRequired[SignedExchangeHeader]
    securityDetails: NotRequired['SecurityDetails']
    errors: NotRequired[list[SignedExchangeError]]


class ContentEncoding(str, Enum):
    """后端支持的内容编码列表。"""

    DEFLATE = 'deflate'
    GZIP = 'gzip'
    BR = 'br'
    ZSTD = 'zstd'


class DirectSocketDnsQueryType(str, Enum):
    IPV4 = 'ipv4'
    IPV6 = 'ipv6'


class DirectTCPSocketOptions(TypedDict):
    noDelay: bool
    keepAliveDelay: NotRequired[float]
    sendBufferSize: NotRequired[float]
    receiveBufferSize: NotRequired[float]
    dnsQueryType: NotRequired[DirectSocketDnsQueryType]


class DirectUDPSocketOptions(TypedDict):
    remoteAddr: NotRequired[str]
    remotePort: NotRequired[int]
    localAddr: NotRequired[str]
    localPort: NotRequired[int]
    dnsQueryType: NotRequired[DirectSocketDnsQueryType]
    sendBufferSize: NotRequired[float]
    receiveBufferSize: NotRequired[float]


class DirectUDPMessage(TypedDict):
    data: str
    remoteAddr: NotRequired[str]
    remotePort: NotRequired[int]


class PrivateNetworkRequestPolicy(str, Enum):
    ALLOW = 'Allow'
    BLOCK_FROM_INSECURE_TO_MORE_PRIVATE = 'BlockFromInsecureToMorePrivate'
    WARN_FROM_INSECURE_TO_MORE_PRIVATE = 'WarnFromInsecureToMorePrivate'
    PREFLIGHT_BLOCK = 'PreflightBlock'
    PREFLIGHT_WARN = 'PreflightWarn'


class IPAddressSpace(str, Enum):
    LOOPBACK = 'Loopback'
    LOCAL = 'Local'
    PUBLIC = 'Public'
    UNKNOWN = 'Unknown'


class ConnectTiming(TypedDict):
    requestTime: float


class ClientSecurityState(TypedDict):
    initiatorIsSecureContext: bool
    initiatorIPAddressSpace: IPAddressSpace
    privateNetworkRequestPolicy: PrivateNetworkRequestPolicy


class CrossOriginOpenerPolicyValue(str, Enum):
    SAME_ORIGIN = 'SameOrigin'
    SAME_ORIGIN_ALLOW_POPUPS = 'SameOriginAllowPopups'
    RESTRICT_PROPERTIES = 'RestrictProperties'
    UNSAFE_NONE = 'UnsafeNone'
    SAME_ORIGIN_PLUS_COEP = 'SameOriginPlusCoep'
    RESTRICT_PROPERTIES_PLUS_COEP = 'RestrictPropertiesPlusCoep'
    NO_OPENER_ALLOW_POPUPS = 'NoopenerAllowPopups'


class CrossOriginOpenerPolicyStatus(TypedDict):
    value: CrossOriginOpenerPolicyValue
    reportOnlyValue: CrossOriginOpenerPolicyValue
    reportingEndpoint: NotRequired[str]
    reportOnlyReportingEndpoint: NotRequired[str]


class CrossOriginEmbedderPolicyValue(str, Enum):
    NONE = 'None'
    CREDENTIALLESS = 'Credentialless'
    REQUIRE_CORP = 'RequireCorp'


class CrossOriginEmbedderPolicyStatus(TypedDict):
    value: CrossOriginEmbedderPolicyValue
    reportOnlyValue: CrossOriginEmbedderPolicyValue
    reportingEndpoint: NotRequired[str]
    reportOnlyReportingEndpoint: NotRequired[str]


class ContentSecurityPolicySource(str, Enum):
    HTTP = 'HTTP'
    META = 'Meta'


class ContentSecurityPolicyStatus(TypedDict):
    effectiveDirectives: str
    isEnforced: bool
    source: ContentSecurityPolicySource


class SecurityIsolationStatus(TypedDict):
    coop: NotRequired[CrossOriginOpenerPolicyStatus]
    coep: NotRequired[CrossOriginEmbedderPolicyStatus]
    csp: NotRequired[list[ContentSecurityPolicyStatus]]


class ReportStatus(str, Enum):
    """Reporting API 报告的状态。"""

    QUEUED = 'Queued'
    PENDING = 'Pending'
    MARKED_FOR_REMOVAL = 'MarkedForRemoval'
    SUCCESS = 'Success'


class ReportId(str):
    pass


class ReportingApiReport(TypedDict):
    """表示由 Reporting API 生成的报告的对象。"""

    id: ReportId
    initiatorUrl: str
    destination: str
    type: str
    timestamp: TimeSinceEpoch
    depth: int
    completedAttempts: int
    body: dict
    status: ReportStatus


class ReportingApiEndpoint(TypedDict):
    url: str
    groupName: str


class LoadNetworkResourcePageResult(TypedDict):
    """提供网络资源负载结果的对象。"""

    success: bool
    netError: NotRequired[float]
    netErrorName: NotRequired[str]
    httpStatusCode: NotRequired[float]
    stream: NotRequired[str]
    headers: NotRequired['Headers']


class LoadNetworkResourceOptions(TypedDict):
    """一个选项对象，稍后可能会扩展以更好地支持 CORS、CORB 和流。"""

    disableCache: bool
    includeCredentials: bool
