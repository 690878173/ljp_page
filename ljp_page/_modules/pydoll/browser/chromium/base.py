from __future__ import annotations

import asyncio
import json
from ljp_page.logger import logger
import os
import shutil
import warnings
from abc import ABC, abstractmethod
from contextlib import suppress
from functools import partial
from random import randint
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, overload
from urllib.parse import urlsplit, urlunsplit

from ljp_page._modules.pydoll.browser.managers import (
    BrowserProcessManager,
    ProxyManager,
    TempDirectoryManager,
)
from ljp_page._modules.pydoll.browser.tab import Tab
from ljp_page._modules.pydoll.commands import (
    BrowserCommands,
    EmulationCommands,
    FetchCommands,
    PageCommands,
    RuntimeCommands,
    StorageCommands,
    TargetCommands,
)
from ljp_page._modules.pydoll.connection import ConnectionHandler
from ljp_page._modules.pydoll.exceptions import (
    BrowserNotRunning,
    FailedToStartBrowser,
    InvalidConnectionPort,
    InvalidWebSocketAddress,
    MissingTargetOrWebSocket,
    NoValidTabFound,
)
from ljp_page._modules.pydoll.protocol.browser.types import DownloadBehavior
from ljp_page._modules.pydoll.protocol.fetch.events import FetchEvent
from ljp_page._modules.pydoll.protocol.fetch.types import AuthChallengeResponseType
from ljp_page._modules.pydoll.utils.user_agent_parser import UserAgentParser

if TYPE_CHECKING:
    from tempfile import TemporaryDirectory

    from ljp_page._modules.pydoll.browser.interfaces import BrowserOptionsManager
    from ljp_page._modules.pydoll.protocol.base import Command, Response, T_CommandParams, T_CommandResponse
    from ljp_page._modules.pydoll.protocol.browser.methods import (
        GetVersionResponse,
        GetVersionResult,
        GetWindowForTargetResponse,
    )
    from ljp_page._modules.pydoll.protocol.browser.types import Bounds, PermissionType
    from ljp_page._modules.pydoll.protocol.fetch.events import RequestPausedEvent
    from ljp_page._modules.pydoll.protocol.fetch.types import HeaderEntry
    from ljp_page._modules.pydoll.protocol.network.types import (
        Cookie,
        CookieParam,
        ErrorReason,
        RequestMethod,
        ResourceType,
    )
    from ljp_page._modules.pydoll.protocol.storage.methods import GetCookiesResponse
    from ljp_page._modules.pydoll.protocol.target.methods import (
        CreateBrowserContextResponse,
        CreateTargetResponse,
        GetBrowserContextsResponse,
        GetTargetsResponse,
    )
    from ljp_page._modules.pydoll.protocol.target.types import TargetInfo



