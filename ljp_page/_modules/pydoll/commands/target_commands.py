from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ljp_page._modules.pydoll.protocol.base import Command
from ljp_page._modules.pydoll.protocol.target.methods import (
    ActivateTargetParams,
    AttachToBrowserTargetParams,
    AttachToTargetParams,
    CloseTargetParams,
    CreateBrowserContextParams,
    CreateTargetParams,
    DetachFromTargetParams,
    DisposeBrowserContextParams,
    GetTargetInfoParams,
    GetTargetsParams,
    SetAutoAttachParams,
    SetDiscoverTargetsParams,
    SetRemoteLocationsParams,
    TargetMethod,
)

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.protocol.browser.types import WindowState
    from ljp_page._modules.pydoll.protocol.target.methods import (
        ActivateTargetCommand,
        AttachToBrowserTargetCommand,
        AttachToTargetCommand,
        CloseTargetCommand,
        CreateBrowserContextCommand,
        CreateTargetCommand,
        DetachFromTargetCommand,
        DisposeBrowserContextCommand,
        GetBrowserContextsCommand,
        GetTargetInfoCommand,
        GetTargetsCommand,
        SetAutoAttachCommand,
        SetDiscoverTargetsCommand,
        SetRemoteLocationsCommand,
    )
    from ljp_page._modules.pydoll.protocol.target.types import RemoteLocation


