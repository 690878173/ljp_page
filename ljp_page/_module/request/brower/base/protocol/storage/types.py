from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ..network.types import TimeSinceEpoch
from ..target.types import TargetID

SerializedStorageKey = str
InterestGroupAuctionId = str


class StorageType(str, Enum):
    COOKIES = 'cookies'
    FILE_SYSTEMS = 'file_systems'
    INDEXEDDB = 'indexeddb'
    LOCAL_STORAGE = 'local_storage'
    SHADER_CACHE = 'shader_cache'
    WEBSQL = 'websql'
    SERVICE_WORKERS = 'service_workers'
    CACHE_STORAGE = 'cache_storage'
    INTEREST_GROUPS = 'interest_groups'
    SHARED_STORAGE = 'shared_storage'
    STORAGE_BUCKETS = 'storage_buckets'
    ALL = 'all'
    OTHER = 'other'


class UsageForType(TypedDict):
    """存储类型的用法。"""

    storageType: StorageType
    usage: float


class TrustTokens(TypedDict):
    """一对发行人来源和可用（已签名，但未使用）信托数量
    来自该发行人的代币。"""

    issuerOrigin: str
    count: float


class InterestGroupAccessType(str, Enum):
    """兴趣组访问类型的枚举。"""

    JOIN = 'join'
    LEAVE = 'leave'
    UPDATE = 'update'
    LOADED = 'loaded'
    BID = 'bid'
    WIN = 'win'
    ADDITIONAL_BID = 'additionalBid'
    ADDITIONAL_BID_WIN = 'additionalBidWin'
    TOP_LEVEL_BID = 'topLevelBid'
    TOP_LEVEL_ADDITIONAL_BID = 'topLevelAdditionalBid'
    CLEAR = 'clear'


class InterestGroupAuctionEventType(str, Enum):
    """拍卖事件的枚举。"""

    STARTED = 'started'
    CONFIG_RESOLVED = 'configResolved'


class InterestGroupAuctionFetchType(str, Enum):
    """网络获取拍卖可以做的枚举。"""

    BIDDER_JS = 'bidderJs'
    BIDDER_WASM = 'bidderWasm'
    SELLER_JS = 'sellerJs'
    BIDDER_TRUSTED_SIGNALS = 'bidderTrustedSignals'
    SELLER_TRUSTED_SIGNALS = 'sellerTrustedSignals'


class SharedStorageAccessScope(str, Enum):
    """共享存储访问范围的枚举。"""

    WINDOW = 'window'
    SHARED_STORAGE_WORKLET = 'sharedStorageWorklet'
    PROTECTED_AUDIENCE_WORKLET = 'protectedAudienceWorklet'
    HEADER = 'header'


class SharedStorageAccessMethod(str, Enum):
    """共享存储访问方法的枚举。"""

    ADD_MODULE = 'addModule'
    CREATE_WORKLET = 'createWorklet'
    SELECT_URL = 'selectURL'
    RUN = 'run'
    BATCH_UPDATE = 'batchUpdate'
    SET = 'set'
    APPEND = 'append'
    DELETE = 'delete'
    CLEAR = 'clear'
    GET = 'get'
    KEYS = 'keys'
    VALUES = 'values'
    ENTRIES = 'entries'
    LENGTH = 'length'
    REMAINING_BUDGET = 'remainingBudget'


class SharedStorageEntry(TypedDict):
    """源共享存储中单个键值对的结构。"""

    key: str
    value: str


class SharedStorageMetadata(TypedDict):
    """源共享存储的详细信息。"""

    creationTime: TimeSinceEpoch
    length: int
    remainingBudget: float
    bytesUsed: int


class SharedStoragePrivateAggregationConfig(TypedDict):
    """表示作为 privateAggregationConfig 传入的字典对象
    运行或选择URL。"""

    filteringIdMaxBytes: int
    aggregationCoordinatorOrigin: NotRequired[str]
    contextId: NotRequired[str]
    maxContributions: NotRequired[int]


class SharedStorageReportingMetadata(TypedDict):
    """`selectURL()` 的候选 URL 的一对报告元数据详细信息。"""

    eventType: str
    reportingUrl: str


class SharedStorageUrlWithMetadata(TypedDict):
    """将候选 URL 与其报告元数据捆绑在一起。"""

    url: str
    reportingMetadata: list[SharedStorageReportingMetadata]


class SharedStorageAccessParams(TypedDict, total=False):
    """捆绑共享存储访问事件的参数，其
    存在/不存在可能会根据 SharedStorageAccessType 的不同而有所不同。"""

    scriptSourceUrl: str
    dataOrigin: str
    operationName: str
    operationId: str
    keepAlive: bool
    privateAggregationConfig: SharedStoragePrivateAggregationConfig
    serializedData: str
    urlsWithMetadata: list[SharedStorageUrlWithMetadata]
    urnUuid: str
    key: str
    value: str
    ignoreIfPresent: bool
    workletOrdinal: int
    workletTargetId: TargetID
    withLock: str
    batchUpdateId: str
    batchSize: int


