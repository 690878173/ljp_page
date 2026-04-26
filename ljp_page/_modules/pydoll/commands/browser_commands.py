from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ljp_page._modules.pydoll.protocol.base import Command
from ljp_page._modules.pydoll.protocol.browser.methods import (
    AddPrivacySandboxCoordinatorKeyConfigParams,
    AddPrivacySandboxEnrollmentOverrideParams,
    BrowserMethod,
    CancelDownloadParams,
    ExecuteBrowserCommandParams,
    GetHistogramParams,
    GetHistogramsParams,
    GetWindowBoundsParams,
    GetWindowForTargetParams,
    GrantPermissionsParams,
    ResetPermissionsParams,
    SetContentsSizeParams,
    SetDockTileParams,
    SetDownloadBehaviorParams,
    SetPermissionParams,
    SetWindowBoundsParams,
)
from ljp_page._modules.pydoll.protocol.browser.types import (
    Bounds,
    WindowState,
)

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.protocol.browser.methods import (
        AddPrivacySandboxCoordinatorKeyConfigCommand,
        AddPrivacySandboxEnrollmentOverrideCommand,
        CancelDownloadCommand,
        CloseCommand,
        CrashCommand,
        CrashGpuProcessCommand,
        DownloadBehavior,
        ExecuteBrowserCommandCommand,
        GetBrowserCommandLineCommand,
        GetHistogramCommand,
        GetHistogramsCommand,
        GetVersionCommand,
        GetWindowBoundsCommand,
        GetWindowForTargetCommand,
        GrantPermissionsCommand,
        ResetPermissionsCommand,
        SetContentsSizeCommand,
        SetDockTileCommand,
        SetDownloadBehaviorCommand,
        SetPermissionCommand,
        SetWindowBoundsCommand,
    )
    from ljp_page._modules.pydoll.protocol.browser.types import (
        BrowserCommandId,
        BrowserContextID,
        PermissionDescriptor,
        PermissionSetting,
        PermissionType,
        PrivacySandboxAPI,
        WindowID,
    )