class Browser(ABC):  #编号：PLR0904
    """使用 Chrome DevTools 协议的浏览器自动化的抽象基类。

    提供全面的浏览器控制，包括生命周期管理、
    上下文处理、网络拦截、cookie 管理和 CDP 命令。"""

    def __init__(
        self,
        options_manager: BrowserOptionsManager,
        connection_port: Optional[int] = None,
    ):
        """使用配置初始化浏览器实例。

        参数：
            options_manager：管理浏览器选项初始化和默认值。
                必须实现initialize_options()和add_default_arguments()。
            连接端口：CDP WebSocket 端口。如果无，则随机端口 (9223-9322)。

        注意：
            调用 start() 来实际启动浏览器。"""
        self._validate_connection_port(connection_port)
        self.options = options_manager.initialize_options()
        self._proxy_manager = ProxyManager(self.options)
        self._connection_port = connection_port if connection_port else randint(9223, 9322)
        self._browser_process_manager = BrowserProcessManager()
        self._temp_directory_manager = TempDirectoryManager()
        self._ws_address: Optional[str] = None
        self._connection_handler = ConnectionHandler(self._connection_port)
        self._backup_preferences_dir = ''
        self._tabs_opened: dict[str, Tab] = {}
        self._context_proxy_auth: dict[str, tuple[str, str]] = {}
        logger.debug(
            f'Browser initialized: port={self._connection_port}, '
            f'headless={getattr(self.options, "headless", None)}'
        )

    async def __aenter__(self) -> 'Browser':
        """异步上下文管理器条目。"""
        logger.debug('Entering browser async context')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出并进行清理。"""
        logger.debug(f'Exiting browser async context: exc_type={exc_type}')
        if self._backup_preferences_dir:
            logger.debug(f'Restoring backup preferences directory: {self._backup_preferences_dir}')
            user_data_dir = self._get_user_data_dir()
            shutil.copy2(
                self._backup_preferences_dir,
                os.path.join(user_data_dir, 'Default', 'Preferences'),
            )
        if await self._is_browser_running(timeout=2):
            await self.stop()

        await self._connection_handler.close()

    async def connect(self, ws_address: str) -> Tab:
        """使用 WebSocket 地址连接到浏览器。当我们设置
        连接处理程序将使用 _ws_address 属性
        该地址而不是从连接端口解析它。

        参数：
            ws_address：浏览器的WebSocket地址。

        返回：
            打开的选项卡列表中的第一个选项卡。

        注意：
            仅当您想连接到浏览器时才应该使用此方法
            已经在运行了。"""
        logger.info(f'Connecting to browser via WebSocket: {ws_address}')
        await self._setup_ws_address(ws_address)
        tabs = await self.get_opened_tabs()
        logger.info(f'Connected. Tabs available: {len(tabs)}')
        return tabs[0]

    async def start(self) -> Tab:
        """启动浏览器进程并建立 CDP 连接。

        返回：
            用于交互的初始选项卡。

        加薪：
            FailedToStartBrowser：如果浏览器无法启动或连接。"""


        binary_location = self.options.binary_location or self._get_default_binary_location()
        logger.debug('Resolved binary location: %s', binary_location)

        self._setup_user_dir()
        logger.debug('User data directory configured')
        proxy_config = self._proxy_manager.get_proxy_credentials()

        logger.info(f'Starting browser process on port {self._connection_port}')
        self._browser_process_manager.start_browser_process(
            binary_location, self._connection_port, self.options.arguments
        )
        await self._verify_browser_running()
        logger.info('Browser process started and responsive')
        await self._configure_proxy(proxy_config[0], proxy_config[1])

        valid_tab_id = await self._get_valid_tab_id(await self.get_targets())
        tab = Tab(self, target_id=valid_tab_id, connection_port=self._connection_port)
        self._tabs_opened[valid_tab_id] = tab
        await self._apply_user_agent_override(tab)
        logger.info(f'Initial tab attached: {valid_tab_id}')
        return tab

    async def stop(self):
        """停止浏览器进程并清理资源。

        发送 Browser.close 命令，终止进程，删除临时目录，
        并关闭 WebSocket 连接。

        加薪：
            BrowserNotRunning：如果浏览器当前未运行。"""
        if not await self._is_browser_running():
            logger.error('Stop called but browser is not running')
            raise BrowserNotRunning()

        logger.info('Stopping browser process')
        await self._execute_command(BrowserCommands.close())
        self._browser_process_manager.stop_process()
        await self._connection_handler.close()
        await asyncio.sleep(0.5 if os.name == 'nt' else 0.1)
        self._temp_directory_manager.cleanup()
        logger.info('Browser process stopped and resources cleaned up')

    async def close(self):
        """关闭WebSocket连接并释放资源。"""
        logger.info('Closing browser WebSocket connection')
        await self._connection_handler.close()

    async def create_browser_context(
        self, proxy_server: Optional[str] = None, proxy_bypass_list: Optional[str] = None
    ) -> str:
        """创建隔离的浏览器上下文（例如隐身）。

        浏览器上下文提供隔离存储并且不共享会话数据。
        多个上下文可以同时存在。

        参数：
            proxy_server：仅适用于此上下文的可选代理（scheme://host:port）。
            proxy_bypass_list：绕过代理的逗号分隔主机。

        返回：
            与其他方法一起使用的浏览器上下文 ID。"""
        #如果 proxy_server 包含凭据，则删除它们并存储每个上下文的身份验证
        sanitized_proxy = proxy_server
        extracted_auth: Optional[tuple[str, str]] = None
        if proxy_server:
            sanitized_proxy, extracted_auth = self._sanitize_proxy_and_extract_auth(proxy_server)
            logger.debug(
                f'Creating browser context with proxy: {sanitized_proxy}'
                f'(credentials provided={bool(extracted_auth)})'
            )

        response: CreateBrowserContextResponse = await self._execute_command(
            TargetCommands.create_browser_context(
                proxy_server=sanitized_proxy,
                proxy_bypass_list=proxy_bypass_list,
            )
        )
        context_id = response['result']['browserContextId']
        if extracted_auth:
            self._context_proxy_auth[context_id] = extracted_auth
        logger.info(f'Created browser context: {context_id}')
        return context_id

    async def delete_browser_context(self, browser_context_id: str):
        """删除浏览器上下文和所有关联的选项卡/资源。

        删除所有存储（cookie、localStorage 等）并关闭所有选项卡。
        默认浏览器上下文无法删除。

        注意：
            立即关闭所有关联的选项卡。"""
        logger.info(f'Deleting browser context: {browser_context_id}')
        return await self._execute_command(
            TargetCommands.dispose_browser_context(browser_context_id)
        )

    async def get_browser_contexts(self) -> list[str]:
        """获取所有浏览器上下文 ID，包括默认上下文。"""
        response: GetBrowserContextsResponse = await self._execute_command(
            TargetCommands.get_browser_contexts()
        )
        logger.debug(f'Fetched {len(response["result"]["browserContextIds"])} browser contexts')
        return response['result']['browserContextIds']

    async def new_tab(self, url: str = '', browser_context_id: Optional[str] = None) -> Tab:
        """创建新的页面交互选项卡。

        参数：
            url：初始 URL（about：如果为空则为空）。
            browser_context_id：要在其中创建选项卡的上下文（默认为“无”）。

        返回：
            用于页面导航和元素交互的选项卡实例。"""
        logger.info(f'Creating new tab (context={browser_context_id})')
        response: CreateTargetResponse = await self._execute_command(
            TargetCommands.create_target(
                browser_context_id=browser_context_id,
            )
        )
        target_id = response['result']['targetId']
        tab = Tab(self, **self._get_tab_kwargs(target_id, browser_context_id))
        self._tabs_opened[target_id] = tab
        await self._apply_user_agent_override(tab)
        await self._setup_context_proxy_auth_for_tab(tab, browser_context_id)
        if url:
            await tab.go_to(url)
        logger.info(f'New tab created: {target_id}')
        return tab

    async def get_targets(self) -> list[TargetInfo]:
        """获取浏览器中的所有活动目标/页面。

        目标包括页面、服务工作人员、共享工作人员和浏览器进程。
        对于调试和管理多个选项卡很有用。

        返回：
            TargetInfo 对象的列表。"""
        response: GetTargetsResponse = await self._execute_command(TargetCommands.get_targets())
        logger.debug(f'Fetched {len(response["result"]["targetInfos"])} targets')
        return response['result']['targetInfos']

    async def get_opened_tabs(self) -> list[Tab]:
        """获取所有打开的非扩展且类型为“页面”的选项卡。
        已打开的选项卡将按原样返回。如果打开新目标，
        将创建一个新的选项卡实例。

        返回：
            Tab 实例的列表。最后一个选项卡是最新的选项卡。"""
        targets = await self.get_targets()
        valid_tab_targets = [
            target
            for target in targets
            if target['type'] == 'page' and 'extension' not in target['url']
        ]
        all_target_ids = [target['targetId'] for target in valid_tab_targets]
        existing_target_ids = list(self._tabs_opened.keys())
        remaining_target_ids = [
            target_id for target_id in all_target_ids if target_id not in existing_target_ids
        ]
        existing_tabs = [self._tabs_opened[target_id] for target_id in existing_target_ids]
        new_tabs = []
        for target_id in reversed(remaining_target_ids):
            tab = Tab(self, **self._get_tab_kwargs(target_id))
            await self._apply_user_agent_override(tab)
            new_tabs.append(tab)
        self._tabs_opened.update(dict(zip(remaining_target_ids, new_tabs)))
        logger.debug(
            f'Opened tabs resolved: existing={len(existing_tabs)}, new={len(new_tabs)}',
        )
        return existing_tabs + new_tabs

    async def get_tab_by_target(self, target: TargetInfo) -> Tab:
        tab = Tab(self, **self._get_tab_kwargs(target['targetId']))
        await self._apply_user_agent_override(tab)
        return tab

    async def set_download_path(self, path: str, browser_context_id: Optional[str] = None):
        """设置下载目录路径（set_download_behavior 的便捷方法）。"""
        logger.info(f'Setting download path: {path} (context={browser_context_id})')
        return await self._execute_command(
            BrowserCommands.set_download_behavior(
                behavior=DownloadBehavior.ALLOW,
                download_path=path,
                browser_context_id=browser_context_id,
            )
        )

    async def set_download_behavior(
        self,
        behavior: DownloadBehavior,
        download_path: Optional[str] = None,
        browser_context_id: Optional[str] = None,
        events_enabled: bool = False,
    ):
        """配置下载处理。

        参数：
            行为：允许（保存到路径）、拒绝（取消）或默认。
            download_path：如果行为允许，则需要。
            browser_context_id：要应用的上下文（默认为“无”）。
            events_enabled：生成下载事件以进行进度跟踪。"""
        logger.info(
            f'Setting download behavior: behavior={behavior},'
            f'path={download_path}, context={browser_context_id},'
            f'events={events_enabled}'
        )
        return await self._execute_command(
            BrowserCommands.set_download_behavior(
                behavior=behavior,
                download_path=download_path,
                browser_context_id=browser_context_id,
                events_enabled=events_enabled,
            )
        )

    async def delete_all_cookies(self, browser_context_id: Optional[str] = None):
        """从浏览器或上下文中删除所有 cookie（会话、持久、第三方）。"""
        logger.info(f'Clearing all cookies (context={browser_context_id})')
        return await self._execute_command(StorageCommands.clear_cookies(browser_context_id))

    async def set_cookies(
        self, cookies: list[CookieParam], browser_context_id: Optional[str] = None
    ):
        """在浏览器或上下文中设置多个 cookie。"""
        logger.debug(f'Setting {len(cookies)} cookies (context={browser_context_id})')
        return await self._execute_command(StorageCommands.set_cookies(cookies, browser_context_id))

    async def get_cookies(self, browser_context_id: Optional[str] = None) -> list[Cookie]:
        """从浏览器或上下文获取所有 cookie。

        注意：
            此方法不适用于本机隐身模式（--incognito 标志）。
            对于隐身模式，请使用“tab.get_cookies()”代替。"""
        response: GetCookiesResponse = await self._execute_command(
            StorageCommands.get_cookies(browser_context_id)
        )
        logger.debug(
            f'Retrieved {len(response["result"]["cookies"])} cookies (context={browser_context_id})'
        )
        return response['result']['cookies']

    async def get_version(self) -> GetVersionResult:
        """获取浏览器版本和 CDP 协议信息。"""
        response: GetVersionResponse = await self._execute_command(BrowserCommands.get_version())
        logger.debug(f'Browser version: {response["result"]}')
        return response['result']

    async def get_window_id_for_target(self, target_id: str) -> int:
        """获取目标的窗口 ID（用于通过 CDP 进行窗口操作）。"""
        response: GetWindowForTargetResponse = await self._execute_command(
            BrowserCommands.get_window_for_target(target_id)
        )
        logger.debug(f'Window id for target {target_id}: {response["result"]["windowId"]}')
        return response['result']['windowId']

    async def get_window_id_for_tab(self, tab: Tab) -> int:
        """获取选项卡的窗口 ID（便捷方法）。"""
        target_id = tab._target_id or (tab._ws_address.split('/')[-1] if tab._ws_address else None)
        if not target_id:
            logger.error('Missing target id or ws address for tab when getting window id')
            raise MissingTargetOrWebSocket()
        return await self.get_window_id_for_target(target_id)

    async def get_window_id(self) -> int:
        """获取任何有效选项卡的窗口 ID。

        加薪：
            NoValidTabFound：如果找不到有效的附加选项卡。"""
        targets = await self.get_targets()
        valid_tab_id = await self._get_valid_tab_id(targets)
        return await self.get_window_id_for_target(valid_tab_id)

    async def set_window_maximized(self):
        """最大化浏览器窗口（影响窗口中的所有选项卡）。"""
        window_id = await self.get_window_id()
        logger.info(f'Maximizing window: id={window_id}')
        return await self._execute_command(BrowserCommands.set_window_maximized(window_id))

    async def set_window_minimized(self):
        """将浏览器窗口最小化到任务栏/停靠栏。"""
        window_id = await self.get_window_id()
        logger.info(f'Minimizing window: id={window_id}')
        return await self._execute_command(BrowserCommands.set_window_minimized(window_id))

    async def set_window_bounds(self, bounds: Bounds):
        """设置窗口位置和/或大小。

        参数：
            bounds：要修改的属性（左、上、宽度、高度、windowState）。
                仅更改指定的属性。"""
        window_id = await self.get_window_id()
        logger.info(f'Setting window bounds: id={window_id}, bounds={bounds}')
        return await self._execute_command(BrowserCommands.set_window_bounds(window_id, bounds))

    async def grant_permissions(
        self,
        permissions: list[PermissionType],
        origin: Optional[str] = None,
        browser_context_id: Optional[str] = None,
    ):
        """授予浏览器权限（地理位置、通知、相机等）。

        绕过自动化测试的正常权限提示。

        参数：
            权限：授予的权限。
            origin：要授予的源（如果没有，则为所有源）。
            browser_context_id：要应用的上下文（默认为“无”）。"""
        logger.info(
            f'Granting permissions: {permissions} (origin={origin}, context={browser_context_id})',
        )
        return await self._execute_command(
            BrowserCommands.grant_permissions(permissions, origin, browser_context_id)
        )

    async def reset_permissions(self, browser_context_id: Optional[str] = None):
        """将所有权限重置为默认值并恢复提示行为。"""
        logger.info(f'Resetting permissions (context={browser_context_id})')
        return await self._execute_command(BrowserCommands.reset_permissions(browser_context_id))

    @overload
    async def on(
        self, event_name: str, callback: Callable[[Any], Any], temporary: bool = False
    ) -> int: ...
    @overload
    async def on(
        self, event_name: str, callback: Callable[[Any], Awaitable[Any]], temporary: bool = False
    ) -> int: ...
    async def on(self, event_name, callback, temporary: bool = False) -> int:
        """在浏览器级别注册 CDP 事件侦听器。

        回调在后台任务中运行以防止阻塞。影响所有页面/目标。

        参数：
            event_name：CDP 事件名称（例如“Network.responseReceived”）。
            回调：事件调用的函数（同步或异步）。
            临时：第一次调用后删除。

        返回：
            用于删除的回调 ID。

        注意：
            对于特定于页面的事件，请改用 Tab.on()。"""

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback
        logger.debug(
            f'Registering callback: event={event_name}, temporary={temporary}, '
            f'async={asyncio.iscoroutinefunction(callback)}'
        )
        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """从浏览器中删除回调。"""
        logger.debug(f'Removing callback: id={callback_id}')
        return await self._connection_handler.remove_callback(callback_id)

    async def enable_fetch_events(
        self,
        handle_auth_requests: bool = False,
        resource_type: Optional[ResourceType] = None,
    ):
        """通过 Fetch 域启用网络请求拦截。

        允许在发送请求之前监视、修改或阻止请求。
        所有匹配的请求都会暂停，直到明确继续。

        参数：
            handle_auth_requests：拦截身份验证质询。
            resource_type：按类型过滤（XHR、Fetch、Document 等）。空=全部。

        注意：
            暂停的请求必须继续，否则将超时。"""
        logger.debug(
            f'Enabling Fetch events: handle_auth={handle_auth_requests}, '
            f'resource_type={resource_type}'
        )
        return await self._connection_handler.execute_command(
            FetchCommands.enable(
                handle_auth_requests=handle_auth_requests,
                resource_type=resource_type,
            )
        )

    async def disable_fetch_events(self):
        """禁用请求拦截并释放任何暂停的请求。"""
        logger.debug('Disabling Fetch events')
        return await self._connection_handler.execute_command(FetchCommands.disable())

    async def enable_runtime_events(self):
        """启用运行时事件。"""
        logger.debug('Enabling Runtime events')
        return await self._connection_handler.execute_command(RuntimeCommands.enable())

    async def disable_runtime_events(self):
        """禁用运行时事件。"""
        logger.debug('Disabling Runtime events')
        return await self._connection_handler.execute_command(RuntimeCommands.disable())

    async def continue_request(
        self,
        request_id: str,
        url: Optional[str] = None,
        method: Optional[RequestMethod] = None,
        post_data: Optional[str] = None,
        headers: Optional[list[HeaderEntry]] = None,
        intercept_response: Optional[bool] = None,
    ):
        """继续暂停的请求而不进行修改。"""
        logger.debug(f'Continuing request: id={request_id}')
        return await self._execute_command(
            FetchCommands.continue_request(
                request_id=request_id,
                url=url,
                method=method,
                post_data=post_data,
                headers=headers,
                intercept_response=intercept_response,
            )
        )

    async def fail_request(self, request_id: str, error_reason: ErrorReason):
        """请求失败并显示错误代码。"""
        logger.debug(f'Failing request: id={request_id}, reason={error_reason}')
        return await self._execute_command(FetchCommands.fail_request(request_id, error_reason))

    async def fulfill_request(
        self,
        request_id: str,
        response_code: int,
        response_headers: Optional[list[HeaderEntry]] = None,
        body: Optional[str] = None,
        response_phrase: Optional[str] = None,
    ):
        """使用响应数据完成请求。"""
        logger.debug(
            f'Fulfilling request: id={request_id}, code={response_code}, '
            f'headers={bool(response_headers)}, body={bool(body)}'
        )
        return await self._execute_command(
            FetchCommands.fulfill_request(
                request_id=request_id,
                response_code=response_code,
                response_headers=response_headers,
                body=body,
                response_phrase=response_phrase,
            )
        )

    @staticmethod
    def _validate_connection_port(connection_port: Optional[int]):
        """验证连接端口。"""
        if connection_port and connection_port < 0:
            logger.error(f'Invalid connection port: {connection_port}')
            raise InvalidConnectionPort()

    async def _continue_request_callback(self, event: RequestPausedEvent):
        """用于继续暂停的请求的内部回调。"""
        request_id = event['params']['requestId']
        logger.debug(f'[Fetch] REQUEST_PAUSED -> continue: id={request_id}')
        return await self.continue_request(request_id)

    async def _continue_request_with_auth_callback(
        self,
        event: RequestPausedEvent,
        proxy_username: Optional[str],
        proxy_password: Optional[str],
    ):
        """代理身份验证的内部回调。"""
        request_id = event['params']['requestId']
        logger.debug(
            f'[Fetch] AUTH_REQUIRED -> provide credentials: id={request_id}, '
            f'user_set={bool(proxy_username)}'
        )
        response: Response = await self._execute_command(
            FetchCommands.continue_request_with_auth(
                request_id,
                auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )
        await self.disable_fetch_events()
        return response

    @staticmethod
    async def _tab_continue_request_callback(event: RequestPausedEvent, tab: Tab):
        """用于在选项卡级别继续暂停的请求的内部回调。"""
        request_id = event['params']['requestId']
        logger.debug(f'[Tab Fetch] REQUEST_PAUSED -> continue: id={request_id}')
        return await tab.continue_request(request_id)

    @staticmethod
    async def _tab_continue_request_with_auth_callback(
        event: RequestPausedEvent,
        tab: Tab,
        proxy_username: Optional[str],
        proxy_password: Optional[str],
    ):
        """用于选项卡级别的代理/服务器身份验证的内部回调。"""
        request_id = event['params']['requestId']
        logger.debug(
            f'[Tab Fetch] AUTH_REQUIRED -> provide credentials: id={request_id}, '
            f'user_set={bool(proxy_username)}'
        )
        response: Response = await tab.continue_with_auth(
            request_id=request_id,
            auth_challenge_response=AuthChallengeResponseType.PROVIDE_CREDENTIALS,
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
        await tab.disable_fetch_events()
        return response

    async def _setup_context_proxy_auth_for_tab(
        self, tab: Tab, browser_context_id: Optional[str]
    ) -> None:
        """如果选项卡的上下文存储了凭据，则为选项卡启用代理身份验证处理。"""
        if not browser_context_id:
            return
        creds = self._context_proxy_auth.get(browser_context_id)
        if not creds:
            return
        username, password = creds
        logger.debug(
            f'Enabling context-level proxy auth for tab (context={browser_context_id}, '
            f'user_set={bool(username)}'
        )
        await tab.enable_fetch_events(handle_auth=True)
        await tab.on(
            FetchEvent.REQUEST_PAUSED,
            partial(
                self._tab_continue_request_callback,
                tab=tab,
            ),
            temporary=True,
        )
        await tab.on(
            FetchEvent.AUTH_REQUIRED,
            partial(
                self._tab_continue_request_with_auth_callback,
                tab=tab,
                proxy_username=username,
                proxy_password=password,
            ),
            temporary=True,
        )

    async def _apply_user_agent_override(self, tab: Tab) -> None:
        """如果设置了 --user-agent=，则将一致的用户代理覆盖应用于选项卡。

        检测浏览器选项中的 --user-agent= 参数并自动
        同步 HTTP 标头、导航器 JS 属性和客户端提示
        通过 CDP Emulation.setUserAgentOverride + JS 注入。"""
        user_agent = self._get_user_agent_from_options()
        if not user_agent:
            return

        parsed = UserAgentParser.parse(user_agent)
        logger.debug('Applying User-Agent override: %s', user_agent[:60])

        await tab._execute_command(
            EmulationCommands.set_user_agent_override(
                user_agent=user_agent,
                platform=parsed.platform,
                user_agent_metadata=parsed.user_agent_metadata,
            )
        )

        if parsed.navigator_override_js:
            await tab._execute_command(
                PageCommands.add_script_to_evaluate_on_new_document(
                    source=parsed.navigator_override_js,
                    run_immediately=True,
                )
            )

    def _get_user_agent_from_options(self) -> Optional[str]:
        """从 --user-agent= 浏览器参数中提取 User-Agent 值。"""
        for arg in self.options.arguments:
            if arg.startswith('--user-agent='):
                return arg[len('--user-agent=') :]
        return None

    async def _verify_browser_running(self):
        """验证浏览器启动成功。

        加薪：
            FailedToStartBrowser：如果浏览器启动失败。"""
        logger.debug(f'Verifying browser is running (timeout={self.options.start_timeout})')
        if not await self._is_browser_running(self.options.start_timeout):
            logger.error('Browser failed to start within timeout')
            raise FailedToStartBrowser()

    async def _configure_proxy(
        self, private_proxy: bool, proxy_credentials: tuple[Optional[str], Optional[str]]
    ):
        """如果需要，设置代理身份验证处理。"""
        if not private_proxy:
            return

        logger.debug(
            'Configuring proxy authentication: '
            f'credentials provided={bool(proxy_credentials[0] or proxy_credentials[1])}'
        )
        await self.enable_fetch_events(handle_auth_requests=True)
        await self.on(
            FetchEvent.REQUEST_PAUSED,
            self._continue_request_callback,
            temporary=True,
        )
        await self.on(
            FetchEvent.AUTH_REQUIRED,
            partial(
                self._continue_request_with_auth_callback,
                proxy_username=proxy_credentials[0],
                proxy_password=proxy_credentials[1],
            ),
            temporary=True,
        )

    @staticmethod
    def _is_valid_tab(target: TargetInfo) -> bool:
        """检查目标是否是有效的浏览器选项卡（过滤掉扩展程序）。"""
        return target.get('type') == 'page' and 'chrome-extension://' not in target.get('url', '')

    @staticmethod
    async def _get_valid_tab_id(targets: list[TargetInfo]) -> str:
        """查找有效的附加选项卡 ID。

        加薪：
            NoValidTabFound：如果未找到有效的附加选项卡。"""
        valid_tab = next(
            (
                tab
                for tab in targets
                if tab.get('type') == 'page' and 'extension' not in tab.get('url', '')
            ),
            None,
        )

        if not valid_tab:
            logger.error(f'No valid tab found among {len(targets)} targets')
            raise NoValidTabFound()

        tab_id = valid_tab.get('targetId')
        if not tab_id:
            logger.error('Valid tab missing targetId')
            raise NoValidTabFound('Tab missing targetId')

        return tab_id

    async def _is_browser_running(self, timeout: int = 10) -> bool:
        """检查浏览器进程是否正在运行并且 CDP 端点是否有响应。"""
        for _ in range(timeout):
            if await self._connection_handler.ping():
                return True
            await asyncio.sleep(1)

        return False

    async def _execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse], timeout: int = 60
    ) -> T_CommandResponse:
        """执行CDP命令并返回结果（浏览器通信的核心方法）。"""
        logger.debug(f'Executing command: {command.get("method")} (timeout={timeout})')
        return await self._connection_handler.execute_command(command, timeout=timeout)

    def _setup_user_dir(self):
        """如果选项中未指定，则设置临时用户数据目录。"""
        user_data_dir = self._get_user_data_dir()
        if user_data_dir and self.options.browser_preferences:
            self._set_browser_preferences_in_user_data_dir(user_data_dir)
        elif not user_data_dir:
            temp_dir = self._temp_directory_manager.create_temp_dir()
            #对于所有浏览器，请使用临时目录
            self.options.arguments.append(f'--user-data-dir={temp_dir.name}')
            if self.options.browser_preferences:
                self._set_browser_preferences_in_temp_dir(temp_dir)
        logger.debug(f'User dir setup complete: {self._get_user_data_dir()}')

    def _set_browser_preferences_in_temp_dir(self, temp_dir: TemporaryDirectory):
        os.mkdir(os.path.join(temp_dir.name, 'Default'))
        preferences = self.options.browser_preferences
        with open(
            os.path.join(temp_dir.name, 'Default', 'Preferences'), 'w', encoding='utf-8'
        ) as json_file:
            json.dump(preferences, json_file)
        logger.debug('Wrote browser preferences to temp user dir')

    def _set_browser_preferences_in_user_data_dir(self, user_data_dir: str):
        """在用户数据目录中设置浏览器首选项。

        该函数将：
        1. 创建现有首选项文件的备份（如果存在）
        2.如果Default目录不存在，则创建它
        3. 将新的首选项写入 Preferences 文件

        参数：
            user_data_dir：用户数据目录的路径"""
        default_dir = os.path.join(user_data_dir, 'Default')
        os.makedirs(default_dir, exist_ok=True)

        preferences_path = os.path.join(default_dir, 'Preferences')
        self._backup_preferences_dir = os.path.join(default_dir, 'Preferences.backup')

        if os.path.exists(preferences_path):
            #备份现有的首选项文件
            shutil.copy2(preferences_path, self._backup_preferences_dir)

        preferences = {}
        if os.path.exists(preferences_path):
            with suppress(json.JSONDecodeError):
                with open(preferences_path, 'r', encoding='utf-8') as preferences_file:
                    preferences = json.load(preferences_file)
        preferences.update(self.options.browser_preferences)
        with open(preferences_path, 'w', encoding='utf-8') as json_file:
            json.dump(preferences, json_file, indent=2)
        logger.debug(f'Updated browser preferences in user data dir: {preferences_path}')

    def _get_user_data_dir(self) -> Optional[str]:
        for arg in self.options.arguments:
            if arg.startswith('--user-data-dir='):
                return arg.split('=', 1)[1]
        return None

    @staticmethod
    def _validate_ws_address(ws_address: str):
        """验证 WebSocket 地址。"""
        min_slashes = 4
        if not ws_address.startswith(('ws://', 'wss://')):
            logger.error('Invalid WebSocket address: missing ws:// or wss:// prefix')
            raise InvalidWebSocketAddress('WebSocket address must start with ws:// or wss://')
        if len(ws_address.split('/')) < min_slashes:
            logger.error('Invalid WebSocket address: not enough slashes')
            raise InvalidWebSocketAddress(
                f'WebSocket address must contain at least {min_slashes} slashes'
            )

    async def _setup_ws_address(self, ws_address: str):
        """设置浏览器的 WebSocket 地址。"""
        self._validate_ws_address(ws_address)
        self._ws_address = ws_address
        self._connection_handler._ws_address = self._ws_address
        await self._connection_handler._ensure_active_connection()
        logger.info('WebSocket address set for browser-level connection')

    def _get_tab_kwargs(self, target_id: str, browser_context_id: Optional[str] = None) -> dict:
        """获取用于根据 WebSocket 地址创建选项卡的 kwargs。
        如果设置了 WebSocket 地址，则将使用 WebSocket 地址创建选项卡。
        否则，将使用连接端口和目标 ID 创建该选项卡。

        参数：
            target_id：选项卡的目标 ID。
            browser_context_id：选项卡的浏览器上下文 ID。

        返回：
            用于创建选项卡的 kwargs 字典。"""
        kwargs: dict[str, Any] = {
            'target_id': target_id,
            'browser_context_id': browser_context_id,
        }
        if self._ws_address:
            kwargs['ws_address'] = self._get_tab_ws_address(target_id)
        else:
            kwargs['connection_port'] = self._connection_port
        logger.debug(f'Tab kwargs resolved for {target_id}: using_ws={bool(self._ws_address)}')
        return kwargs

    def _get_tab_ws_address(self, tab_id: str) -> str:
        """获取特定选项卡的 WebSocket 地址，保留任何查询或片段
        原始浏览器级 WebSocket URL 中存在的组件。

        这确保通过查询字符串传递身份验证令牌（例如，
        ws://host/devtools/browser/abc?token=XYZ) 切换时保留
        到页面级端点（devtools/page/<tab_id>），这很关键
        适用于无浏览器或经过身份验证的 CDP 代理等提供商。"""
        if not self._ws_address:
            raise InvalidWebSocketAddress('WebSocket address is not set')

        parts = urlsplit(self._ws_address)
        #保留scheme和netloc；构建页面路径并保留查询/片段
        page_path = f'/devtools/page/{tab_id}'
        ws = urlunsplit((parts.scheme, parts.netloc, page_path, parts.query, parts.fragment))
        logger.debug(f'Resolved tab WebSocket address: {ws}')
        return ws

    @staticmethod
    def _sanitize_proxy_and_extract_auth(
        proxy_server: str,
    ) -> tuple[str, Optional[tuple[str, str]]]:
        """从代理 URL 中删除凭据并返回经过清理的 URL 加（用户、通行证）。

        接受如下输入：
        - 用户名:密码@主机:端口
        - http://用户名:密码@主机:端口
        -socks5://用户名:密码@主机:端口
        - 主机：端口（无凭据）
        返回 (sanitized_proxy, (user, pass) | None)。
        确保方案存在于清理后的 URL 中（默认为 http）。"""
        base = proxy_server if '://' in proxy_server else f'http://{proxy_server}'
        parts = urlsplit(base)
        netloc = parts.netloc
        creds: Optional[tuple[str, str]] = None
        if '@' in netloc:
            cred_part, host_part = netloc.split('@', 1)
            if ':' in cred_part:
                user, pwd = cred_part.split(':', 1)
            else:
                user, pwd = cred_part, ''
            creds = (user, pwd)
            sanitized = urlunsplit((
                parts.scheme,
                host_part,
                parts.path,
                parts.query,
                parts.fragment,
            ))
        else:
            #没有信用；保障方案
            sanitized = urlunsplit((
                parts.scheme,
                parts.netloc,
                parts.path,
                parts.query,
                parts.fragment,
            ))
        return sanitized, creds

    @abstractmethod
    def _get_default_binary_location(self) -> str:
        """获取默认浏览器可执行路径（由子类实现）。"""
        pass
