from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional

from ljp_page._modules.pydoll.protocol.base import Command
from ljp_page._modules.pydoll.protocol.page.methods import (
    AddCompilationCacheParams,
    AddScriptToEvaluateOnNewDocumentParams,
    CaptureScreenshotParams,
    CaptureSnapshotParams,
    CreateIsolatedWorldParams,
    EnableParams,
    GenerateTestReportParams,
    GetAdScriptAncestryIdsParams,
    GetAppIdParams,
    GetAppManifestParams,
    GetOriginTrialsParams,
    GetPermissionsPolicyStateParams,
    GetResourceContentParams,
    HandleJavaScriptDialogParams,
    NavigateParams,
    NavigateToHistoryEntryParams,
    PageMethod,
    PrintToPDFParams,
    ProduceCompilationCacheParams,
    ReloadParams,
    RemoveScriptToEvaluateOnNewDocumentParams,
    ScreencastFrameAckParams,
    SearchInResourceParams,
    SetAdBlockingEnabledParams,
    SetBypassCSPParams,
    SetDocumentContentParams,
    SetFontFamiliesParams,
    SetFontSizesParams,
    SetInterceptFileChooserDialogParams,
    SetLifecycleEventsEnabledParams,
    SetPrerenderingAllowedParams,
    SetRPHRegistrationModeParams,
    SetSPCTransactionModeParams,
    SetWebLifecycleStateParams,
    StartScreencastParams,
)
from ljp_page._modules.pydoll.protocol.page.types import (
    CompilationCacheParams,
    FontFamilies,
    FontSizes,
    ScriptFontFamilies,
)

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.protocol.page.methods import (
        AddCompilationCacheCommand,
        AddScriptToEvaluateOnNewDocumentCommand,
        BringToFrontCommand,
        CaptureScreenshotCommand,
        CaptureSnapshotCommand,
        ClearCompilationCacheCommand,
        CloseCommand,
        CrashCommand,
        CreateIsolatedWorldCommand,
        DisableCommand,
        EnableCommand,
        GenerateTestReportCommand,
        GetAdScriptAncestryIdsCommand,
        GetAppIdCommand,
        GetAppManifestCommand,
        GetFrameTreeCommand,
        GetInstallabilityErrorsCommand,
        GetLayoutMetricsCommand,
        GetNavigationHistoryCommand,
        GetOriginTrialsCommand,
        GetPermissionsPolicyStateCommand,
        GetResourceContentCommand,
        GetResourceTreeCommand,
        HandleJavaScriptDialogCommand,
        NavigateCommand,
        NavigateToHistoryEntryCommand,
        PrintToPDFCommand,
        ProduceCompilationCacheCommand,
        ReloadCommand,
        RemoveScriptToEvaluateOnNewDocumentCommand,
        ResetNavigationHistoryCommand,
        ScreencastFrameAckCommand,
        SearchInResourceCommand,
        SetAdBlockingEnabledCommand,
        SetBypassCSPCommand,
        SetDocumentContentCommand,
        SetFontFamiliesCommand,
        SetFontSizesCommand,
        SetInterceptFileChooserDialogCommand,
        SetLifecycleEventsEnabledCommand,
        SetPrerenderingAllowedCommand,
        SetRPHRegistrationModeCommand,
        SetSPCTransactionModeCommand,
        SetWebLifecycleStateCommand,
        StartScreencastCommand,
        StopLoadingCommand,
        StopScreencastCommand,
        WaitForDebuggerCommand,
    )
    from ljp_page._modules.pydoll.protocol.page.types import (
        AutoResponseMode,
        ReferrerPolicy,
        ScreencastFormat,
        ScreenshotFormat,
        TransferMode,
        TransitionType,
        Viewport,
        WebLifecycleState,
    )


