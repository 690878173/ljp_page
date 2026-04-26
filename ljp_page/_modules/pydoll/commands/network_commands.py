from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ljp_page._modules.pydoll.protocol.base import Command
from ljp_page._modules.pydoll.protocol.network.methods import (
    DeleteCookiesParams,
    EmulateNetworkConditionsParams,
    EnableReportingApiParams,
    GetCertificateParams,
    GetCookiesParams,
    GetRequestPostDataParams,
    GetResponseBodyForInterceptionParams,
    GetResponseBodyParams,
    GetSecurityIsolationStatusParams,
    LoadNetworkResourceParams,
    NetworkEnableParams,
    NetworkMethod,
    ReplayXHRParams,
    SearchInResponseBodyParams,
    SetAcceptedEncodingsParams,
    SetAttachDebugStackParams,
    SetBlockedURLsParams,
    SetBypassServiceWorkerParams,
    SetCacheDisabledParams,
    SetCookieControlsParams,
    SetCookieParams,
    SetCookiesParams,
    SetExtraHTTPHeadersParams,
    SetUserAgentOverrideParams,
    StreamResourceContentParams,
    TakeResponseBodyForInterceptionAsStreamParams,
)

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.protocol.emulation.types import UserAgentMetadata
    from ljp_page._modules.pydoll.protocol.network.methods import (
        ClearAcceptedEncodingsOverrideCommand,
        ClearBrowserCacheCommand,
        ClearBrowserCookiesCommand,
        ClearCookiesCommand,
        DisableCommand,
        EmulateNetworkConditionsCommand,
        EnableCommand,
        EnableReportingApiCommand,
        GetCertificateCommand,
        GetCookiesCommand,
        GetRequestPostDataCommand,
        GetResponseBodyCommand,
        GetResponseBodyForInterceptionCommand,
        GetSecurityIsolationStatusCommand,
        HeaderEntry,
        LoadNetworkResourceCommand,
        ReplayXHRCommand,
        SearchInResponseBodyCommand,
        SetAcceptedEncodingsCommand,
        SetAttachDebugStackCommand,
        SetBlockedURLsCommand,
        SetBypassServiceWorkerCommand,
        SetCacheDisabledCommand,
        SetCookieCommand,
        SetCookieControlsCommand,
        SetCookiesCommand,
        SetExtraHTTPHeadersCommand,
        SetUserAgentOverrideCommand,
        StreamResourceContentCommand,
        TakeResponseBodyForInterceptionAsStreamCommand,
    )
    from ljp_page._modules.pydoll.protocol.network.types import (
        ConnectionType,
        ContentEncoding,
        CookiePartitionKey,
        CookiePriority,
        CookieSameSite,
        CookieSourceScheme,
        LoadNetworkResourceOptions,
    )