class StorageBucketsDurability(str, Enum):
    RELAXED = 'relaxed'
    STRICT = 'strict'


class StorageBucket(TypedDict):
    storageKey: SerializedStorageKey
    name: NotRequired[str]


class StorageBucketInfo(TypedDict):
    bucket: StorageBucket
    id: str
    expiration: TimeSinceEpoch
    quota: float
    persistent: bool
    durability: StorageBucketsDurability


class AttributionReportingSourceType(str, Enum):
    NAVIGATION = 'navigation'
    EVENT = 'event'


UnsignedInt64AsBase10 = str
UnsignedInt128AsBase16 = str
SignedInt64AsBase10 = str


class AttributionReportingFilterDataEntry(TypedDict):
    key: str
    values: list[str]


class AttributionReportingFilterConfig(TypedDict):
    filterValues: list[AttributionReportingFilterDataEntry]
    lookbackWindow: NotRequired[int]


class AttributionReportingFilterPair(TypedDict):
    filters: list[AttributionReportingFilterConfig]
    notFilters: list[AttributionReportingFilterConfig]


class AttributionReportingAggregationKeysEntry(TypedDict):
    key: str
    value: UnsignedInt128AsBase16


class AttributionReportingEventReportWindows(TypedDict):
    start: int
    ends: list[int]


class AttributionReportingTriggerDataMatching(str, Enum):
    EXACT = 'exact'
    MODULUS = 'modulus'


class AttributionReportingAggregatableDebugReportingData(TypedDict):
    keyPiece: UnsignedInt128AsBase16
    value: float
    types: list[str]


class AttributionReportingAggregatableDebugReportingConfig(TypedDict):
    keyPiece: UnsignedInt128AsBase16
    debugData: list[AttributionReportingAggregatableDebugReportingData]
    budget: NotRequired[float]
    aggregationCoordinatorOrigin: NotRequired[str]


class AttributionScopesData(TypedDict):
    values: list[str]
    limit: float
    maxEventStates: float


class AttributionReportingNamedBudgetDef(TypedDict):
    name: str
    budget: int


class AttributionReportingSourceRegistration(TypedDict):
    time: TimeSinceEpoch
    expiry: int
    triggerData: list[float]
    eventReportWindows: AttributionReportingEventReportWindows
    aggregatableReportWindow: int
    type: AttributionReportingSourceType
    sourceOrigin: str
    reportingOrigin: str
    destinationSites: list[str]
    eventId: UnsignedInt64AsBase10
    priority: SignedInt64AsBase10
    filterData: list[AttributionReportingFilterDataEntry]
    aggregationKeys: list[AttributionReportingAggregationKeysEntry]
    triggerDataMatching: AttributionReportingTriggerDataMatching
    destinationLimitPriority: SignedInt64AsBase10
    aggregatableDebugReportingConfig: AttributionReportingAggregatableDebugReportingConfig
    maxEventLevelReports: int
    namedBudgets: list[AttributionReportingNamedBudgetDef]
    debugReporting: bool
    eventLevelEpsilon: float
    debugKey: NotRequired[UnsignedInt64AsBase10]
    scopesData: NotRequired[AttributionScopesData]


class AttributionReportingSourceRegistrationResult(str, Enum):
    SUCCESS = 'success'
    INTERNAL_ERROR = 'internalError'
    INSUFFICIENT_SOURCE_CAPACITY = 'insufficientSourceCapacity'
    INSUFFICIENT_UNIQUE_DESTINATION_CAPACITY = 'insufficientUniqueDestinationCapacity'
    EXCESSIVE_REPORTING_ORIGINS = 'excessiveReportingOrigins'
    PROHIBITED_BY_BROWSER_POLICY = 'prohibitedByBrowserPolicy'
    SUCCESS_NOISED = 'successNoised'
    DESTINATION_REPORTING_LIMIT_REACHED = 'destinationReportingLimitReached'
    DESTINATION_GLOBAL_LIMIT_REACHED = 'destinationGlobalLimitReached'
    DESTINATION_BOTH_LIMITS_REACHED = 'destinationBothLimitsReached'
    REPORTING_ORIGINS_PER_SITE_LIMIT_REACHED = 'reportingOriginsPerSiteLimitReached'
    EXCEEDS_MAX_CHANNEL_CAPACITY = 'exceedsMaxChannelCapacity'
    EXCEEDS_MAX_SCOPES_CHANNEL_CAPACITY = 'exceedsMaxScopesChannelCapacity'
    EXCEEDS_MAX_TRIGGER_STATE_CARDINALITY = 'exceedsMaxTriggerStateCardinality'
    EXCEEDS_MAX_EVENT_STATES_LIMIT = 'exceedsMaxEventStatesLimit'
    DESTINATION_PER_DAY_REPORTING_LIMIT_REACHED = 'destinationPerDayReportingLimitReached'


class AttributionReportingSourceRegistrationTimeConfig(str, Enum):
    INCLUDE = 'include'
    EXCLUDE = 'exclude'


class AttributionReportingAggregatableValueDictEntry(TypedDict):
    key: str
    value: float
    filteringId: UnsignedInt64AsBase10


