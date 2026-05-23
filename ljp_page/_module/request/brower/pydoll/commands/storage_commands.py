from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from base import Command
from storage.methods import (
    ClearCookiesParams,
    ClearDataForOriginParams,
    ClearDataForStorageKeyParams,
    ClearSharedStorageEntriesParams,
    ClearTrustTokensParams,
    DeleteSharedStorageEntryParams,
    DeleteStorageBucketParams,
    GetAffectedUrlsForThirdPartyCookieMetadataParams,
    GetCookiesParams,
    GetInterestGroupDetailsParams,
    GetSharedStorageEntriesParams,
    GetSharedStorageMetadataParams,
    GetStorageKeyForFrameParams,
    GetUsageAndQuotaParams,
    OverrideQuotaForOriginParams,
    ResetSharedStorageBudgetParams,
    SetAttributionReportingLocalTestingModeParams,
    SetAttributionReportingTrackingParams,
    SetCookiesParams,
    SetInterestGroupAuctionTrackingParams,
    SetInterestGroupTrackingParams,
    SetProtectedAudienceKAnonymityParams,
    SetSharedStorageEntryParams,
    SetSharedStorageTrackingParams,
    SetStorageBucketTrackingParams,
    StorageMethod,
    TrackCacheStorageForOriginParams,
    TrackCacheStorageForStorageKeyParams,
    TrackIndexedDBForOriginParams,
    TrackIndexedDBForStorageKeyParams,
    UntrackCacheStorageForOriginParams,
    UntrackCacheStorageForStorageKeyParams,
    UntrackIndexedDBForOriginParams,
    UntrackIndexedDBForStorageKeyParams,
)

if TYPE_CHECKING:
    from network.types import CookieParam
    from storage.methods import (
        ClearCookiesCommand,
        ClearDataForOriginCommand,
        ClearDataForStorageKeyCommand,
        ClearSharedStorageEntriesCommand,
        ClearTrustTokensCommand,
        DeleteSharedStorageEntryCommand,
        DeleteStorageBucketCommand,
        GetAffectedUrlsForThirdPartyCookieMetadataCommand,
        GetCookiesCommand,
        GetInterestGroupDetailsCommand,
        GetRelatedWebsiteSetsCommand,
        GetSharedStorageEntriesCommand,
        GetSharedStorageMetadataCommand,
        GetStorageKeyForFrameCommand,
        GetTrustTokensCommand,
        GetUsageAndQuotaCommand,
        OverrideQuotaForOriginCommand,
        ResetSharedStorageBudgetCommand,
        RunBounceTrackingMitigationsCommand,
        SendPendingAttributionReportsCommand,
        SetAttributionReportingLocalTestingModeCommand,
        SetAttributionReportingTrackingCommand,
        SetCookiesCommand,
        SetInterestGroupAuctionTrackingCommand,
        SetInterestGroupTrackingCommand,
        SetProtectedAudienceKAnonymityCommand,
        SetSharedStorageEntryCommand,
        SetSharedStorageTrackingCommand,
        SetStorageBucketTrackingCommand,
        TrackCacheStorageForOriginCommand,
        TrackCacheStorageForStorageKeyCommand,
        TrackIndexedDBForOriginCommand,
        TrackIndexedDBForStorageKeyCommand,
        UntrackCacheStorageForOriginCommand,
        UntrackCacheStorageForStorageKeyCommand,
        UntrackIndexedDBForOriginCommand,
        UntrackIndexedDBForStorageKeyCommand,
    )
    from storage.types import StorageBucket