class BrowserCommands:
    """BrowserCommands 类提供了一组与浏览器交互的命令
    浏览器的主要功能基于CDP。这些命令允许
    管理浏览器窗口，例如关闭窗口、检索窗口 ID、
    并调整窗口边界（大小和状态）。

    此类中定义的命令提供以下功能：
    - 管理浏览器窗口和目标。
    - 设置权限和下载行为。
    - 控制浏览器窗口（大小、状态）。
    - 检索浏览器信息和版本控制。"""

    @staticmethod
    def get_version() -> GetVersionCommand:
        """生成获取浏览器版本信息的命令。

        返回：
            GetVersionCommand：返回浏览器版本详细信息的 CDP 命令
                包括协议版本、产品名称、修订版本和用户代理。"""
        return Command(method=BrowserMethod.GET_VERSION)

    @staticmethod
    def get_browser_command_line() -> GetBrowserCommandLineCommand:
        """返回浏览器进程的命令行开关。

        返回：
            GetBrowserCommandLineCommand：返回命令行参数的 CDP 命令。

        注意：仅当 --enable-automation 在命令行上时才有效。"""
        return Command(method=BrowserMethod.GET_BROWSER_COMMAND_LINE)

    @staticmethod
    def get_histograms(
        query: Optional[str] = None,
        delta: bool = False,
    ) -> GetHistogramsCommand:
        """获取 Chrome 直方图。

        参数：
            查询：名称中请求的子字符串。仅将查询作为直方图
                   提取其名称中的子字符串。返回空或不存在的查询
                   所有直方图。
            delta：如果为 true，则检索自上次 delta 调用以来的 delta。

        返回：
            GetHistogramsCommand：返回直方图数据的 CDP 命令。"""
        params = GetHistogramsParams()
        if query is not None:
            params['query'] = query
        if delta:
            params['delta'] = delta
        return Command(method=BrowserMethod.GET_HISTOGRAMS, params=params)

    @staticmethod
    def get_histogram(
        name: str,
        delta: bool = False,
    ) -> GetHistogramCommand:
        """按名称获取 Chrome 直方图。

        参数：
            name：请求的直方图名称。
            delta：如果为 true，则检索自上次 delta 调用以来的 delta。

        返回：
            GetHistogramCommand：返回直方图数据的 CDP 命令。"""
        params = GetHistogramParams(name=name)
        if delta:
            params['delta'] = delta
        return Command(method=BrowserMethod.GET_HISTOGRAM, params=params)

    @staticmethod
    def get_window_bounds(window_id: WindowID) -> GetWindowBoundsCommand:
        """获取浏览器窗口的位置和大小。

        参数：
            window_id：浏览器窗口 ID。

        返回：
            GetWindowBoundsCommand：返回窗口边界信息的 CDP 命令。"""
        params = GetWindowBoundsParams(windowId=window_id)
        return Command(method=BrowserMethod.GET_WINDOW_BOUNDS, params=params)

    @staticmethod
    def get_window_for_target(
        target_id: Optional[str] = None,
    ) -> GetWindowForTargetCommand:
        """获取包含 devtools 目标的浏览器窗口。

        参数：
            target_id：Devtools 代理主机 ID。如果作为会话的一部分调用，
                      使用关联的 targetId。

        返回：
            GetWindowForTargetCommand：返回窗口信息的CDP命令
                包括windowId和bounds。"""
        params = GetWindowForTargetParams()
        if target_id is not None:
            params['targetId'] = target_id
        return Command(method=BrowserMethod.GET_WINDOW_FOR_TARGET, params=params)

    @staticmethod
    def set_window_bounds(window_id: WindowID, bounds: Bounds) -> SetWindowBoundsCommand:
        """设置浏览器窗口的位置和/或大小。

        参数：
            window_id：浏览器窗口 ID。
            边界：新窗口边界。 “最小化”、“最大化”和“全屏”状态
                   不能与“左”、“上”、“宽度”或“高度”组合。叶子
                   未指定的字段不变。

        返回：
            SetWindowBoundsCommand：设置窗口边界的 CDP 命令。"""
        params = SetWindowBoundsParams(windowId=window_id, bounds=bounds)
        return Command(method=BrowserMethod.SET_WINDOW_BOUNDS, params=params)

    @staticmethod
    def set_contents_size(
        window_id: WindowID,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> SetContentsSizeCommand:
        """设置浏览器内容的大小，根据需要调整浏览器窗口的大小。

        参数：
            window_id：浏览器窗口 ID。
            width：窗口内容宽度（DIP）。如果省略，则假定当前宽度。
                  如果省略“高度”，则必须指定。
            height：窗口内容的高度（DIP）。如果省略，则假定当前高度。
                   如果省略“宽度”，则必须指定。

        返回：
            SetContentsSizeCommand：设置窗口内容大小的 CDP 命令。"""
        params = SetContentsSizeParams(windowId=window_id)
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        return Command(method=BrowserMethod.SET_CONTENTS_SIZE, params=params)

    @staticmethod
    def set_dock_tile(
        badge_label: Optional[str] = None,
        image: Optional[str] = None,
    ) -> SetDockTileCommand:
        """设置特定于平台的停靠图块详细信息。

        参数：
            Badge_label：可选的徽章标签。
            image：Png 编码图像（通过 JSON 传递时的 Base64 字符串）。

        返回：
            SetDockTileCommand：设置停靠图块详细信息的 CDP 命令。"""
        params = SetDockTileParams()
        if badge_label is not None:
            params['badgeLabel'] = badge_label
        if image is not None:
            params['image'] = image
        return Command(method=BrowserMethod.SET_DOCK_TILE, params=params)

    @staticmethod
    def execute_browser_command(command_id: BrowserCommandId) -> ExecuteBrowserCommandCommand:
        """调用遥测使用的自定义浏览器命令。

        参数：
            command_id：浏览器命令标识符。

        返回：
            ExecuteBrowserCommandCommand：执行浏览器命令的CDP命令。"""
        params = ExecuteBrowserCommandParams(commandId=command_id)
        return Command(method=BrowserMethod.EXECUTE_BROWSER_COMMAND, params=params)

    @staticmethod
    def add_privacy_sandbox_enrollment_override(
        url: str,
    ) -> AddPrivacySandboxEnrollmentOverrideCommand:
        """允许网站使用需要注册的隐私沙箱功能
        该网站并未实际注册。仅在页面目标上受支持。

        参数：
            url：站点 URL。

        返回：
            AddPrivacySandboxEnrollmentOverrideCommand：添加注册的 CDP 命令
            覆盖。"""
        params = AddPrivacySandboxEnrollmentOverrideParams(url=url)
        return Command(method=BrowserMethod.ADD_PRIVACY_SANDBOX_ENROLLMENT_OVERRIDE, params=params)

    @staticmethod
    def add_privacy_sandbox_coordinator_key_config(
        api: PrivacySandboxAPI,
        coordinator_origin: str,
        key_config: str,
        browser_context_id: Optional[BrowserContextID] = None,
    ) -> AddPrivacySandboxCoordinatorKeyConfigCommand:
        """配置与给定隐私沙箱 API 一起使用的加密密钥以进行通信
        交给值得信赖的协调员。由于这仅用于测试自动化，
        coordinatorOrigin 必须是 .test 域。没有现有的协调员
        源配置可能存在。

        参数：
            api：Privacy Sandbox API 类型。
            coordinator_origin：协调器来源（必须是 .test 域）。
            key_config：密钥配置字符串。
            browser_context_id：执行操作的BrowserContext。省略时，
                               使用默认浏览器上下文。

        返回：
            AddPrivacySandboxCoordinatorKeyConfigCommand：添加密钥配置的 CDP 命令。"""
        params = AddPrivacySandboxCoordinatorKeyConfigParams(
            api=api,
            coordinatorOrigin=coordinator_origin,
            keyConfig=key_config,
        )
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(
            method=BrowserMethod.ADD_PRIVACY_SANDBOX_COORDINATOR_KEY_CONFIG, params=params
        )

    @staticmethod
    def set_permission(
        permission: PermissionDescriptor,
        setting: PermissionSetting,
        origin: Optional[str] = None,
        browser_context_id: Optional[BrowserContextID] = None,
    ) -> SetPermissionCommand:
        """设置给定来源的权限设置。

        参数：
            权限：覆盖权限的描述符。
            设置：权限的设置。
            origin：权限适用的来源，如果未指定则为所有来源。
            browser_context_id：要覆盖的上下文。省略时，将使用默认浏览器上下文。

        返回：
            SetPermissionCommand：设置权限的CDP命令。"""
        params = SetPermissionParams(permission=permission, setting=setting)
        if origin is not None:
            params['origin'] = origin
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.SET_PERMISSION, params=params)

    @staticmethod
    def grant_permissions(
        permissions: list['PermissionType'],
        origin: Optional[str] = None,
        browser_context_id: Optional['BrowserContextID'] = None,
    ) -> GrantPermissionsCommand:
        """向给定源授予特定权限并拒绝所有其他权限。

        参数：
            权限：要授予的权限列表。
            origin：权限适用的来源，如果未指定则为所有来源。
            browser_context_id：要覆盖权限的BrowserContext。当省略时，
                               使用默认浏览器上下文。

        返回：
            GrantPermissionsCommand：授予权限的CDP命令。"""
        params = GrantPermissionsParams(permissions=permissions)
        if origin is not None:
            params['origin'] = origin
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.GRANT_PERMISSIONS, params=params)

    @staticmethod
    def reset_permissions(
        browser_context_id: Optional['BrowserContextID'] = None,
    ) -> ResetPermissionsCommand:
        """重置所有来源的所有权限管理。

        参数：
            browser_context_id：重置权限的BrowserContext。当省略时，
                               使用默认浏览器上下文。

        返回：
            ResetPermissionsCommand：重置权限的 CDP 命令。"""
        params = ResetPermissionsParams()
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.RESET_PERMISSIONS, params=params)

    @staticmethod
    def set_download_behavior(
        behavior: DownloadBehavior,
        browser_context_id: Optional['BrowserContextID'] = None,
        download_path: Optional[str] = None,
        events_enabled: bool = False,
    ) -> SetDownloadBehaviorCommand:
        """设置下载文件时的行为。

        参数：
            行为：是否允许所有或拒绝所有下载请求，或使用默认值
                     Chrome 行为（如果可用）（否则拒绝）。 allowedAndName 允许
                     根据下载指南下载并命名文件。
            browser_context_id：用于设置下载行为的BrowserContext。当省略时，
                               使用默认浏览器上下文。
            download_path：保存下载文件的默认路径。这是必需的
                          如果行为设置为“allow”或“allowAndName”。
            events_enabled：是否发出下载事件（默认为 false）。

        返回：
            SetDownloadBehaviorCommand：设置下载行为的 CDP 命令。"""
        params = SetDownloadBehaviorParams(behavior=behavior)
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        if download_path is not None:
            params['downloadPath'] = download_path
        if events_enabled is not None:
            params['eventsEnabled'] = events_enabled
        return Command(method=BrowserMethod.SET_DOWNLOAD_BEHAVIOR, params=params)

    @staticmethod
    def cancel_download(
        guid: str,
        browser_context_id: Optional['BrowserContextID'] = None,
    ) -> CancelDownloadCommand:
        """如果正在下载，请取消下载。

        参数：
            guid：下载的全局唯一标识符。
            browser_context_id：执行操作的BrowserContext。省略时，
                               使用默认浏览器上下文。

        返回：
            CancelDownloadCommand：取消下载的 CDP 命令。"""
        params = CancelDownloadParams(guid=guid)
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        return Command(method=BrowserMethod.CANCEL_DOWNLOAD, params=params)

    @staticmethod
    def close() -> CloseCommand:
        """优雅地关闭浏览器。

        返回：
            CloseCommand：关闭浏览器的 CDP 命令。"""
        return Command(method=BrowserMethod.CLOSE)

    @staticmethod
    def crash() -> CrashCommand:
        """导致主线程上的浏览器崩溃。

        返回：
            CrashCommand：导致浏览器崩溃的 CDP 命令。"""
        return Command(method=BrowserMethod.CRASH)

    @staticmethod
    def crash_gpu_process() -> CrashGpuProcessCommand:
        """GPU 进程崩溃。

        返回：
            CrashGpuProcessCommand：导致 GPU 进程崩溃的 CDP 命令。"""
        return Command(method=BrowserMethod.CRASH_GPU_PROCESS)

    #常见窗口操作的辅助方法
    @staticmethod
    def set_window_maximized(window_id: WindowID) -> SetWindowBoundsCommand:
        """最大化浏览器窗口。

        参数：
            window_id：浏览器窗口 ID。

        返回：
            SetWindowBoundsCommand：最大化窗口的CDP命令。"""
        bounds = Bounds(windowState=WindowState.MAXIMIZED)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_minimized(window_id: WindowID) -> SetWindowBoundsCommand:
        """最小化浏览器窗口。

        参数：
            window_id：浏览器窗口 ID。

        返回：
            SetWindowBoundsCommand：最小化窗口的CDP命令。"""
        bounds = Bounds(windowState=WindowState.MINIMIZED)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_fullscreen(window_id: WindowID) -> SetWindowBoundsCommand:
        """将浏览器窗口设置为全屏。

        参数：
            window_id：浏览器窗口 ID。

        返回：
            SetWindowBoundsCommand：将窗口设置为全屏的 CDP 命令。"""
        bounds = Bounds(windowState=WindowState.FULLSCREEN)
        return BrowserCommands.set_window_bounds(window_id, bounds)

    @staticmethod
    def set_window_normal(window_id: WindowID) -> SetWindowBoundsCommand:
        """将浏览器窗口设置为正常状态。

        参数：
            window_id：浏览器窗口 ID。

        返回：
            SetWindowBoundsCommand：将窗口设置为正常状态的 CDP 命令。"""
        bounds = Bounds(windowState=WindowState.NORMAL)
        return BrowserCommands.set_window_bounds(window_id, bounds)