class NetworkCommands:
    """针对网络域的 Chrome DevTools 协议的实现。

    此类提供用于监视和操作网络活动的命令，
    启用对 HTTP 请求和响应的详细检查和控制。
    网络域公开了全面的网络相关信息，包括：
    - 请求/响应标头和正文
    - 资源计时和缓存行为
    - Cookie 管理和安全详细信息
    - 网络条件模拟
    - 流量拦截和修改

    这些命令允许开发人员分析性能、调试网络问题、
    并测试各种网络条件下的应用程序行为。"""

    @staticmethod
    def clear_browser_cache() -> ClearBrowserCacheCommand:
        """清除浏览器缓存存储。

        此命令对于测试缓存行为并确保新鲜至关重要
        资源加载。它会影响所有缓存的资源，包括：
        - CSS/JavaScript 文件
        - 图像和媒体资产
        - API响应缓存

        使用案例：
        - 测试缓存失效策略
        - 重现陈旧内容的问题
        - 不受缓存影响的性能基准测试

        返回：
            命令：CDP命令清除整个浏览器缓存"""
        return Command(method=NetworkMethod.CLEAR_BROWSER_CACHE)

    @staticmethod
    def clear_browser_cookies() -> ClearBrowserCookiesCommand:
        """清除浏览器中存储的所有 cookie 的命令。

        这对于测试您需要的场景很有帮助
        模拟一个没有任何先前存储的新用户会话
        可能影响应用程序行为的 cookie。

        返回：
            命令[响应]：清除浏览器中所有cookie的命令。"""
        return Command(method=NetworkMethod.CLEAR_BROWSER_COOKIES)

    @staticmethod
    def delete_cookies(
        name: str,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        path: Optional[str] = None,
        partition_key: Optional[CookiePartitionKey] = None,
    ) -> ClearCookiesCommand:
        """删除符合条件的浏览器 cookie。

        通过多个参数提供对 cookie 删除的精细控制：
        - 仅按名称删除（影响所有匹配的 cookie）
        - 使用 URL、域或路径删除范围
        - 处理隐私意识应用程序的分区cookie

        参数：
            name：要删除的 cookie 的名称（必填）
            url：删除特定 URL 的 cookie（域/路径必须匹配）
            域：删除 cookie 的确切域
            path：删除cookie的确切路径
            partition_key：用于cookie隔离的分区键属性

        返回：
            命令：执行选择性 cookie 删除的 CDP 命令"""
        params = DeleteCookiesParams(name=name)
        if url is not None:
            params['url'] = url
        if domain is not None:
            params['domain'] = domain
        if path is not None:
            params['path'] = path
        if partition_key is not None:
            params['partitionKey'] = partition_key
        return Command(method=NetworkMethod.DELETE_COOKIES, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """停止网络监控和事件报告。

        保留网络状态但停止：
        - 请求/响应事件
        - WebSocket消息跟踪
        - 加载进度通知

        使用时：
        - 减少非网络操作期间的开销
        - 暂时暂停监控
        - 完成网络相关测试

        返回：
            命令：CDP命令禁用网络监控"""
        return Command(method=NetworkMethod.DISABLE)

    @staticmethod
    def enable(
        max_total_buffer_size: Optional[int] = None,
        max_resource_buffer_size: Optional[int] = None,
        max_post_data_size: Optional[int] = None,
    ) -> EnableCommand:
        """通过可配置的缓冲区启用网络监控。

        参数：
            max_total_buffer_size：网络数据的总内存缓冲区（字节）
            max_resource_buffer_size：每个资源缓冲区限制（字节）
            max_post_data_size：要捕获的最大 POST 负载（字节）

        推荐设置：
        - 增加长时间运行会话的缓冲区
        - 调整 API 测试的帖子大小
        - 使用大缓冲区监视内存使用情况

        返回：
            命令：CDP命令启用网络监控"""
        params = NetworkEnableParams()
        if max_total_buffer_size is not None:
            params['maxTotalBufferSize'] = max_total_buffer_size
        if max_resource_buffer_size is not None:
            params['maxResourceBufferSize'] = max_resource_buffer_size
        if max_post_data_size is not None:
            params['maxPostDataSize'] = max_post_data_size
        return Command(method=NetworkMethod.ENABLE, params=params)

    @staticmethod
    def get_cookies(
        urls: Optional[list[str]] = None,
    ) -> GetCookiesCommand:
        """检索与指定 URL 匹配的 cookie。

        参数：
            urls：用于 cookie 检索范围的 URL 列表

        返回：
            命令：CDP 命令返回 cookie 详细信息，包括：
                - 名称、值和属性
                - 安全性和范围参数
                - 有效期和尺寸信息

        使用注意事项：
        - 空 URL 列表返回所有 cookie
        - 包括仅 HTTP 和安全 cookie
        - 显示分区 cookie 状态"""
        params = GetCookiesParams()
        if urls is not None:
            params['urls'] = urls
        return Command(method=NetworkMethod.GET_COOKIES, params=params)

    @staticmethod
    def get_request_post_data(
        request_id: str,
    ) -> GetRequestPostDataCommand:
        """从特定网络请求检索 POST 数据。

        必不可少：
        - 表单提交分析
        - API请求调试
        - 文件上传监控
        - 安全测试

        参数：
            request_id：网络请求的唯一标识符

        返回：
            命令：CDP 命令，返回：
                - 原始POST数据内容
                - 多部分表单数据（不包括文件内容）
                - 内容编码信息

        注意：根据缓冲区设置，大型 POST 正文可能会被截断"""
        params = GetRequestPostDataParams(requestId=request_id)
        return Command(method=NetworkMethod.GET_REQUEST_POST_DATA, params=params)

    @staticmethod
    def get_response_body(
        request_id: str,
    ) -> GetResponseBodyCommand:
        """检索网络响应的完整内容。

        支持各种内容类型：
        - 基于文本的资源（HTML、CSS、JSON）
        - Base64 编码的二进制内容（图像、媒体）
        - Gzip/deflate 压缩响应

        参数：
            request_id：唯一的网络请求标识符

        重要考虑因素：
        - 响应必须在浏览器内存中可用
        - 大量响应可能需要流式处理方法
        - 敏感数据应得到安全处理

        返回：
            命令：返回响应正文和编码详细信息的 CDP 命令"""
        params = GetResponseBodyParams(requestId=request_id)
        return Command(method=NetworkMethod.GET_RESPONSE_BODY, params=params)

    @staticmethod
    def set_cache_disabled(cache_disabled: bool) -> SetCacheDisabledCommand:
        """控制浏览器的缓存机制。

        使用案例：
        - 测试资源更新行为
        - 强制加载新内容
        - 性能影响分析
        - 缓存破坏场景

        参数：
            cache_disabled：True 表示禁用缓存，False 表示启用

        返回：
            命令：修改缓存行为的 CDP 命令

        注意：影响所有请求，直到重新启用"""
        params = SetCacheDisabledParams(cacheDisabled=cache_disabled)
        return Command(method=NetworkMethod.SET_CACHE_DISABLED, params=params)

    @staticmethod
    def set_cookie(
        name: str,
        value: str,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        path: Optional[str] = None,
        secure: Optional[bool] = None,
        http_only: Optional[bool] = None,
        same_site: Optional[CookieSameSite] = None,
        expires: Optional[float] = None,
        priority: Optional[CookiePriority] = None,
        same_party: Optional[bool] = None,
        source_scheme: Optional[CookieSourceScheme] = None,
        source_port: Optional[int] = None,
        partition_key: Optional[CookiePartitionKey] = None,
    ) -> SetCookieCommand:
        """创建或更新具有指定属性的 cookie。

        全面的 cookie 控制支持：
        - 会话和持久cookie
        - 安全属性（安全、HttpOnly）
        - SameSite 政策
        - Cookie 分区
        - 优先级

        参数：
            名称：Cookie 名称
            value: Cookie 值
            url：cookie 的目标 URL
            域：Cookie 域范围
            路径：Cookie 路径范围
            安全：需要 HTTPS
            http_only：阻止 JavaScript 访问
            same_site：跨站访问策略
            过期：过期时间戳
            优先级：Cookie 优先级
            same_party：第一方设置标志
            source_scheme：Cookie 源上下文
            source_port：源端口限制
            partition_key：存储分区键

        返回：
            Command：返回成功状态的CDP命令

        安全考虑：
        - 对敏感数据使用安全标志
        - 考虑 SameSite 策略
        - 注意跨站点影响"""
        params = SetCookieParams(name=name, value=value)

        if url is not None:
            params['url'] = url
        if domain is not None:
            params['domain'] = domain
        if path is not None:
            params['path'] = path
        if secure is not None:
            params['secure'] = secure
        if http_only is not None:
            params['httpOnly'] = http_only
        if same_site is not None:
            params['sameSite'] = same_site
        if expires is not None:
            params['expires'] = expires
        if priority is not None:
            params['priority'] = priority
        if same_party is not None:
            params['sameParty'] = same_party
        if source_scheme is not None:
            params['sourceScheme'] = source_scheme
        if source_port is not None:
            params['sourcePort'] = source_port
        if partition_key is not None:
            params['partitionKey'] = partition_key

        return Command(method=NetworkMethod.SET_COOKIE, params=params)

    @staticmethod
    def set_cookies(cookies: list[SetCookieParams]) -> SetCookiesCommand:
        """在一次操作中设置多个 cookie。

        有效用于：
        - 批量cookie操作
        - 会话状态恢复
        - 测试多种身份验证状态
        - 跨域cookie设置

        参数：
            cookies：cookie参数列表，包括
                    名称、值和属性

        返回：
            命令：用于批量 cookie 设置的 CDP 命令

        性能说明：
        - 比多次 set_cookie 调用更高效
        - 考虑大批量的内存影响"""
        params = SetCookiesParams(cookies=cookies)
        return Command(method=NetworkMethod.SET_COOKIES, params=params)

    @staticmethod
    def set_extra_http_headers(
        headers: list[HeaderEntry],
    ) -> SetExtraHTTPHeadersCommand:
        """将自定义 HTTP 标头应用于所有后续请求。

        启用高级场景：
        - 使用自定义标头进行 A/B 测试
        - 测试时绕过身份验证
        - 内容谈判模拟
        - 安全标头验证

        参数：
            headers：键值头对列表

        安全注意事项：
        - 标头在浏览器范围内应用
        - 敏感标头（例如授权）持续存在直至清除
        - 在共享环境中谨慎使用

        返回：
            命令：用于设置全局 HTTP 标头的 CDP 命令"""
        params = SetExtraHTTPHeadersParams(headers=headers)
        return Command(method=NetworkMethod.SET_EXTRA_HTTP_HEADERS, params=params)

    @staticmethod
    def set_useragent_override(
        user_agent: str,
        accept_language: Optional[str] = None,
        platform: Optional[str] = None,
        user_agent_metadata: Optional[UserAgentMetadata] = None,
    ) -> SetUserAgentOverrideCommand:
        """覆盖浏览器的用户代理字符串。

        使用案例：
        - 设备/浏览器模拟
        - 兼容性测试
        - 内容协商
        - 机器人检测绕过

        参数：
            user_agent：完整的用户代理字符串
            Accept_language：语言首选项标头
            平台：平台标识符
            user_agent_metadata：详细的UA元数据

        返回：
            命令：覆盖用户代理的 CDP 命令

        测试注意事项：
        - 影响所有后续请求
        - 可能会影响服务器端行为
        - 考虑移动/桌面差异"""
        params = SetUserAgentOverrideParams(userAgent=user_agent)
        if accept_language is not None:
            params['acceptLanguage'] = accept_language
        if platform is not None:
            params['platform'] = platform
        if user_agent_metadata is not None:
            params['userAgentMetadata'] = user_agent_metadata
        return Command(method=NetworkMethod.SET_USER_AGENT_OVERRIDE, params=params)

    @staticmethod
    def clear_accepted_encodings_override() -> ClearAcceptedEncodingsOverrideCommand:
        """恢复默认内容编码接受。

        效果：
        - 重置压缩首选项
        - 恢复默认的 Accept-Encoding 标头
        - 允许服务器选择编码

        使用时：
        - 测试编码回退
        - 调试压缩问题
        - 编码测试后重置

        返回：
            命令：清除编码覆盖的 CDP 命令"""
        return Command(method=NetworkMethod.CLEAR_ACCEPTED_ENCODINGS_OVERRIDE)

    @staticmethod
    def enable_reporting_api(
        enabled: bool,
    ) -> EnableReportingApiCommand:
        """控制报告 API 功能。

        特点：
        - 网络错误报告
        - 弃用通知
        - CSP 违规报告
        - CORS问题

        参数：
            已启用：True 表示启用，False 表示禁用

        返回：
            命令：用于配置报告 API 的 CDP 命令

        注意：需要浏览器支持报告 API"""
        params = EnableReportingApiParams(enabled=enabled)
        return Command(method=NetworkMethod.ENABLE_REPORTING_API, params=params)

    @staticmethod
    def search_in_response_body(
        request_id: str,
        query: str,
        case_sensitive: bool = False,
        is_regex: bool = False,
    ) -> SearchInResponseBodyCommand:
        """搜索响应正文中的内容。

        功能强大，适用于：
        - 内容验证
        - 安全扫描
        - 数据提取
        - 响应验证

        参数：
            request_id：目标响应标识符
            查询：搜索字符串或模式
            case_sensitive：区分大小写
            is_regex：使用正则表达式匹配

        返回：
            命令：返回匹配结果的CDP命令

        性能提示：
        - 使用特定查询来获得大量响应
        - 考虑正则表达式的复杂性"""
        params = SearchInResponseBodyParams(requestId=request_id, query=query)
        if case_sensitive is not None:
            params['caseSensitive'] = case_sensitive
        if is_regex is not None:
            params['isRegex'] = is_regex
        return Command(method=NetworkMethod.SEARCH_IN_RESPONSE_BODY, params=params)

    @staticmethod
    def set_blocked_urls(urls: list[str]) -> SetBlockedURLsCommand:
        """阻止加载指定的 URL。

        主要特点：
        - 基于模式的 URL 拦截
        - 资源类型过滤
        - 网络请求预防
        - 错误模拟

        参数：
            urls：要阻止的 URL 模式列表
                 支持通配符和模式匹配

        返回：
            命令：设置URL阻止规则的CDP命令

        常见应用：
        - 广告/跟踪器拦截模拟
        - 资源加载控制
        - 错误处理测试
        - 网络隔离测试"""
        params = SetBlockedURLsParams(urls=urls)
        return Command(method=NetworkMethod.SET_BLOCKED_URLS, params=params)

    @staticmethod
    def set_bypass_service_worker(
        bypass: bool,
    ) -> SetBypassServiceWorkerCommand:
        """控制 Service Worker 拦截网络请求。

        使用案例：
        - 测试直接网络行为
        - 绕过离线功能
        - 调试缓存问题
        - 性能比较

        参数：
            bypass：True 表示跳过 Service Worker，False 表示允许

        返回：
            命令：用于配置 Service Worker 行为的 CDP 命令

        影响：
        - 影响离线功能
        - 更改缓存行为
        - 修改推送通知"""
        params = SetBypassServiceWorkerParams(bypass=bypass)
        return Command(method=NetworkMethod.SET_BYPASS_SERVICE_WORKER, params=params)

    @staticmethod
    def get_certificate(origin: str) -> GetCertificateCommand:
        """检索域的 SSL/TLS 证书信息。

        提供：
        - 证书链详细信息
        - 验证状态
        - 到期信息
        - 发行人详细信息

        参数：
            origin：证书检查的目标域

        返回：
            命令：返回证书数据的 CDP 命令

        安全应用：
        - 证书验证
        - SSL/TLS 验证
        - 安全评估
        - 信任链验证"""
        params = GetCertificateParams(origin=origin)
        return Command(method=NetworkMethod.GET_CERTIFICATE, params=params)

    @staticmethod
    def get_response_body_for_interception(
        interception_id: str,
    ) -> GetResponseBodyForInterceptionCommand:
        """从拦截的请求中检索响应正文。

        必不可少：
        - 响应修改
        - 内容检查
        - 安全测试
        - API响应验证

        参数：
            Interception_id：拦截请求的标识符

        返回：
            Command：提供截获响应内容的CDP命令

        注意：
        - 必须在启用拦截的情况下使用
        - 支持流式响应
        - 处理各种内容类型"""
        params = GetResponseBodyForInterceptionParams(interceptionId=interception_id)
        return Command(method=NetworkMethod.GET_RESPONSE_BODY_FOR_INTERCEPTION, params=params)

    @staticmethod
    def set_accepted_encodings(
        encodings: list[ContentEncoding],
    ) -> SetAcceptedEncodingsCommand:
        """指定请求接受的内容编码。

        控制：
        - 压缩算法
        - 传输编码
        - 内容优化

        参数：
            编码：可接受的编码方法列表
                     （gzip、deflate、br 等）

        返回：
            命令：用于设置编码首选项的 CDP 命令

        性能影响：
        - 影响带宽使用
        - 影响响应时间
        - 更改服务器行为"""
        params = SetAcceptedEncodingsParams(encodings=encodings)
        return Command(method=NetworkMethod.SET_ACCEPTED_ENCODINGS, params=params)

    @staticmethod
    def set_attach_debug_stack(enabled: bool) -> SetAttachDebugStackCommand:
        """启用/禁用请求的调试堆栈附加。

        调试功能：
        - 堆栈跟踪收集
        - 请求原产地追踪
        - 初始化上下文
        - 呼叫站点识别

        参数：
            启用：True 附加调试信息，False 禁用

        返回：
            命令：用于配置调试堆栈附加的 CDP 命令

        性能说明：
        - 启用后可能会影响性能
        - 对于开发/调试有用
        - 考虑内存使用情况"""
        params = SetAttachDebugStackParams(enabled=enabled)
        return Command(method=NetworkMethod.SET_ATTACH_DEBUG_STACK, params=params)

    @staticmethod
    def set_cookie_controls(
        enable_third_party_cookie_restriction: bool,
        disable_third_party_cookie_metadata: Optional[bool] = None,
        disable_third_party_cookie_heuristics: Optional[bool] = None,
    ) -> SetCookieControlsCommand:
        """配置第三方 cookie 处理策略。

        隐私功能：
        - Cookie访问控制
        - 第三方限制
        - 防追踪
        - 隐私政策执行

        参数：
            enable_third_party_cookie_restriction：启用限制
            disable_third_party_cookie_metadata：跳过元数据检查
            disable_third_party_cookie_heuristics：禁用检测逻辑

        返回：
            命令：设置cookie控制策略的CDP命令

        安全影响：
        - 影响跨站点跟踪
        - 更改身份验证行为
        - 影响嵌入内容"""
        params = SetCookieControlsParams(
            enableThirdPartyCookieRestriction=enable_third_party_cookie_restriction
        )
        if disable_third_party_cookie_metadata is not None:
            params['disableThirdPartyCookieMetadata'] = disable_third_party_cookie_metadata
        if disable_third_party_cookie_heuristics is not None:
            params['disableThirdPartyCookieHeuristics'] = disable_third_party_cookie_heuristics
        return Command(method=NetworkMethod.SET_COOKIE_CONTROLS, params=params)

    @staticmethod
    def stream_resource_content(
        request_id: str,
    ) -> StreamResourceContentCommand:
        """启用响应内容流。

        适用于：
        - 大文件下载
        - 渐进式加载
        - 内存优化
        - 实时处理

        参数：
            request_id：目标请求标识符

        返回：
            命令：启动内容流的 CDP 命令

        最佳实践：
        - 监控内存使用情况
        - 有效处理流块
        - 考虑错误恢复"""
        params = StreamResourceContentParams(requestId=request_id)
        return Command(method=NetworkMethod.STREAM_RESOURCE_CONTENT, params=params)

    @staticmethod
    def take_response_body_for_interception_as_stream(
        interception_id: str,
    ) -> TakeResponseBodyForInterceptionAsStreamCommand:
        """为拦截的响应正文创建流。

        应用：
        - 大响应处理
        - 内容修改
        - 带宽优化
        - 渐进式处理

        参数：
            Interception_id：拦截的响应标识符

        返回：
            命令：返回流句柄的 CDP 命令

        流处理：
        - 支持分块传输
        - 有效管理内存
        - 启用实时处理"""
        params = TakeResponseBodyForInterceptionAsStreamParams(interceptionId=interception_id)
        return Command(
            method=NetworkMethod.TAKE_RESPONSE_BODY_FOR_INTERCEPTION_AS_STREAM,
            params=params,
        )

    @staticmethod
    def emulate_network_conditions(
        offline: bool,
        latency: float,
        download_throughput: float,
        upload_throughput: float,
        connection_type: Optional[ConnectionType] = None,
        packet_loss: Optional[float] = None,
        packet_queue_length: Optional[int] = None,
        packet_reordering: Optional[bool] = None,
    ) -> EmulateNetworkConditionsCommand:
        """模拟真实测试场景的自定义网络条件。

        模拟各种网络配置文件，包括：
        - 离线模式
        - 高延迟连接
        - 带宽限制
        - 不可靠的网络特性

        参数：
            离线：模拟完全断网
            延迟：最小延迟（以毫秒为单位）（往返时间）
            download_throughput：最大下载速度（字节/秒，-1 禁用）
            upload_throughput：最大上传速度（字节/秒，-1表示禁用）
            connection_type：网络连接类型（蜂窝、wifi 等）
            packet_loss：模拟丢包百分比（0-100）
            packet_queue_length：网络缓冲区大小模拟
            packet_reordering：启用数据包顺序随机化

        典型用例：
        - 测试渐进加载状态
        - 验证离线优先功能
        - 受限网络下的性能优化

        返回：
            命令：激活网络仿真的 CDP 命令"""
        params = EmulateNetworkConditionsParams(
            offline=offline,
            latency=latency,
            downloadThroughput=download_throughput,
            uploadThroughput=upload_throughput,
        )
        if connection_type is not None:
            params['connectionType'] = connection_type
        if packet_loss is not None:
            params['packetLoss'] = packet_loss
        if packet_queue_length is not None:
            params['packetQueueLength'] = packet_queue_length
        if packet_reordering is not None:
            params['packetReordering'] = packet_reordering
        return Command(method=NetworkMethod.EMULATE_NETWORK_CONDITIONS, params=params)

    @staticmethod
    def get_security_isolation_status(
        frame_id: Optional[str] = None,
    ) -> GetSecurityIsolationStatusCommand:
        """检索安全隔离信息。

        提供：
        - CORS状态
        - 跨域隔离
        - 安全上下文
        - 框架隔离

        参数：
            frame_id：要检查的可选帧

        返回：
            命令：返回隔离状态的 CDP 命令

        安全方面：
        - 跨域策略
        - iframe 安全
        - 场地隔离
        - 内容保护"""
        params = GetSecurityIsolationStatusParams()
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=NetworkMethod.GET_SECURITY_ISOLATION_STATUS, params=params)

    @staticmethod
    def load_network_resource(
        url: str,
        options: LoadNetworkResourceOptions,
        frame_id: Optional[str] = None,
    ) -> LoadNetworkResourceCommand:
        """使用特定选项加载网络资源。

        特点：
        - 自定义请求配置
        - 资源加载控制
        - 特定于框架的加载
        - 错误处理

        参数：
            url：要加载的资源URL
            选项：加载配置
            frame_id：目标帧上下文

        返回：
            命令：CDP命令加载资源

        使用注意事项：
        - 尊重 CORS 政策
        - 处理身份验证
        - 管理重定向
        - 支持流媒体"""
        params = LoadNetworkResourceParams(url=url, options=options)
        if frame_id is not None:
            params['frameId'] = frame_id
        return Command(method=NetworkMethod.LOAD_NETWORK_RESOURCE, params=params)

    @staticmethod
    def replay_xhr(
        request_id: str,
    ) -> ReplayXHRCommand:
        """重放 XHR 请求。

        应用：
        - 请求调试
        - 反应测试
        - 竞赛条件分析
        - API验证

        参数：
            request_id: XHR 请求重放

        返回：
            命令：重放 XHR 的 CDP 命令

        注意：
        - 保留原始标题
        - 保留请求正文
        - 更新时间戳
        - 创建新的请求 ID"""
        params = ReplayXHRParams(requestId=request_id)
        return Command(method=NetworkMethod.REPLAY_XHR, params=params)