class StorageCommands:  #编号：PLR0904
    """使用 Chrome DevTools 协议 (CDP) 与浏览器存储交互的类。

    CDP 的存储域允许管理各种类型的浏览器存储，包括：
    - 饼干
    - 缓存存储
    - 索引数据库
    - 网络存储（localStorage/sessionStorage）
    - 共享存储
    - 储物桶
    - 信任代币
    - 兴趣小组
    - 归因报告

    此类提供生成 CDP 命令来管理这些类型的静态方法
    无需传统网络驱动程序即可存储。"""

    @staticmethod
    def clear_cookies(browser_context_id: Optional[str] = None) -> ClearCookiesCommand:
        """生成清除所有浏览器 cookie 的命令。

        参数：
            browser_context_id：浏览器上下文 ID（可选）。工作时有用
                               具有多个上下文（例如，多个窗口或选项卡）。

        返回：
            ClearCookiesCommand：清除所有 cookie 的 CDP 命令。"""
        params = ClearCookiesParams()
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=StorageMethod.CLEAR_COOKIES, params=params)

    @staticmethod
    def clear_data_for_origin(origin: str, storage_types: str) -> ClearDataForOriginCommand:
        """生成命令以清除特定源的存储数据。

        参数：
            origin：安全源（例如“https://example.com”）。
            storage_types：要清除的以逗号分隔的存储类型列表。
                          可能的值包括：“cookies”、“local_storage”、“indexeddb”、
                          “cache_storage”等。使用“all”清除所有类型。

        返回：
            ClearDataForOriginCommand：清除指定源的数据的 CDP 命令。"""
        params = ClearDataForOriginParams(origin=origin, storageTypes=storage_types)
        return Command(method=StorageMethod.CLEAR_DATA_FOR_ORIGIN, params=params)

    @staticmethod
    def clear_data_for_storage_key(
        storage_key: str, storage_types: str
    ) -> ClearDataForStorageKeyCommand:
        """生成命令以清除特定存储密钥的数据。

        参数：
            storage_key：要清除数据的存储键。
                        与 origin 不同，存储密钥是更具体的标识符
                        这可能包括分区隔离。
            storage_types：要清除的以逗号分隔的存储类型列表。
                          可能的值包括：“cookies”、“local_storage”、“indexeddb”、
                          “cache_storage”等。使用“all”清除所有类型。

        返回：
            ClearDataForStorageKeyCommand：清除指定存储的数据的 CDP 命令
                关键。"""
        params = ClearDataForStorageKeyParams(storageKey=storage_key, storageTypes=storage_types)
        return Command(method=StorageMethod.CLEAR_DATA_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def get_cookies(browser_context_id: Optional[str] = None) -> GetCookiesCommand:
        """生成获取所有浏览器 cookie 的命令。

        参数：
            browser_context_id：浏览器上下文 ID（可选）。工作时有用
                               具有多个上下文（例如，多个窗口或选项卡）。

        返回：
            GetCookiesCommand：获取所有cookie的CDP命令，该命令将返回一个数组
                Cookie 对象。"""
        params = GetCookiesParams()
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=StorageMethod.GET_COOKIES, params=params)

    @staticmethod
    def get_storage_key_for_frame(frame_id: str) -> GetStorageKeyForFrameCommand:
        """生成一个命令来获取特定帧的存储密钥。

        存储密钥用于隔离不同来源之间的数据或
        浏览器中的分区。

        参数：
            frame_id：要获取存储密钥的帧的 ID。

        返回：
            GetStorageKeyForFrameCommand：获取指定存储密钥的 CDP 命令
                框架。"""
        params = GetStorageKeyForFrameParams(frameId=frame_id)
        return Command(method=StorageMethod.GET_STORAGE_KEY_FOR_FRAME, params=params)

    @staticmethod
    def get_usage_and_quota(origin: str) -> GetUsageAndQuotaCommand:
        """生成命令以获取源的存储使用情况和配额信息。

        对于监视或调试站点的存储消耗很有用。

        参数：
            origin：要获取信息的安全源（例如“https://example.com”）。

        返回：
            GetUsageAndQuotaCommand：将返回的 CDP 命令：
                - 使用情况：存储使用量（以字节为单位）
                - 配额：存储配额（以字节为单位）
                - 使用情况细分：按存储类型划分的使用情况细分
                - overrideActive：是否存在活动配额覆盖"""
        params = GetUsageAndQuotaParams(origin=origin)
        return Command(method=StorageMethod.GET_USAGE_AND_QUOTA, params=params)

    @staticmethod
    def set_cookies(
        cookies: list[CookieParam], browser_context_id: Optional[str] = None
    ) -> SetCookiesCommand:
        """生成设置浏览器 cookie 的命令。

        参数：
            cookies：要设置的 Cookie 对象列表。
            browser_context_id：浏览器上下文 ID（可选）。工作时有用
                               具有多个上下文（例如，多个窗口或选项卡）。

        返回：
            SetCookiesCommand：用于设置指定 cookie 的 CDP 命令。"""
        params = SetCookiesParams(cookies=cookies)
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=StorageMethod.SET_COOKIES, params=params)

    @staticmethod
    def set_protected_audience_k_anonymity(
        owner: str, name: str, hashes: list[str]
    ) -> SetProtectedAudienceKAnonymityCommand:
        """生成一个命令来为受保护的受众设置 K-匿名。

        该命令用于配置隐私保护广告中的匿名性
        系统（Google 隐私沙箱的一部分）。

        参数：
            所有者：K-匿名配置的所有者。
            name：K-匿名配置的名称。
            hashes：配置的哈希列表。

        返回：
            SetProtectedAudienceKAnonymityCommand：用于设置受保护受众的 CDP 命令
                K-匿名。"""
        params = SetProtectedAudienceKAnonymityParams(owner=owner, name=name, hashes=hashes)
        return Command(method=StorageMethod.SET_PROTECTED_AUDIENCE_K_ANONYMITY, params=params)

    @staticmethod
    def track_cache_storage_for_origin(origin: str) -> TrackCacheStorageForOriginCommand:
        """生成命令来注册源以接收有关更改的通知
        到其缓存存储。

        缓存存储主要由 Service Worker 用于存储资源以供离线使用。

        参数：
            origin：要监控的安全源（例如“https://example.com”）。

        返回：
            TrackCacheStorageForOriginCommand：注册监控的 CDP 命令
                origin 的缓存存储。"""
        params = TrackCacheStorageForOriginParams(origin=origin)
        return Command(method=StorageMethod.TRACK_CACHE_STORAGE_FOR_ORIGIN, params=params)

    @staticmethod
    def track_cache_storage_for_storage_key(
        storage_key: str,
    ) -> TrackCacheStorageForStorageKeyCommand:
        """生成命令来注册存储密钥以接收通知
        关于其缓存存储的更改。

        与 track_cache_storage_for_origin 类似，但使用存储密钥
        以实现更精确的隔离。

        参数：
            storage_key：要监控的存储密钥。

        返回：
            TrackCacheStorageForStorageKeyCommand：注册监控的CDP命令
                密钥的缓存存储。"""
        params = TrackCacheStorageForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.TRACK_CACHE_STORAGE_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def track_indexed_db_for_origin(origin: str) -> TrackIndexedDBForOriginCommand:
        """生成命令来注册源以接收有关更改的通知
        到其 IndexedDB。

        IndexedDB是浏览器中的NoSQL数据库系统，用于存储
        大量结构化数据。

        参数：
            origin：要监控的安全源（例如“https://example.com”）。

        返回：
            TrackIndexedDBForOriginCommand：注册监控的 CDP 命令
                原点的 IndexedDB。"""
        params = TrackIndexedDBForOriginParams(origin=origin)
        return Command(method=StorageMethod.TRACK_INDEXED_DB_FOR_ORIGIN, params=params)

    @staticmethod
    def track_indexed_db_for_storage_key(storage_key: str) -> TrackIndexedDBForStorageKeyCommand:
        """生成命令来注册存储密钥以接收通知
        关于其 IndexedDB 的更改。

        与 track_indexed_db_for_origin 类似，但使用存储密钥
        以实现更精确的隔离。

        参数：
            storage_key：要监控的存储密钥。

        返回：
            TrackIndexedDBForStorageKeyCommand：注册监控的CDP命令
                键的 IndexedDB。"""
        params = TrackIndexedDBForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.TRACK_INDEXED_DB_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def untrack_cache_storage_for_origin(origin: str) -> UntrackCacheStorageForOriginCommand:
        """生成命令以注销接收通知的源
        关于其缓存存储的更改。

        使用此方法可以在使用 track_cache_storage_for_origin 后停止监控缓存存储。

        参数：
            origin：停止监控的安全源（例如“https://example.com”）。

        返回：
            UntrackCacheStorageForOriginCommand：取消监控的 CDP 命令
                origin 的缓存存储。"""
        params = UntrackCacheStorageForOriginParams(origin=origin)
        return Command(method=StorageMethod.UNTRACK_CACHE_STORAGE_FOR_ORIGIN, params=params)

    @staticmethod
    def untrack_cache_storage_for_storage_key(
        storage_key: str,
    ) -> UntrackCacheStorageForStorageKeyCommand:
        """生成命令以取消注册存储密钥以接收通知
        关于其缓存存储的更改。

        使用此方法可以在使用后停止监控Cache Storage
        track_cache_storage_for_storage_key。

        参数：
            storage_key：停止监控的存储键。

        返回：
            UntrackCacheStorageForStorageKeyCommand：取消监控的 CDP 命令
                密钥的缓存存储。"""
        params = UntrackCacheStorageForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.UNTRACK_CACHE_STORAGE_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def untrack_indexed_db_for_origin(origin: str) -> UntrackIndexedDBForOriginCommand:
        """生成命令以注销接收通知的源
        关于其 IndexedDB 的更改。

        使用该方法可以在使用track_indexed_db_for_origin后停止监控IndexedDB。

        参数：
            origin：停止监控的安全源（例如“https://example.com”）。

        返回：
            UntrackIndexedDBForOriginCommand：取消监控的CDP命令
                原点的 IndexedDB。"""
        params = UntrackIndexedDBForOriginParams(origin=origin)
        return Command(method=StorageMethod.UNTRACK_INDEXED_DB_FOR_ORIGIN, params=params)

    @staticmethod
    def untrack_indexed_db_for_storage_key(
        storage_key: str,
    ) -> UntrackIndexedDBForStorageKeyCommand:
        """生成命令以取消注册存储密钥以接收通知
        关于其 IndexedDB 的更改。

        使用此方法可以在使用 track_indexed_db_for_storage_key 后停止监控 IndexedDB。

        参数：
            storage_key：停止监控的存储键。

        返回：
            UntrackIndexedDBForStorageKeyCommand：取消监控的CDP命令
                键的 IndexedDB。"""
        params = UntrackIndexedDBForStorageKeyParams(storageKey=storage_key)
        return Command(method=StorageMethod.UNTRACK_INDEXED_DB_FOR_STORAGE_KEY, params=params)

    @staticmethod
    def clear_shared_storage_entries(owner_origin: str) -> ClearSharedStorageEntriesCommand:
        """生成命令以清除特定源的所有共享存储条目。

        Shared Storage 是一个实验性 API，允许跨域共享存储
        具有隐私保护。

        参数：
            owner_origin：要清除的共享存储的所有者来源。

        返回：
            ClearSharedStorageEntriesCommand：用于清除共享存储条目的 CDP 命令。"""
        params = ClearSharedStorageEntriesParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.CLEAR_SHARED_STORAGE_ENTRIES, params=params)

    @staticmethod
    def clear_trust_tokens(issuer_origin: str) -> ClearTrustTokensCommand:
        """生成命令以删除指定来源颁发的所有信任令牌。

        Trust Tokens 是一个实验性 API，用于在保护用户的同时打击欺诈行为
        隐私。该命令保留其他存储的数据，包括发行人的赎回
        记录，完好无损。

        参数：
            Issuer_origin：要删除的代币的发行者来源。

        返回：
            ClearTrustTokensCommand：清除信任令牌的 CDP 命令，该命令将返回：
                - didDeleteTokens：如果删除了任何令牌，则为 True，否则为 False。"""
        params = ClearTrustTokensParams(issuerOrigin=issuer_origin)
        return Command(method=StorageMethod.CLEAR_TRUST_TOKENS, params=params)

    @staticmethod
    def delete_shared_storage_entry(owner_origin: str, key: str) -> DeleteSharedStorageEntryCommand:
        """生成删除特定共享存储条目的命令。

        参数：
            owner_origin：共享存储的所有者来源。
            key：要删除的条目的键。

        返回：
            DeleteSharedStorageEntryCommand：用于删除共享存储条目的 CDP 命令。"""
        params = DeleteSharedStorageEntryParams(ownerOrigin=owner_origin, key=key)
        return Command(method=StorageMethod.DELETE_SHARED_STORAGE_ENTRY, params=params)

    @staticmethod
    def delete_storage_bucket(bucket: StorageBucket) -> DeleteStorageBucketCommand:
        """生成命令以删除具有指定键和名称的存储桶。

        存储桶是一个实验性 API，用于管理存储数据
        更大的粒度和过期控制。

        参数：
            Bucket：一个StorageBucket对象，包含存储桶的storageKey和名称
                删除。

        返回：
            DeleteStorageBucketCommand：用于删除存储桶的 CDP 命令。"""
        params = DeleteStorageBucketParams(bucket=bucket)
        return Command(method=StorageMethod.DELETE_STORAGE_BUCKET, params=params)

    @staticmethod
    def get_affected_urls_for_third_party_cookie_metadata(
        first_party_url: str, third_party_urls: list[str]
    ) -> GetAffectedUrlsForThirdPartyCookieMetadataCommand:
        """生成一个命令以从页面及其嵌入资源获取 URL 列表
        与现有宽限期 URL 模式规则匹配。

        此命令对于监控哪些 URL 将受到影响非常有用
        Privacy Sandbox 的第三方 cookie 政策。

        参数：
            first_party_url：正在访问的页面的 URL（第一方）。
            Third_party_urls：嵌入式第三方资源 URL 的可选列表。

        返回：
            GetAffectedUrlsForThirdPartyCookieMetadataCommand：用于获取 URL 的 CDP 命令
                受第三方 cookie 元数据的影响。"""
        params = GetAffectedUrlsForThirdPartyCookieMetadataParams(
            firstPartyUrl=first_party_url, thirdPartyUrls=third_party_urls
        )
        return Command(
            method=StorageMethod.GET_AFFECTED_URLS_FOR_THIRD_PARTY_COOKIE_METADATA, params=params
        )

    @staticmethod
    def get_interest_group_details(owner_origin: str, name: str) -> GetInterestGroupDetailsCommand:
        """生成命令以获取特定兴趣组的详细信息。

        兴趣组是 FLEDGE/Protected Audience API 的一部分，用于保护隐私
        广告，支持浏览器内广告拍卖。

        参数：
            owner_origin：兴趣组的所有者来源。
            名称：兴趣小组的名称。

        返回：
            GetInterestGroupDetailsCommand：用于获取兴趣组详细信息的 CDP 命令。"""
        params = GetInterestGroupDetailsParams(ownerOrigin=owner_origin, name=name)
        return Command(method=StorageMethod.GET_INTEREST_GROUP_DETAILS, params=params)

    @staticmethod
    def get_related_website_sets() -> GetRelatedWebsiteSetsCommand:
        """生成获取相关网站集的命令。

        相关网站集是一个 API，允许同一实体下的网站
        尽管第三方 cookie 存在限制，但仍可共享一些数据。

        返回：
            GetRelatedWebsiteSetsCommand：用于获取相关网站集的 CDP 命令。"""
        return Command(method=StorageMethod.GET_RELATED_WEBSITE_SETS)

    @staticmethod
    def get_shared_storage_entries(owner_origin: str) -> GetSharedStorageEntriesCommand:
        """生成命令以获取源的所有共享存储条目。

        参数：
            owner_origin：共享存储的所有者来源。

        返回：
            GetSharedStorageEntriesCommand：用于获取共享存储条目的 CDP 命令。"""
        params = GetSharedStorageEntriesParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.GET_SHARED_STORAGE_ENTRIES, params=params)

    @staticmethod
    def get_shared_storage_metadata(owner_origin: str) -> GetSharedStorageMetadataCommand:
        """生成命令以获取源的共享存储元数据。

        元数据包括使用情况、预算和创建时间等信息。

        参数：
            owner_origin：共享存储的所有者来源。

        返回：
            GetSharedStorageMetadataCommand：用于获取共享存储元数据的 CDP 命令。"""
        params = GetSharedStorageMetadataParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.GET_SHARED_STORAGE_METADATA, params=params)

    @staticmethod
    def get_trust_tokens() -> GetTrustTokensCommand:
        """生成一个命令来获取所有可用的信任令牌。

        返回：
            GetTrustTokensCommand：获取信任令牌的 CDP 命令，它将返回对
                    发行人来源和可用代币数量。"""
        return Command(method=StorageMethod.GET_TRUST_TOKENS, params={})

    @staticmethod
    def override_quota_for_origin(
        origin: str, quota_size: Optional[float] = None
    ) -> OverrideQuotaForOriginCommand:
        """生成命令来覆盖特定源的存储配额。

        此命令对于存储耗尽测试或模拟很有用
        不同的储存条件。

        参数：
            来源：要覆盖配额的来源。
            quota_size：新配额的大小（以字节为单位）（可选）。
                       如果未指定，任何现有的覆盖都将被删除。

        返回：
            OverrideQuotaForOriginCommand：用于覆盖源配额的 CDP 命令。"""
        params = OverrideQuotaForOriginParams(origin=origin)
        if quota_size is not None:
            params['quotaSize'] = quota_size
        return Command(method=StorageMethod.OVERRIDE_QUOTA_FOR_ORIGIN, params=params)

    @staticmethod
    def reset_shared_storage_budget(owner_origin: str) -> ResetSharedStorageBudgetCommand:
        """生成一个命令来重置源的共享存储预算。

        共享存储使用预算系统来限制操作量
        或保护用户隐私的特定操作。

        参数：
            owner_origin：共享存储的所有者来源。

        返回：
            ResetSharedStorageBudgetCommand：用于重置共享存储预算的 CDP 命令。"""
        params = ResetSharedStorageBudgetParams(ownerOrigin=owner_origin)
        return Command(method=StorageMethod.RESET_SHARED_STORAGE_BUDGET, params=params)

    @staticmethod
    def run_bounce_tracking_mitigations() -> RunBounceTrackingMitigationsCommand:
        """生成命令来运行跳出跟踪缓解措施。

        跳出跟踪是一种涉及重定向用户的跟踪技术
        通过中间 URL 建立跟踪 cookie。
        此命令激活针对此技术的保护。

        返回：
            RunBounceTrackingMitigationsCommand：用于运行跳出跟踪缓解措施的 CDP 命令。"""
        return Command(method=StorageMethod.RUN_BOUNCE_TRACKING_MITIGATIONS, params={})

    @staticmethod
    def send_pending_attribution_reports() -> SendPendingAttributionReportsCommand:
        """生成发送待处理归因报告的命令。

        归因报告是一个 API，允许在测量转化的同时
        保护用户隐私。该命令强制发送报告
        正在等待发送。

        返回：
            SendPendingAttributionReportsCommand：发送待处理归因的 CDP 命令
                报告。"""
        return Command(method=StorageMethod.SEND_PENDING_ATTRIBUTION_REPORTS, params={})

    @staticmethod
    def set_attribution_reporting_local_testing_mode(
        enabled: bool,
    ) -> SetAttributionReportingLocalTestingModeCommand:
        """生成命令以启用或禁用归因报告的本地测试模式。

        测试模式使开发和测试归因报告 API 变得更加容易
        取消通常适用的延迟和速率限制等限制。

        参数：
            enabled：True 表示启用本地测试模式，False 表示禁用它。

        返回：
            SetAttributionReportingLocalTestingModeCommand：用于设置归因的 CDP 命令
                报告本地测试模式。"""
        params = SetAttributionReportingLocalTestingModeParams(enabled=enabled)
        return Command(
            method=StorageMethod.SET_ATTRIBUTION_REPORTING_LOCAL_TESTING_MODE, params=params
        )

    @staticmethod
    def set_attribution_reporting_tracking(enable: bool) -> SetAttributionReportingTrackingCommand:
        """生成命令以启用或禁用归因报告跟踪。

        参数：
            启用：True 启用跟踪，False 禁用它。

        返回：
            SetAttributionReportingTrackingCommand：用于设置归因的 CDP 命令
                报告跟踪。"""
        params = SetAttributionReportingTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_ATTRIBUTION_REPORTING_TRACKING, params=params)

    @staticmethod
    def set_interest_group_auction_tracking(enable: bool) -> SetInterestGroupAuctionTrackingCommand:
        """生成命令以启用或禁用兴趣组拍卖跟踪。

        兴趣小组拍卖是 FLEDGE/Protected Audience API 的一部分，并且
        允许以保护隐私的方式进行浏览器内广告拍卖。

        参数：
            启用：True 启用跟踪，False 禁用它。

        返回：
            SetInterestGroupAuctionTrackingCommand：设置兴趣组的 CDP 命令
                拍卖跟踪。"""
        params = SetInterestGroupAuctionTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_INTEREST_GROUP_AUCTION_TRACKING, params=params)

    @staticmethod
    def set_interest_group_tracking(enable: bool) -> SetInterestGroupTrackingCommand:
        """生成命令以启用或禁用兴趣组跟踪。

        参数：
            启用：True 启用跟踪，False 禁用它。

        返回：
            SetInterestGroupTrackingCommand：用于设置兴趣组跟踪的 CDP 命令。"""
        params = SetInterestGroupTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_INTEREST_GROUP_TRACKING, params=params)

    @staticmethod
    def set_shared_storage_entry(
        owner_origin: str, key: str, value: str, ignore_if_present: Optional[bool] = None
    ) -> SetSharedStorageEntryCommand:
        """生成命令以设置共享存储中的条目。

        参数：
            owner_origin：共享存储的所有者来源。
            key：要设置的条目的键。
            value：要设置的条目的值。
            ignore_if_present：如果为 True，则不会用相同的键替换现有条目。

        返回：
            SetSharedStorageEntryCommand：用于设置共享存储条目的 CDP 命令。"""
        params = SetSharedStorageEntryParams(ownerOrigin=owner_origin, key=key, value=value)
        if ignore_if_present is not None:
            params['ignoreIfPresent'] = ignore_if_present
        return Command(method=StorageMethod.SET_SHARED_STORAGE_ENTRY, params=params)

    @staticmethod
    def set_shared_storage_tracking(enable: bool) -> SetSharedStorageTrackingCommand:
        """生成命令以启用或禁用共享存储跟踪。

        启用后，将发出与共享存储使用相关的事件。

        参数：
            启用：True 启用跟踪，False 禁用它。

        返回：
            SetSharedStorageTrackingCommand：用于设置共享存储跟踪的 CDP 命令。"""
        params = SetSharedStorageTrackingParams(enable=enable)
        return Command(method=StorageMethod.SET_SHARED_STORAGE_TRACKING, params=params)

    @staticmethod
    def set_storage_bucket_tracking(
        storage_key: str, enable: bool
    ) -> SetStorageBucketTrackingCommand:
        """生成命令以启用或禁用存储桶跟踪。

        启用后，将发出与存储桶更改相关的事件。

        参数：
            storage_key：要设置跟踪的存储密钥。
            启用：True 启用跟踪，False 禁用它。

        返回：
            SetStorageBucketTrackingCommand：用于设置存储桶跟踪的 CDP 命令。"""
        params = SetStorageBucketTrackingParams(storageKey=storage_key, enable=enable)
        return Command(method=StorageMethod.SET_STORAGE_BUCKET_TRACKING, params=params)