class TargetCommands:
    """使用 Chrome DevTools 协议管理浏览器目标的类。

    CDP 的目标域支持其他目标发现并允许附加到它们。
    目标可以代表浏览器选项卡、窗口、框架、Web Worker、Service Worker 等。
    该域提供了创建、发现和控制这些目标的方法。

    此类提供了创建与浏览器目标交互的命令的方法，
    包括通过 CDP 命令创建、激活、附加和关闭目标。"""

    @staticmethod
    def activate_target(target_id: str) -> ActivateTargetCommand:
        """生成激活（聚焦）目标的命令。

        参数：
            target_id：要激活的目标的 ID。

        返回：
            命令：激活目标的 CDP 命令。"""
        params = ActivateTargetParams(targetId=target_id)
        return Command(method=TargetMethod.ACTIVATE_TARGET, params=params)

    @staticmethod
    def attach_to_target(target_id: str, flatten: Optional[bool] = None) -> AttachToTargetCommand:
        """生成附加到具有给定 ID 的目标的命令。

        连接到目标后，您可以向其发送命令并从其接收事件。
        这对于控制和自动化浏览器选项卡等目标至关重要。

        参数：
            target_id：要附加到的目标的 ID。
            flatten：如果为 true，则通过指定 sessionId 启用对会话的“平面”访问
                    命令中的属性。建议将其作为非扁平化
                    模式已被弃用。请参阅 https://crbug.com/991325

        返回：
            Command：附加到目标的 CDP 命令，该命令将返回 sessionId。"""
        params = AttachToTargetParams(targetId=target_id)
        if flatten is not None:
            params['flatten'] = flatten
        return Command(method=TargetMethod.ATTACH_TO_TARGET, params=params)

    @staticmethod
    def close_target(target_id: str) -> CloseTargetCommand:
        """生成关闭目标的命令。

        如果目标是页面或选项卡，它将被关闭。这相当于
        单击浏览器选项卡上的关闭按钮。

        参数：
            target_id：要关闭的目标的 ID。

        返回：
            命令：关闭目标的 CDP 命令，该命令将返回成功标志。"""
        params = CloseTargetParams(targetId=target_id)
        return Command(method=TargetMethod.CLOSE_TARGET, params=params)

    @staticmethod
    def create_browser_context(
        dispose_on_detach: Optional[bool] = None,
        proxy_server: Optional[str] = None,
        proxy_bypass_list: Optional[str] = None,
        origins_with_universal_network_access: Optional[list[str]] = None,
    ) -> CreateBrowserContextCommand:
        """生成命令来创建新的空浏览器上下文。

        浏览器上下文类似于隐身配置文件，但您可以拥有多个。
        每个上下文都有自己的一组 cookie、本地存储和其他浏览器数据。
        这对于测试多个用户或隔离会话非常有用。

        参数：
            dispose_on_detach：如果指定，上下文将在
                              调试会话断开连接。
            proxy_server：代理服务器字符串，类似于传递给 --proxy-server 的字符串
                         命令行参数（例如“socks5://192.168.1.100:1080”）。
            proxy_bypass_list：代理绕过列表，与传递给的列表类似
                               --proxy-bypass-list 命令行参数
                               （例如，“*.example.com,localhost”）。
            origins_with_universal_network_access：要授予的可选来源列表
                                                  无限制的跨域访问。
                                                  除这些之外的 URL 部分
                                                  构成原点的被忽略。

        返回：
            命令：创建浏览器上下文的CDP命令，该命令将返回
                    创建的上下文的ID。"""
        params = CreateBrowserContextParams()
        if dispose_on_detach is not None:
            params['disposeOnDetach'] = dispose_on_detach
        if proxy_server is not None:
            params['proxyServer'] = proxy_server
        if proxy_bypass_list is not None:
            params['proxyBypassList'] = proxy_bypass_list
        if origins_with_universal_network_access is not None:
            params['originsWithUniversalNetworkAccess'] = origins_with_universal_network_access
        return Command(method=TargetMethod.CREATE_BROWSER_CONTEXT, params=params)

    @staticmethod
    def create_target(
        url: str = 'about:blank',
        left: Optional[int] = None,
        top: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        window_state: Optional[WindowState] = None,
        browser_context_id: Optional[str] = None,
        enable_begin_frame_control: Optional[bool] = None,
        new_window: Optional[bool] = None,
        background: Optional[bool] = None,
        for_tab: Optional[bool] = None,
        hidden: Optional[bool] = None,
    ) -> CreateTargetCommand:
        """生成创建新页面（目标）的命令。

        这是打开具有特定内容的新选项卡或窗口的主要方法之一
        属性，例如位置、大小和浏览器上下文。

        参数：
            url：页面将导航到的初始 URL。空字符串表示 about:blank。
            left：框架左侧位置，以设备无关像素 (DIP) 为单位。
                 要求 newWindow 为 true 或处于无头模式。
            top：DIP 中框架顶部位置。要求 newWindow 为 true 或处于无头模式。
            width：DIP 中的帧宽度。
            height：DIP 中的框架高度。
            window_state：框架窗口状态：正常、最小化、最大化或全屏。
                         默认是正常的。
            browser_context_id：创建页面的浏览器上下文。
                               如果未指定，则使用默认浏览器上下文。
            enable_begin_frame_control：是否控制该目标的BeginFrames
                                       通过 DevTools（仅限无头 shell，不支持
                                       MacOS 尚未，默认为 false）。
            new_window：是否创建新窗口或选项卡（默认为 false，
                       无头 shell 不支持）。
            背景：是否在后台或前台创建目标
                       （默认为 false，headless shell 不支持）。
            for_tab：是否创建“tab”类型的目标。
            hidden：是否创建隐藏目标。隐藏目标可通过以下方式观察
                   协议，但不存在于选项卡 UI 条中。无法创建
                   forTab：true，newWindow：true 或background：false。的寿命
                   选项卡仅限于会话的生命周期。

        返回：
            命令：创建目标的 CDP 命令，该命令将返回 ID
                所创建的目标。"""
        params = CreateTargetParams(url=url)
        if left is not None:
            params['left'] = left
        if top is not None:
            params['top'] = top
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        if window_state is not None:
            params['windowState'] = window_state
        if browser_context_id is not None:
            params['browserContextId'] = browser_context_id
        if enable_begin_frame_control is not None:
            params['enableBeginFrameControl'] = enable_begin_frame_control
        if new_window is not None:
            params['newWindow'] = new_window
        if background is not None:
            params['background'] = background
        if for_tab is not None:
            params['forTab'] = for_tab
        if hidden is not None:
            params['hidden'] = hidden
        return Command(method=TargetMethod.CREATE_TARGET, params=params)

    @staticmethod
    def detach_from_target(session_id: Optional[str] = None) -> DetachFromTargetCommand:
        """生成将会话与其目标分离的命令。

        分离后，您将不再接收来自目标的事件，并且
        无法向其发送命令。

        参数：
            session_id：要分离的会话 ID。如果未指定，则分离所有会话。

        返回：
            命令：与目标分离的 CDP 命令。"""
        params = DetachFromTargetParams()
        if session_id is not None:
            params['sessionId'] = session_id
        return Command(method=TargetMethod.DETACH_FROM_TARGET, params=params)

    @staticmethod
    def dispose_browser_context(browser_context_id: str) -> DisposeBrowserContextCommand:
        """生成删除浏览器上下文的命令。

        属于浏览器上下文的所有页面将在不调用的情况下关闭
        他们的 beforeunload 钩子。这类似于关闭隐身个人资料。

        参数：
            browser_context_id：要处理的浏览器上下文的 ID。

        返回：
            命令：用于处理浏览器上下文的 CDP 命令。"""
        params = DisposeBrowserContextParams(browserContextId=browser_context_id)
        return Command(method=TargetMethod.DISPOSE_BROWSER_CONTEXT, params=params)

    @staticmethod
    def get_browser_contexts() -> GetBrowserContextsCommand:
        """生成一个命令来获取使用 createBrowserContext 创建的所有浏览器上下文。

        这对于获取用于管理的所有可用上下文的列表非常有用
        多个独立的浏览器会话。

        返回：
            Command：获取所有浏览器上下文的CDP命令，会返回
                    浏览器上下文 ID 的数组。"""
        return Command(method=TargetMethod.GET_BROWSER_CONTEXTS, params={})

    @staticmethod
    def get_targets(filter: Optional[list] = None) -> GetTargetsCommand:
        """生成一个命令来检索可用目标的列表。

        目标包括选项卡、扩展、Web Worker 和其他可附加实体
        在浏览器中。这对于发现之前存在的目标很有用
        依附于他们。

        参数：
            过滤器：仅报告与过滤器匹配的目标。如果没有过滤器
                   指定且目标发现当前已启用，过滤器用于
                   目标发现用于一致性。

        返回：
            命令：用于获取目标的 CDP 命令，该命令将返回一个列表
                    TargetInfo 对象，其中包含有关每个目标的详细信息。"""
        params = GetTargetsParams()
        if filter is not None:
            params['filter'] = filter
        return Command(method=TargetMethod.GET_TARGETS, params=params)

    @staticmethod
    def set_auto_attach(
        auto_attach: bool,
        wait_for_debugger_on_start: bool = False,
        flatten: Optional[bool] = None,
        filter: Optional[list] = None,
    ) -> SetAutoAttachCommand:
        """生成一个命令来控制是否自动附加到新目标。

        该方法控制是否自动附加到新目标
        被认为与当前框架直接相关（例如，iframe 或工人）。
        打开后，它还会附加到所有现有的相关目标。当关闭时，
        它会自动与所有当前连接的目标分离。

        参数：
            auto_attach：是否自动附加到相关目标。
            wait_for_debugger_on_start：附加到新目标时是否暂停它们。
                                       使用 Runtime.runIfWaitingForDebugger 运行暂停的目标。
            flatten：通过指定 sessionId 属性启用对会话的“平面”访问
                    在命令中。该模式是首选，非扁平化模式
                    已被弃用（请参阅 crbug.com/991325）。
            过滤器：仅附加匹配过滤器的目标。

        返回：
            命令：用于设置自动附加行为的 CDP 命令。"""
        params = SetAutoAttachParams(
            autoAttach=auto_attach, waitForDebuggerOnStart=wait_for_debugger_on_start
        )
        if flatten is not None:
            params['flatten'] = flatten
        if filter is not None:
            params['filter'] = filter
        return Command(method=TargetMethod.SET_AUTO_ATTACH, params=params)

    @staticmethod
    def set_discover_targets(
        discover: bool, filter: Optional[list] = None
    ) -> SetDiscoverTargetsCommand:
        """生成控制目标发现的命令。

        该方法控制是否发现可用目标并通过以下方式通知
        targetCreated/targetInfoChanged/targetDestroyed 事件。目标发现很有用
        用于监视新选项卡、工作人员或其他目标何时创建或销毁。

        参数：
            discovery：是否发现可用目标。
            过滤器：只有匹配过滤器的目标才会被发现。如果发现是假的，
                   过滤器必须省略或为空。

        返回：
            命令：用于设置目标发现的 CDP 命令。"""
        params = SetDiscoverTargetsParams(discover=discover)
        if filter is not None:
            params['filter'] = filter
        return Command(method=TargetMethod.SET_DISCOVER_TARGETS, params=params)

    @staticmethod
    def attach_to_browser_target(session_id: str) -> AttachToBrowserTargetCommand:
        """生成附加到浏览器目标的命令。

        这是附加到浏览器目标的实验方法，
        仅使用平面 sessionId 模式。浏览器目标是一个特殊的目标
        代表浏览器本身而不是页面或其他内容。

        参数：
            session_id：附加到浏览器目标的会话 ID。

        返回：
            命令：附加到浏览器目标的 CDP 命令，
                    这将返回一个新的会话 ID。"""
        params = AttachToBrowserTargetParams(sessionId=session_id)
        return Command(method=TargetMethod.ATTACH_TO_BROWSER_TARGET, params=params)

    @staticmethod
    def get_target_info(target_id: str) -> GetTargetInfoCommand:
        """生成命令以获取有关特定目标的信息。

        该实验方法返回有关目标的详细信息，
        例如其类型、URL、标题和其他属性。

        参数：
            target_id：要获取信息的目标的 ID。

        返回：
            Command：获取目标信息的CDP命令，会返回
                    包含目标详细信息的 TargetInfo 对象。"""
        params = GetTargetInfoParams(targetId=target_id)
        return Command(method=TargetMethod.GET_TARGET_INFO, params=params)

    @staticmethod
    def set_remote_locations(locations: list[RemoteLocation]) -> SetRemoteLocationsCommand:
        """生成命令以启用指定远程位置的目标发现。

        该实验方法可以在以下情况下实现远程位置的目标发现：
        setDiscoverTargets 已设置为 true。这对于发现目标很有用
        在远程设备或不同的浏览器实例中。

        参数：
            位置：远程位置列表，每个位置包含一个主机和端口。

        返回：
            命令：用于设置目标发现的远程位置的 CDP 命令。"""
        params = SetRemoteLocationsParams(locations=locations)
        return Command(method=TargetMethod.SET_REMOTE_LOCATIONS, params=params)