class AttributionReportingAggregatableValueEntry(TypedDict):
    values: list[AttributionReportingAggregatableValueDictEntry]
    filters: AttributionReportingFilterPair


class AttributionReportingEventTriggerData(TypedDict):
    data: UnsignedInt64AsBase10
    priority: SignedInt64AsBase10
    filters: AttributionReportingFilterPair
    dedupKey: NotRequired[UnsignedInt64AsBase10]


class AttributionReportingAggregatableTriggerData(TypedDict):
    keyPiece: UnsignedInt128AsBase16
    sourceKeys: list[str]
    filters: AttributionReportingFilterPair


class AttributionReportingAggregatableDedupKey(TypedDict):
    filters: AttributionReportingFilterPair
    dedupKey: NotRequired[UnsignedInt64AsBase10]


class AttributionReportingNamedBudgetCandidate(TypedDict):
    filters: AttributionReportingFilterPair
    name: NotRequired[str]


class AttributionReportingTriggerRegistration(TypedDict):
    filters: AttributionReportingFilterPair
    aggregatableDedupKeys: list[AttributionReportingAggregatableDedupKey]
    eventTriggerData: list[AttributionReportingEventTriggerData]
    aggregatableTriggerData: list[AttributionReportingAggregatableTriggerData]
    aggregatableValues: list[AttributionReportingAggregatableValueEntry]
    aggregatableFilteringIdMaxBytes: int
    debugReporting: bool
    sourceRegistrationTimeConfig: AttributionReportingSourceRegistrationTimeConfig
    aggregatableDebugReportingConfig: AttributionReportingAggregatableDebugReportingConfig
    scopes: list[str]
    namedBudgets: list[AttributionReportingNamedBudgetCandidate]
    debugKey: NotRequired[UnsignedInt64AsBase10]
    aggregationCoordinatorOrigin: NotRequired[str]
    triggerContextId: NotRequired[str]


class AttributionReportingEventLevelResult(str, Enum):
    SUCCESS = 'success'
    SUCCESS_DROPPED_LOWER_PRIORITY = 'successDroppedLowerPriority'
    INTERNAL_ERROR = 'internalError'
    NO_CAPACITY_FOR_ATTRIBUTION_DESTINATION = 'noCapacityForAttributionDestination'
    NO_MATCHING_SOURCES = 'noMatchingSources'
    DEDUPLICATED = 'deduplicated'
    EXCESSIVE_ATTRIBUTIONS = 'excessiveAttributions'
    PRIORITY_TOO_LOW = 'priorityTooLow'
    NEVER_ATTRIBUTED_SOURCE = 'neverAttributedSource'
    EXCESSIVE_REPORTING_ORIGINS = 'excessiveReportingOrigins'
    NO_MATCHING_SOURCE_FILTER_DATA = 'noMatchingSourceFilterData'
    PROHIBITED_BY_BROWSER_POLICY = 'prohibitedByBrowserPolicy'
    NO_MATCHING_CONFIGURATIONS = 'noMatchingConfigurations'
    EXCESSIVE_REPORTS = 'excessiveReports'
    FALSELY_ATTRIBUTED_SOURCE = 'falselyAttributedSource'
    REPORT_WINDOW_PASSED = 'reportWindowPassed'
    NOT_REGISTERED = 'notRegistered'
    REPORT_WINDOW_NOT_STARTED = 'reportWindowNotStarted'
    NO_MATCHING_TRIGGER_DATA = 'noMatchingTriggerData'


class AttributionReportingAggregatableResult(str, Enum):
    SUCCESS = 'success'
    INTERNAL_ERROR = 'internalError'
    NO_CAPACITY_FOR_ATTRIBUTION_DESTINATION = 'noCapacityForAttributionDestination'
    NO_MATCHING_SOURCES = 'noMatchingSources'
    EXCESSIVE_ATTRIBUTIONS = 'excessiveAttributions'
    EXCESSIVE_REPORTING_ORIGINS = 'excessiveReportingOrigins'
    NO_HISTOGRAMS = 'noHistograms'
    INSUFFICIENT_BUDGET = 'insufficientBudget'
    INSUFFICIENT_NAMED_BUDGET = 'insufficientNamedBudget'
    NO_MATCHING_SOURCE_FILTER_DATA = 'noMatchingSourceFilterData'
    NOT_REGISTERED = 'notRegistered'
    PROHIBITED_BY_BROWSER_POLICY = 'prohibitedByBrowserPolicy'
    DEDUPLICATED = 'deduplicated'
    REPORT_WINDOW_PASSED = 'reportWindowPassed'
    EXCESSIVE_REPORTS = 'excessiveReports'


class AttributionReportingReportResult(str, Enum):
    SENT = 'sent'
    PROHIBITED = 'prohibited'
    FAILED_TO_ASSEMBLE = 'failedToAssemble'
    EXPIRED = 'expired'


class RelatedWebsiteSet(TypedDict):
    primarySites: list[str]
    associatedSites: list[str]
    serviceSites: list[str]