class PageCommands:
    """该类封装了 Chrome DevTools Protocol (CDP) 的页面命令。

    CDP 的页面域允许与浏览器页面交互，包括导航、
    内容操作和页面状态监控。这些命令提供了强大的
    Web 自动化、测试和调试功能。

    此类中定义的命令提供以下功能：
    - 导航到 URL 并管理页面历史记录
    - 捕获屏幕截图并生成 PDF
    - 处理 JavaScript 对话框
    - 启用和控制页面事件
    - 管理下载行为
    - 操作页面内容和状态"""

    @staticmethod
    def add_script_to_evaluate_on_new_document(
        source: str,
        world_name: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        run_immediately: Optional[bool] = None,
    ) -> AddScriptToEvaluateOnNewDocumentCommand:
        """创建一个命令来添加将在创建新文档时评估的脚本。

        参数：
            source (str)：创建新文档时要评估的脚本源。
            world_name（可选[str]）：如果指定，则使用给定名称创建一个孤立的世界。
            include_command_line_api （可选[bool]）：是否包含命令行 API。
            run_immediately (可选[bool]): 是否立即运行脚本
                现有的背景。

        返回：
            AddScriptToEvaluateOnNewDocumentCommand：带有标识符的命令对象
                添加的脚本的。"""
        params = AddScriptToEvaluateOnNewDocumentParams(source=source)
        if world_name is not None:
            params['worldName'] = world_name
        if include_command_line_api is not None:
            params['includeCommandLineAPI'] = include_command_line_api
        if run_immediately is not None:
            params['runImmediately'] = run_immediately

        return Command(method=PageMethod.ADD_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT, params=params)

    @staticmethod
    def bring_to_front() -> BringToFrontCommand:
        """将页面置于前面。"""
        return Command(method=PageMethod.BRING_TO_FRONT)

    @staticmethod
    def capture_screenshot(
        format: Optional[ScreenshotFormat] = None,
        quality: Optional[int] = None,
        clip: Optional[Viewport] = None,
        from_surface: Optional[bool] = None,
        capture_beyond_viewport: Optional[bool] = None,
        optimize_for_speed: Optional[bool] = None,
    ) -> CaptureScreenshotCommand:
        """创建一个命令来捕获当前页面的屏幕截图。

        参数：
            format（可选[str]）：图像压缩格式（jpeg、png 或 webp）。
            质量（可选[int]）：压缩质量从0-100（仅限jpeg）。
            剪辑（可选[视口]）：要捕获的页面区域。
            from_surface（可选[bool]）：从表面而不是视图捕获。
            capture_beyond_viewport（可选[bool]）：捕获视口之外的内容。
            optimize_for_speed（可选[bool]）：优化速度，而不是大小。

        返回：
            CaptureScreenshotCommand：具有 Base64 编码图像数据的命令对象。"""
        params = CaptureScreenshotParams()
        if format is not None:
            params['format'] = format
        if quality is not None:
            params['quality'] = quality
        if clip is not None:
            params['clip'] = clip
        if from_surface is not None:
            params['fromSurface'] = from_surface
        if capture_beyond_viewport is not None:
            params['captureBeyondViewport'] = capture_beyond_viewport
        if optimize_for_speed is not None:
            params['optimizeForSpeed'] = optimize_for_speed

        return Command(method=PageMethod.CAPTURE_SCREENSHOT, params=params)

    @staticmethod
    def close() -> CloseCommand:
        """创建关闭当前页面的命令。

        返回：
            CloseCommand：关闭页面的命令对象。"""
        return Command(method=PageMethod.CLOSE)

    @staticmethod
    def create_isolated_world(
        frame_id: str,
        world_name: Optional[str] = None,
        grant_universal_access: Optional[bool] = None,
    ) -> CreateIsolatedWorldCommand:
        """创建一个命令来为给定的框架创建一个孤立的世界。

        参数：
            frame_id (str)：要在其中创建隔离世界的框架的 ID。
            world_name（可选[str]）：要在执行上下文中报告的名称。
            grant_universal_access （可选[bool]）：是否授予通用访问权限。

        返回：
            CreateIsolatedWorldCommand：具有执行上下文 ID 的命令对象。"""
        params = CreateIsolatedWorldParams(frameId=frame_id)
        if world_name is not None:
            params['worldName'] = world_name
        if grant_universal_access is not None:
            params['grantUniveralAccess'] = grant_universal_access

        return Command(method=PageMethod.CREATE_ISOLATED_WORLD, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """创建一个命令来禁用页面域通知。

        返回：
            DisableCommand：禁用Page域的命令对象。"""
        return Command(method=PageMethod.DISABLE)

    @staticmethod
    def enable(
        enable_file_chooser_opened_event: Optional[bool] = None,
    ) -> EnableCommand:
        """创建一个命令来启用页面域通知。

        参数：
            enable_file_chooser_opened_event (可选[bool]): 是否发出
                Page.fileChooserOpened 事件。

        返回：
            EnableCommand：启用Page域的命令对象。"""
        params = EnableParams()
        if enable_file_chooser_opened_event is not None:
            params['enableFileChooserOpenedEvent'] = enable_file_chooser_opened_event

        return Command(method=PageMethod.ENABLE, params=params)

    @staticmethod
    def get_app_manifest(
        manifest_id: Optional[str] = None,
    ) -> GetAppManifestCommand:
        """创建一个命令来获取当前文档的清单。

        返回：
            GetAppManifestCommand：带有清单信息的命令对象。"""
        params = GetAppManifestParams()
        if manifest_id is not None:
            params['manifestId'] = manifest_id
        return Command(method=PageMethod.GET_APP_MANIFEST, params=params)

    @staticmethod
    def get_frame_tree() -> GetFrameTreeCommand:
        """创建一个命令来获取当前页面的框架树。

        返回：
            GetFrameTreeCommand：具有帧树信息的命令对象。"""
        return Command(method=PageMethod.GET_FRAME_TREE)

    @staticmethod
    def get_layout_metrics() -> GetLayoutMetricsCommand:
        """创建一个命令来获取页面的布局指标。

        返回：
            GetLayoutMetricsCommand：具有布局指标的命令对象。"""
        return Command(method=PageMethod.GET_LAYOUT_METRICS)

    @staticmethod
    def get_navigation_history() -> GetNavigationHistoryCommand:
        """创建一个命令来获取当前页面的导航历史记录。

        返回：
            GetNavigationHistoryCommand：具有导航历史记录的命令对象。"""
        return Command(method=PageMethod.GET_NAVIGATION_HISTORY)

    @staticmethod
    def handle_javascript_dialog(
        accept: bool, prompt_text: Optional[str] = None
    ) -> HandleJavaScriptDialogCommand:
        """创建一个命令来处理 JavaScript 对话框。

        参数：
            Accept (bool): 是否接受或关闭对话框。
            Prompt_text（可选[str]）：在提示对话框中输入的文本。

        返回：
            HandleJavaScriptDialogCommand：处理 JavaScript 对话框的命令对象。"""
        params = HandleJavaScriptDialogParams(accept=accept)
        if prompt_text is not None:
            params['promptText'] = prompt_text

        return Command(method=PageMethod.HANDLE_JAVASCRIPT_DIALOG, params=params)

    @staticmethod
    def navigate(
        url: str,
        referrer: Optional[str] = None,
        transition_type: Optional[TransitionType] = None,
        frame_id: Optional[str] = None,
        referrer_policy: Optional[ReferrerPolicy] = None,
    ) -> NavigateCommand:
        """创建导航到特定 URL 的命令。

        参数：
            url (str)：要导航到的 URL。
            引荐来源网址（可选[str]）：引荐来源网址。
            transition_type（可选[str]）：预期的过渡类型。
            frame_id（可选[str]）：要导航的帧 ID。
            referrer_policy（可选[str]）：推荐人策略。

        返回：
            NavigateCommand：导航到 URL 的命令对象。"""
        params = NavigateParams(url=url)
        if referrer is not None:
            params['referrer'] = referrer
        if transition_type is not None:
            params['transitionType'] = transition_type
        if frame_id is not None:
            params['frameId'] = frame_id
        if referrer_policy is not None:
            params['referrerPolicy'] = referrer_policy

        return Command(method=PageMethod.NAVIGATE, params=params)

    @staticmethod
    def navigate_to_history_entry(entry_id: int) -> NavigateToHistoryEntryCommand:
        """创建一个命令来导航到特定的历史记录条目。

        参数：
            Entry_id (int)：要导航到的历史条目的 ID。

        返回：
            NavigateToHistoryEntryCommand：导航到历史记录条目的命令对象。"""
        params = NavigateToHistoryEntryParams(entryId=entry_id)
        return Command(method=PageMethod.NAVIGATE_TO_HISTORY_ENTRY, params=params)

    @staticmethod
    def print_to_pdf(  #编号：PLR0912
        landscape: Optional[bool] = None,
        display_header_footer: Optional[bool] = None,
        print_background: Optional[bool] = None,
        scale: Optional[float] = None,
        paper_width: Optional[float] = None,
        paper_height: Optional[float] = None,
        margin_top: Optional[float] = None,
        margin_bottom: Optional[float] = None,
        margin_left: Optional[float] = None,
        margin_right: Optional[float] = None,
        page_ranges: Optional[str] = None,
        header_template: Optional[str] = None,
        footer_template: Optional[str] = None,
        prefer_css_page_size: Optional[bool] = None,
        transfer_mode: Optional[TransferMode] = None,
        generate_tagged_pdf: Optional[bool] = None,
        generate_document_outline: Optional[bool] = None,
    ) -> PrintToPDFCommand:
        """创建将当前页面打印为 PDF 的命令。

        参数：
            横向（可选[布尔]）：纸张方向。
            display_header_footer （可选[bool]）：显示页眉和页脚。
            print_background （可选[bool]）：打印背景图形。
            比例（可选[float]）：网页渲染的比例。
            paper_width（可选[float]）：纸张宽度（以英寸为单位）。
            paper_height（可选[float]）：纸张高度（以英寸为单位）。
            margin_top （可选[float]）：上边距（以英寸为单位）。
            margin_bottom（可选[float]）：下边距（以英寸为单位）。
            margin_left（可选[float]）：左边距（以英寸为单位）。
            margin_right（可选[float]）：右边距（以英寸为单位）。
            page_ranges（可选[str]）：要打印的纸张范围，例如“1-5、8、11-13”。
            header_template（可选[str]）：打印标题的 HTML 模板。
            footer_template（可选[str]）：打印页脚的 HTML 模板。
            Preferred_css_page_size （可选[bool]）：是否首选 CSS 定义的页面大小。
            Transfer_mode（可选[str]）：传输模式。

        返回：
            PrintToPDFCommand：将页面打印为 PDF 的命令对象。"""
        params = PrintToPDFParams()
        if landscape is not None:
            params['landscape'] = landscape
        if display_header_footer is not None:
            params['displayHeaderFooter'] = display_header_footer
        if print_background is not None:
            params['printBackground'] = print_background
        if scale is not None:
            params['scale'] = scale
        if paper_width is not None:
            params['paperWidth'] = paper_width
        if paper_height is not None:
            params['paperHeight'] = paper_height
        if margin_top is not None:
            params['marginTop'] = margin_top
        if margin_bottom is not None:
            params['marginBottom'] = margin_bottom
        if margin_left is not None:
            params['marginLeft'] = margin_left
        if margin_right is not None:
            params['marginRight'] = margin_right
        if page_ranges is not None:
            params['pageRanges'] = page_ranges
        if header_template is not None:
            params['headerTemplate'] = header_template
        if footer_template is not None:
            params['footerTemplate'] = footer_template
        if prefer_css_page_size is not None:
            params['preferCSSPageSize'] = prefer_css_page_size
        if transfer_mode is not None:
            params['transferMode'] = transfer_mode
        if generate_tagged_pdf is not None:
            params['generateTaggedPDF'] = generate_tagged_pdf
        if generate_document_outline is not None:
            params['generateDocumentOutline'] = generate_document_outline

        return Command(method=PageMethod.PRINT_TO_PDF, params=params)

    @staticmethod
    def reload(
        ignore_cache: Optional[bool] = None,
        script_to_evaluate_on_load: Optional[str] = None,
        loader_id: Optional[str] = None,
    ) -> ReloadCommand:
        """创建一个命令来重新加载当前页面。

        参数：
            ignore_cache（可选[bool]）：如果为 true，则忽略浏览器缓存。
            script_to_evaluate_on_load（可选[str]）：加载时注入页面的脚本。

        返回：
            ReloadCommand：重新加载页面的命令对象。"""
        params = ReloadParams()
        if ignore_cache is not None:
            params['ignoreCache'] = ignore_cache
        if script_to_evaluate_on_load is not None:
            params['scriptToEvaluateOnLoad'] = script_to_evaluate_on_load
        if loader_id is not None:
            params['loaderId'] = loader_id

        return Command(method=PageMethod.RELOAD, params=params)

    @staticmethod
    def reset_navigation_history() -> ResetNavigationHistoryCommand:
        """创建一个命令来重置导航历史记录。"""
        return Command(method=PageMethod.RESET_NAVIGATION_HISTORY)

    @staticmethod
    def remove_script_to_evaluate_on_new_document(
        identifier: str,
    ) -> RemoveScriptToEvaluateOnNewDocumentCommand:
        """创建一个命令来删除添加的脚本以在新文档上进行评估。

        参数：
            标识符 (str)：要删除的脚本的标识符。

        返回：
            RemoveScriptToEvaluateOnNewDocumentCommand：用于删除脚本的命令对象。"""
        params = RemoveScriptToEvaluateOnNewDocumentParams(identifier=identifier)
        return Command(method=PageMethod.REMOVE_SCRIPT_TO_EVALUATE_ON_NEW_DOCUMENT, params=params)

    @staticmethod
    def set_bypass_csp(enabled: bool) -> SetBypassCSPCommand:
        """创建一个命令来切换绕过页面 CSP。

        参数：
            enabled (bool): 是否绕过页面CSP。

        返回：
            SetBypassCSPCommand：用于切换绕过页面 CSP 的命令对象。"""
        params = SetBypassCSPParams(enabled=enabled)
        return Command(method=PageMethod.SET_BYPASS_CSP, params=params)

    @staticmethod
    def set_document_content(frame_id: str, html: str) -> SetDocumentContentCommand:
        """创建一个命令来设置框架的文档内容。

        参数：
            frame_id (str)：要为其设置文档内容的框架 ID。
            html (str)：要设置的 HTML 内容。

        返回：
            SetDocumentContentCommand：设置文档内容的命令对象。"""
        params = SetDocumentContentParams(frameId=frame_id, html=html)
        return Command(method=PageMethod.SET_DOCUMENT_CONTENT, params=params)

    @staticmethod
    def set_intercept_file_chooser_dialog(enabled: bool) -> SetInterceptFileChooserDialogCommand:
        """创建一个命令来设置是否拦截文件选择器对话框。

        参数：
            enabled (bool): 是否拦截文件选择器对话框。

        返回：
            SetInterceptFileChooserDialogCommand：设置文件选择器对话框的命令对象
                拦截。"""
        params = SetInterceptFileChooserDialogParams(enabled=enabled)
        return Command(method=PageMethod.SET_INTERCEPT_FILE_CHOOSER_DIALOG, params=params)

    @staticmethod
    def set_lifecycle_events_enabled(enabled: bool) -> SetLifecycleEventsEnabledCommand:
        """创建一个命令来启用/禁用生命周期事件。

        参数：
            enabled (bool): 是否启用生命周期事件。

        返回：
            SetLifecycleEventsEnabledCommand：用于启用/禁用生命周期事件的命令对象。"""
        params = SetLifecycleEventsEnabledParams(enabled=enabled)
        return Command(method=PageMethod.SET_LIFECYCLE_EVENTS_ENABLED, params=params)

    @staticmethod
    def stop_loading() -> StopLoadingCommand:
        """创建一个命令来停止加载页面。

        返回：
            StopLoadingCommand：停止加载页面的命令对象。"""
        return Command(method=PageMethod.STOP_LOADING)

    @staticmethod
    def add_compilation_cache(url: str, data: str) -> AddCompilationCacheCommand:
        """创建一个命令来添加编译缓存条目。

        实验性：此方法是实验性的，可能会发生变化。

        参数：
            url (str)：要为其添加编译缓存条目的 URL。
            data (str)：Base64 编码的数据。

        返回：
            AddCompilationCacheCommand：添加编译缓存条目的命令对象。"""
        params = AddCompilationCacheParams(url=url, data=data)
        return Command(method=PageMethod.ADD_COMPILATION_CACHE, params=params)

    @staticmethod
    def capture_snapshot(
        format: Literal['mhtml'] = 'mhtml',
    ) -> CaptureSnapshotCommand:
        """创建一个命令来捕获页面快照。

        实验性：此方法是实验性的，可能会发生变化。

        参数：
            format (Literal['mhtml'])：快照的格式（仅支持 'mhtml'）。

        返回：
            CaptureSnapshotCommand：捕获快照的命令对象。"""
        params = CaptureSnapshotParams(format=format)
        return Command(method=PageMethod.CAPTURE_SNAPSHOT, params=params)

    @staticmethod
    def clear_compilation_cache() -> ClearCompilationCacheCommand:
        """创建一个命令来清除编译缓存。"""
        return Command(method=PageMethod.CLEAR_COMPILATION_CACHE)

    @staticmethod
    def crash() -> CrashCommand:
        """创建一个命令来崩溃页面。"""
        return Command(method=PageMethod.CRASH)

    @staticmethod
    def generate_test_report(
        message: str, group: Optional[str] = None
    ) -> GenerateTestReportCommand:
        """创建一个命令来生成测试报告。

        实验性：此方法是实验性的，可能会发生变化。

        参数：
            message (str)：要在报告中显示的消息。
            group （可选[str]）：报告的组标签。

        返回：
            GenerateTestReportCommand：生成测试报告的命令对象。"""
        params = GenerateTestReportParams(message=message)
        if group is not None:
            params['group'] = group
        return Command(method=PageMethod.GENERATE_TEST_REPORT, params=params)

    @staticmethod
    def get_ad_script_ancestry_ids(
        frame_id: str,
    ) -> GetAdScriptAncestryIdsCommand:
        """创建一个命令来获取给定帧的广告脚本祖先 ID。

        实验性：此方法是实验性的，可能会发生变化。

        参数：
            frame_id (str)：要获取其广告脚本祖先 ID 的框架的 ID。

        返回：
            GetAdScriptAncestryIdsCommand：用于获取广告脚本祖先 ID 的命令对象。"""
        params = GetAdScriptAncestryIdsParams(frameId=frame_id)
        return Command(method=PageMethod.GET_AD_SCRIPT_ANCESTRY_IDS, params=params)

    @staticmethod
    def get_app_id(
        app_id: Optional[str] = None, recommended_id: Optional[str] = None
    ) -> GetAppIdCommand:
        """创建一个命令来获取应用程序 ID。

        实验性：此方法是实验性的，可能会发生变化。

        参数：
            app_id（可选[str]）：用于验证的应用程序ID。
            推荐的_id（可选[str]）：推荐的应用程序ID。

        返回：
            GetAppIdCommand：获取应用程序 ID 的命令对象。"""
        params = GetAppIdParams()
        if app_id is not None:
            params['appId'] = app_id
        if recommended_id is not None:
            params['recommendedId'] = recommended_id
        return Command(method=PageMethod.GET_APP_ID, params=params)

    @staticmethod
    def get_installability_errors() -> GetInstallabilityErrorsCommand:
        """创建一个命令来获取可安装性错误。"""
        return Command(method=PageMethod.GET_INSTALLABILITY_ERRORS)

    @staticmethod
    def get_origin_trials(frame_id: str) -> GetOriginTrialsCommand:
        """创建一个命令来获取给定源的源试验。

        实验性：此方法是实验性的，可能会发生变化。

        参数：
            frame_id（可选[str]）：要获取试验的帧ID。

        返回：
            GetOriginTrialsCommand：获取原始试验的命令对象。"""
        params = GetOriginTrialsParams(frameId=frame_id)
        return Command(method=PageMethod.GET_ORIGIN_TRIALS, params=params)

    @staticmethod
    def get_permissions_policy_state(
        frame_id: str,
    ) -> GetPermissionsPolicyStateCommand:
        """创建一个命令来获取权限策略状态。"""
        params = GetPermissionsPolicyStateParams(frameId=frame_id)
        return Command(method=PageMethod.GET_PERMISSIONS_POLICY_STATE, params=params)

    @staticmethod
    def get_resource_content(
        frame_id: str,
        url: str,
    ) -> GetResourceContentCommand:
        """创建一个命令来获取资源内容。"""
        params = GetResourceContentParams(frameId=frame_id, url=url)
        return Command(method=PageMethod.GET_RESOURCE_CONTENT, params=params)

    @staticmethod
    def get_resource_tree() -> GetResourceTreeCommand:
        """创建一个命令来获取资源树。"""
        return Command(method=PageMethod.GET_RESOURCE_TREE)

    @staticmethod
    def produce_compilation_cache(
        scripts: list[CompilationCacheParams],
    ) -> ProduceCompilationCacheCommand:
        """创建一个命令来生成编译缓存条目。"""
        params = ProduceCompilationCacheParams(scripts=scripts)
        return Command(method=PageMethod.PRODUCE_COMPILATION_CACHE, params=params)

    @staticmethod
    def screencast_frame_ack(
        session_id: int,
    ) -> ScreencastFrameAckCommand:
        """创建一个命令来确认截屏帧。"""
        params = ScreencastFrameAckParams(sessionId=session_id)
        return Command(method=PageMethod.SCREENCAST_FRAME_ACK, params=params)

    @staticmethod
    def search_in_resource(
        frame_id: str,
        url: str,
        query: str,
        case_sensitive: Optional[bool] = None,
        is_regex: Optional[bool] = None,
    ) -> SearchInResourceCommand:
        """创建一个命令来搜索资源中的字符串。"""
        params = SearchInResourceParams(frameId=frame_id, url=url, query=query)
        if case_sensitive is not None:
            params['caseSensitive'] = case_sensitive
        if is_regex is not None:
            params['isRegex'] = is_regex
        return Command(method=PageMethod.SEARCH_IN_RESOURCE, params=params)

    @staticmethod
    def set_ad_blocking_enabled(
        enabled: bool,
    ) -> SetAdBlockingEnabledCommand:
        """创建一个命令来设置广告拦截启用。"""
        params = SetAdBlockingEnabledParams(enabled=enabled)
        return Command(method=PageMethod.SET_AD_BLOCKING_ENABLED, params=params)

    @staticmethod
    def set_font_families(
        font_families: FontFamilies,
        for_scripts: list[ScriptFontFamilies],
    ) -> SetFontFamiliesCommand:
        """创建一个命令来设置字体系列。"""
        params = SetFontFamiliesParams(fontFamilies=font_families, forScripts=for_scripts)
        return Command(method=PageMethod.SET_FONT_FAMILIES, params=params)

    @staticmethod
    def set_font_sizes(
        font_sizes: FontSizes,
    ) -> SetFontSizesCommand:
        """创建一个命令来设置字体大小。"""
        params = SetFontSizesParams(fontSizes=font_sizes)
        return Command(method=PageMethod.SET_FONT_SIZES, params=params)

    @staticmethod
    def set_prerendering_allowed(
        is_allowed: bool,
    ) -> SetPrerenderingAllowedCommand:
        """创建一个命令来设置允许的预渲染。"""
        params = SetPrerenderingAllowedParams(isAllowed=is_allowed)
        return Command(method=PageMethod.SET_PRERENDERING_ALLOWED, params=params)

    @staticmethod
    def set_rph_registration_mode(
        mode: AutoResponseMode,
    ) -> SetRPHRegistrationModeCommand:
        """创建设置 RPH 注册模式的命令。"""
        params = SetRPHRegistrationModeParams(mode=mode)
        return Command(method=PageMethod.SET_RPH_REGISTRATION_MODE, params=params)

    @staticmethod
    def set_spc_transaction_mode(
        mode: AutoResponseMode,
    ) -> SetSPCTransactionModeCommand:
        """创建设置 SPC 事务模式的命令。"""
        params = SetSPCTransactionModeParams(mode=mode)
        return Command(method=PageMethod.SET_SPC_TRANSACTION_MODE, params=params)

    @staticmethod
    def set_web_lifecycle_state(
        state: WebLifecycleState,
    ) -> SetWebLifecycleStateCommand:
        """创建一个命令来设置 Web 生命周期状态。"""
        params = SetWebLifecycleStateParams(state=state)
        return Command(method=PageMethod.SET_WEB_LIFECYCLE_STATE, params=params)

    @staticmethod
    def start_screencast(
        format: ScreencastFormat,
        quality: Optional[int] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        every_nth_frame: Optional[int] = None,
    ) -> StartScreencastCommand:
        """创建启动截屏视频的命令。"""
        params = StartScreencastParams(format=format)
        if quality is not None:
            params['quality'] = quality
        if max_width is not None:
            params['maxWidth'] = max_width
        if max_height is not None:
            params['maxHeight'] = max_height
        if every_nth_frame is not None:
            params['everyNthFrame'] = every_nth_frame
        return Command(method=PageMethod.START_SCREENCAST, params=params)

    @staticmethod
    def stop_screencast() -> StopScreencastCommand:
        """创建一个命令来停止截屏视频。"""
        return Command(method=PageMethod.STOP_SCREENCAST)

    @staticmethod
    def wait_for_debugger() -> WaitForDebuggerCommand:
        """创建一个命令来等待调试器。"""
        return Command(method=PageMethod.WAIT_FOR_DEBUGGER)
