from __future__ import annotations

import asyncio
import base64 as _b64
import contextlib
import io
import shutil
import warnings
import zipfile
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from tempfile import mkdtemp
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Optional,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    overload,
)

import aiofiles

from ljp_page._module.request.brower.pydoll.browser.requests import Request
from ljp_page._module.request.brower.pydoll.commands import (
    DomCommands,
    FetchCommands,
    NetworkCommands,
    PageCommands,
    RuntimeCommands,
    StorageCommands,
    TargetCommands,
)
from ljp_page._module.request.brower.pydoll.connection import ConnectionHandler
from ljp_page._module.request.brower.pydoll.constants import By, PageLoadState
from ljp_page._module.request.brower.pydoll.elements.mixins import FindElementsMixin
from ljp_page._module.request.brower.pydoll.elements.shadow_root import ShadowRoot
from ljp_page._module.request.brower.pydoll.elements.web_element import WebElement
from ljp_page._module.request.brower.pydoll.exceptions import (
    CommandExecutionTimeout,
    DownloadTimeout,
    IFrameNotFound,
    InvalidFileExtension,
    InvalidIFrame,
    InvalidScriptWithElement,
    InvalidTabInitialization,
    MissingScreenshotPath,
    NavigationError,
    NetworkEventsNotEnabled,
    NoDialogPresent,
    NotAnIFrame,
    PageLoadTimeout,
    TopLevelTargetRequired,
    WaitElementTimeout,
    WebSocketConnectionClosed,
)
from ljp_page._module.request.brower.pydoll import ExtractionEngine
from ljp_page._module.request.brower.pydoll.interactions import KeyboardAPI, MouseAPI, ScrollAPI
from ljp_page._module.request.brower.pydoll.interactions.iframe import IFrameContext
from browser.types import DownloadBehavior, DownloadProgressState
from dom.types import Node, ShadowRootType
from network.types import ResourceType
from page.events import PageEvent
from page.types import FrameResourceTree, ScreenshotFormat
from runtime.methods import (
    SerializationOptions,
)
from runtime.types import CallArgument
from target.types import TargetInfo
from ljp_page._module.request.brower.pydoll.utils import (
    decode_base64_to_bytes,
    has_return_outside_function,
)
from ljp_page._module.request.brower.pydoll import (
    build_asset_filename,
    collect_frame_resources,
    filter_fetchable_resources,
    inline_all_assets,
    rewrite_html_urls,
)

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.chromium.base import Browser
    from ljp_page._module.request.brower.pydoll import ExtractionModel
    from base import EmptyResponse, Response
    from browser.events import (
        DownloadProgressEvent,
        DownloadWillBeginEvent,
    )
    from dom.methods import (
        DescribeNodeResponse,
        GetDocumentResponse,
        ResolveNodeResponse,
    )
    from fetch.types import AuthChallengeResponseType, HeaderEntry, RequestStage
    from network.events import RequestWillBeSentEvent
    from network.methods import GetCookiesResponse as NetworkGetCookiesResponse
    from network.methods import GetResponseBodyResponse
    from network.types import (
        Cookie,
        CookieParam,
        ErrorReason,
        RequestMethod,
    )
    from page.events import FileChooserOpenedEvent
    from page.methods import (
        CaptureScreenshotResponse,
        GetResourceContentResponse,
        GetResourceTreeResponse,
        NavigateResponse,
        PrintToPDFResponse,
    )
    from runtime.methods import CallFunctionOnResponse, EvaluateResponse
    from storage.methods import GetCookiesResponse as StorageGetCookiesResponse
    from target.methods import AttachToTargetResponse, GetTargetsResponse

from ljp_page.logger import logger

IFrame: TypeAlias = 'Tab'

T = TypeVar('T', bound='ExtractionModel')

_CLOUDFLARE_CHALLENGE_DOMAIN = 'challenges.cloudflare.com'
_CLOUDFLARE_IFRAME_SELECTOR = f'iframe[src*="{_CLOUDFLARE_CHALLENGE_DOMAIN}"]'
_CLOUDFLARE_CHECKBOX_SELECTOR = 'span.cb-i'


class Tab(FindElementsMixin):
    """通过 Chrome DevTools 协议控制浏览器选项卡。

    网页自动化的主要界面，包括导航、DOM 操作、
    JavaScript 执行、事件处理、网络监控和专门任务
    就像 Cloudflare 绕过一样。"""

    def __init__(
        self,
        browser: Browser,
        connection_port: Optional[int] = None,
        target_id: Optional[str] = None,
        browser_context_id: Optional[str] = None,
        ws_address: Optional[str] = None,
    ):
        """为现有浏览器选项卡初始化选项卡控制器。

        参数：
            browser：创建此选项卡的浏览器实例。
            连接端口：CDP WebSocket 端口。
            target_id：此选项卡的 CDP 目标标识符。
            browser_context_id：可选的浏览器上下文 ID。
            ws_address：此选项卡的可选 WebSocket 地址。"""
        if not any([connection_port, target_id, ws_address]):
            raise InvalidTabInitialization()

        self._browser = browser
        self._connection_port = connection_port
        self._target_id = target_id
        self._ws_address = ws_address
        self._browser_context_id = browser_context_id
        self._connection_handler = self._get_connection_handler()
        self._page_events_enabled = False
        self._network_events_enabled = False
        self._fetch_events_enabled = False
        self._dom_events_enabled = False
        self._runtime_events_enabled = False
        self._intercept_file_chooser_dialog_enabled = False
        self._cloudflare_captcha_callback_id: Optional[int] = None
        self._request: Optional[Request] = None
        self._scroll: Optional[ScrollAPI] = None
        self._keyboard: Optional[KeyboardAPI] = None
        self._mouse: MouseAPI = MouseAPI(self)
        self._extraction_engine: Optional[ExtractionEngine] = None
        logger.debug(
            (
                f'Tab initialized: target_id={self._target_id}, '
                f'ws_address_set={bool(self._ws_address)}, '
                f'context_id={self._browser_context_id}, port={self._connection_port}'
            )
        )

    @property
    def page_events_enabled(self) -> bool:
        """是否启用 CDP 页面域事件。"""
        return self._page_events_enabled

    @property
    def network_events_enabled(self) -> bool:
        """是否启用 CDP 网络域事件。"""
        return self._network_events_enabled

    @property
    def fetch_events_enabled(self) -> bool:
        """是否启用 CDP Fetch 域事件（请求拦截）。"""
        return self._fetch_events_enabled

    @property
    def dom_events_enabled(self) -> bool:
        """是否启用 CDP DOM 域事件。"""
        return self._dom_events_enabled

    @property
    def runtime_events_enabled(self) -> bool:
        """是否启用 CDP 运行时域事件。"""
        return self._runtime_events_enabled

    @property
    def request(self) -> Request:
        """使用浏览器的 fetch API 获取用于发出 HTTP 请求的请求对象。

        返回：
            Request：Request 类的一个实例，用于发出 HTTP 请求。"""
        if self._request is None:
            self._request = Request(self)
        return self._request

    @property
    def scroll(self) -> ScrollAPI:
        """获取用于控制页面滚动行为的滚动 API。

        返回：
            ScrollAPI：用于滚动操作的 ScrollAPI 类的实例。"""
        if self._scroll is None:
            self._scroll = ScrollAPI(self)
        return self._scroll

    @property
    def keyboard(self) -> KeyboardAPI:
        """获取用于在页面级别控制键盘输入的键盘 API。

        返回：
            KeyboardAPI：用于键盘操作的KeyboardAPI类的实例。"""
        if self._keyboard is None:
            self._keyboard = KeyboardAPI(self)
        return self._keyboard

    @property
    def mouse(self) -> MouseAPI:
        """获取用于控制鼠标输入的鼠标API。

        返回：
            MouseAPI：用于鼠标操作的 MouseAPI 类的实例。"""
        return self._mouse

    @property
    def _extractor(self) -> ExtractionEngine:
        """延迟初始化的提取引擎。"""
        if self._extraction_engine is None:
            self._extraction_engine = ExtractionEngine(self)
        return self._extraction_engine

    async def extract(
        self,
        model: type[T],
        *,
        scope: Optional[str] = None,
        timeout: int = 0,
    ) -> T:
        """将结构化数据从页面提取到类型化模型中。

        参数：
            model：定义提取模式的 ExtractionModel 子类。
            范围：可选的 CSS/XPath 选择器，用于限制提取区域。
            timeout：等待元素的秒数（0 = 不等待）。

        返回：
            使用提取的数据填充模型实例。

        加薪：
            FieldExtractionFailed：如果无法提取必填字段。
            InvalidExtractionModel：如果模型定义无效。"""
        return await self._extractor.extract(model, scope=scope, timeout=timeout)

    async def extract_all(
        self,
        model: type[T],
        *,
        scope: str,
        timeout: int = 0,
        limit: Optional[int] = None,
    ) -> list[T]:
        """从页面上的重复容器中提取多个项目。

        与范围选择器匹配的每个元素都会生成一个模型实例。
        字段是相对于每个范围容器进行解析的。

        参数：
            model：定义提取模式的 ExtractionModel 子类。
            范围：重复容器的 CSS/XPath 选择器（必需）。
            timeout：等待元素的秒数（0 = 不等待）。
            limit：要提取的最大项目数（无=全部）。

        返回：
            已填充模型实例的列表。"""
        return await self._extractor.extract_all(model, scope=scope, timeout=timeout, limit=limit)

    @property
    def intercept_file_chooser_dialog_enabled(self) -> bool:
        """文件选择器对话框拦截是否处于活动状态。"""
        return self._intercept_file_chooser_dialog_enabled

    @property
    async def current_url(self) -> str:
        """获取当前页面 URL（反映重定向和客户端导航）。"""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('window.location.href')
        )
        return response['result']['result']['value']

    @property
    async def page_source(self) -> str:
        """获取当前页面的完整 HTML 源（实时 DOM 状态）。"""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('document.documentElement.outerHTML')
        )
        return response['result']['result']['value']

    @property
    async def title(self) -> str:
        """获取当前页面标题。"""
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate('document.title')
        )
        return response['result']['result'].get('value', '')

    async def enable_page_events(self):
        """启用 CDP 页面域事件（加载、导航、对话框等）。"""
        logger.debug('Enabling Page events')
        response = await self._execute_command(PageCommands.enable())
        self._page_events_enabled = True
        logger.debug('Page events enabled')
        return response

    async def enable_network_events(self):
        """启用 CDP 网络域事件（请求、响应等）。"""
        logger.debug('Enabling Network events')
        response = await self._execute_command(NetworkCommands.enable())
        self._network_events_enabled = True
        logger.debug('Network events enabled')
        return response

    async def enable_fetch_events(
        self,
        handle_auth: bool = False,
        resource_type: Optional[ResourceType] = None,
        request_stage: Optional[RequestStage] = None,
    ):
        """启用 CDP Fetch 域以进行请求拦截。

        参数：
            handle_auth：拦截身份验证质询。
            resource_type：按资源类型过滤（如果为 None，则全部过滤）。
            request_stage：何时拦截（请求/响应）。

        注意：
            拦截的请求必须明确继续或超时。"""
        logger.debug(
            f'Enabling Fetch events: handle_auth={handle_auth}, resource_type={resource_type}, '
            f'stage={request_stage}'
        )
        response: Response[EmptyResponse] = await self._execute_command(
            FetchCommands.enable(
                handle_auth_requests=handle_auth,
                resource_type=resource_type,
                request_stage=request_stage,
            )
        )
        self._fetch_events_enabled = True
        logger.debug('Fetch events enabled')
        return response

    async def enable_dom_events(self):
        """启用 CDP DOM 域事件（文档结构更改）。"""
        logger.debug('Enabling DOM events')
        response = await self._execute_command(DomCommands.enable())
        self._dom_events_enabled = True
        logger.debug('DOM events enabled')
        return response

    async def enable_runtime_events(self):
        """启用 CDP 运行时域事件。"""
        logger.debug('Enabling Runtime events')
        response = await self._execute_command(RuntimeCommands.enable())
        self._runtime_events_enabled = True
        logger.debug('Runtime events enabled')
        return response

    async def enable_intercept_file_chooser_dialog(self):
        """启用文件选择器对话框拦截以进行自动上传。

        注意：
            为了方便起见，使用expect_file_chooser上下文管理器。"""
        logger.info('Enabling file chooser interception')
        response = await self._execute_command(PageCommands.set_intercept_file_chooser_dialog(True))
        self._intercept_file_chooser_dialog_enabled = True
        logger.debug('File chooser interception enabled')
        return response

    async def enable_auto_solve_cloudflare_captcha(
        self,
        custom_selector: Optional[tuple[By, str]] = None,
        time_before_click: Optional[float] = None,
        time_to_wait_captcha: float = 5,
    ):
        """启用自动 Cloudflare Turnstile 验证码绕过。

        参数：
            custom_selector：已弃用 — 被忽略。 Cloudflare Turnstile 现已上线
                通过影子根检查自动检测到。
            time_before_click：已弃用 — 已忽略。复选框现在是
                通过影子根轮询定位并立即单击。
            time_to_wait_captcha：验证码检测超时（默认5秒）。"""
        if custom_selector is not None:
            warnings.warn(
                'custom_selector is deprecated and ignored. Cloudflare Turnstile is now '
                'detected automatically via shadow root inspection.',
                DeprecationWarning,
                stacklevel=2,
            )

        if time_before_click is not None:
            warnings.warn(
                'time_before_click is deprecated and ignored. The checkbox is now '
                'located via shadow root polling and clicked immediately.',
                DeprecationWarning,
                stacklevel=2,
            )

        logger.info('Enabling Cloudflare captcha auto-solve')
        if not self.page_events_enabled:
            await self.enable_page_events()

        callback = partial(
            self._bypass_cloudflare,
            time_to_wait_captcha=time_to_wait_captcha,
        )

        self._cloudflare_captcha_callback_id = await self.on(PageEvent.LOAD_EVENT_FIRED, callback)
        logger.debug(
            f'Cloudflare auto-solve callback registered: id={self._cloudflare_captcha_callback_id}'
        )

    async def disable_fetch_events(self):
        """禁用 CDP 获取域并释放暂停的请求。"""
        logger.debug('Disabling Fetch events')
        response = await self._execute_command(FetchCommands.disable())
        self._fetch_events_enabled = False
        logger.debug('Fetch events disabled')
        return response

    async def disable_page_events(self):
        """禁用 CDP 页面域事件。"""
        logger.debug('Disabling Page events')
        response = await self._execute_command(PageCommands.disable())
        self._page_events_enabled = False
        logger.debug('Page events disabled')
        return response

    async def disable_network_events(self):
        """禁用 CDP 网络域事件。"""
        logger.debug('Disabling Network events')
        response = await self._execute_command(NetworkCommands.disable())
        self._network_events_enabled = False
        logger.debug('Network events disabled')
        return response

    async def disable_dom_events(self):
        """禁用 CDP DOM 域事件。"""
        logger.debug('Disabling DOM events')
        response = await self._execute_command(DomCommands.disable())
        self._dom_events_enabled = False
        logger.debug('DOM events disabled')
        return response

    async def disable_runtime_events(self):
        """禁用 CDP 运行时域事件。"""
        logger.debug('Disabling Runtime events')
        response = await self._execute_command(RuntimeCommands.disable())
        self._runtime_events_enabled = False
        logger.debug('Runtime events disabled')
        return response

    async def disable_intercept_file_chooser_dialog(self):
        """禁用文件选择器对话框拦截。"""
        logger.info('Disabling file chooser interception')
        response = await self._execute_command(
            PageCommands.set_intercept_file_chooser_dialog(False)
        )
        self._intercept_file_chooser_dialog_enabled = False
        logger.debug('File chooser interception disabled')
        return response

    async def disable_auto_solve_cloudflare_captcha(self):
        """禁用自动 Cloudflare Turnstile 验证码绕过。"""
        logger.info('Disabling Cloudflare captcha auto-solve')
        await self._connection_handler.remove_callback(self._cloudflare_captcha_callback_id)
        self._cloudflare_captcha_callback_id = None

    async def close(self):
        """关闭此浏览器选项卡。

        注意：
            调用该方法后Tab实例失效。"""
        logger.info(f'Closing tab: target_id={self._target_id}')
        result = await self._execute_command(PageCommands.close())
        self._browser._tabs_opened.pop(self._target_id)
        logger.debug('Tab closed and removed from browser registry')
        return result

    async def get_frame(self, frame: 'WebElement') -> IFrame:
        """.. 已弃用:: ?.?.?
            直接使用 iframe `WebElement` 实例；该方法将在
            未来的版本。

        获取用于与 iframe 内容交互的 Tab 对象。

        参数：
            框架：代表 iframe 标签的选项卡。

        返回：
            为 iframe 交互配置的选项卡实例。

        加薪：
            NotAnIFrame：如果元素不是 iframe。
            InvalidIFrame：如果 iframe 缺少有效的 src 属性。
            IFrameNotFound：如果在浏览器中找不到 iframe 目标。"""
        warnings.warn(
            'Tab.get_frame() is deprecated and will be removed in a future version. '
            'Interact with iframe WebElements directly.',
            DeprecationWarning,
            stacklevel=2,
        )
        logger.debug(f'Resolving iframe: tag={frame.tag_name}')
        if not frame.tag_name == 'iframe':
            raise NotAnIFrame

        frame_url = frame.get_attribute('src')
        logger.debug(f'Iframe src resolved: {frame_url}')
        if not frame_url:
            raise InvalidIFrame('The iframe does not have a valid src attribute')

        targets = await self._browser.get_targets()
        iframe_target = next((target for target in targets if target['url'] == frame_url), None)
        if not iframe_target:
            raise IFrameNotFound('The target for the iframe was not found')

        target_id = iframe_target['targetId']
        if target_id in self._browser._tabs_opened:
            logger.debug(f'Iframe tab already tracked: {target_id}')
            return self._browser._tabs_opened[target_id]

        tab = Tab(
            self._browser,
            target_id=target_id,
            connection_port=self._connection_port,
        )
        self._browser._tabs_opened[target_id] = tab
        logger.debug(f'Iframe tab created and registered: {target_id}')
        return tab

    async def find_shadow_roots(self, deep: bool = False, timeout: float = 0) -> list[ShadowRoot]:
        """找到页面中所有的影子根。

        遍历整个 DOM 树（包括 iframe 和嵌套的 Shadow DOM）
        收集所有找到的影子根。当
        影子主机元素选择器未知或动态（例如，Cloudflare
        挑战页面）。

        参数：
            deep：如果为 True，还会遍历跨域 iframe (OOPIF)
                发现它们里面的影子根。返回的 ShadowRoot
                对象将自动通过CDP命令路由
                正确的 OOPIF 会话。
            timeout：等待影子根出现的最大秒数。
                当 > 0 时，重复轮询 DOM（每 0.5 秒）直到至少
                找到一个影子根或超时到期。有用的时候
                影子主机是异步注入的（例如 Cloudflare
                OOPIF 内旋转栅门加载）。

        返回：
            页面中找到的 ShadowRoot 实例的列表。

        加薪：
            WaitElementTimeout：如果超时> 0并且未找到影子根
                在规定的期限内。"""
        logger.debug('Finding all shadow roots in page (timeout=%s)', timeout)

        if not timeout:
            return await self._collect_all_shadow_roots(deep)

        start_time = asyncio.get_event_loop().time()
        while True:
            shadow_roots = await self._collect_all_shadow_roots(deep)
            if shadow_roots:
                return shadow_roots

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'Timed out after {timeout}s waiting for shadow roots in page'
                )

            await asyncio.sleep(0.5)

    async def _collect_all_shadow_roots(self, deep: bool) -> list[ShadowRoot]:
        """从主文档和可选的 OOPIF 中收集影子根。"""
        response: GetDocumentResponse = await self._execute_command(
            DomCommands.get_document(depth=-1, pierce=True)
        )
        root_node = response.get('result', {}).get('root', {})

        shadow_root_entries: list[tuple[Node, int | None]] = []
        self._collect_shadow_roots_from_tree(root_node, shadow_root_entries)

        shadow_roots: list[ShadowRoot] = []
        for shadow_data, host_backend_id in shadow_root_entries:
            backend_node_id = shadow_data.get('backendNodeId')
            if not backend_node_id:
                continue

            try:
                resolve_response: ResolveNodeResponse = await self._execute_command(
                    DomCommands.resolve_node(backend_node_id=backend_node_id)
                )
                shadow_object_id = resolve_response['result']['object']['objectId']
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
                logger.debug(f'Failed to resolve shadow root: backend_node_id={backend_node_id}')
                continue

            try:
                host_element = await self._resolve_shadow_host(host_backend_id)
            except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
                logger.debug(f'Failed to resolve shadow host: backend_node_id={host_backend_id}')
                host_element = None
            mode = ShadowRootType(shadow_data.get('shadowRootType', 'open'))
            shadow_roots.append(
                ShadowRoot(
                    object_id=shadow_object_id,
                    connection_handler=self._connection_handler,
                    mode=mode,
                    host_element=host_element,
                )
            )

        if deep:
            oopif_roots = await self._collect_oopif_shadow_roots()
            shadow_roots.extend(oopif_roots)

        logger.debug(f'Found {len(shadow_roots)} shadow roots')
        return shadow_roots

    async def _resolve_shadow_host(self, host_backend_id: int | None) -> WebElement | None:
        """解析影子根的主机元素（尽力而为）。"""
        if not host_backend_id:
            return None

        host_response: ResolveNodeResponse = await self._execute_command(
            DomCommands.resolve_node(backend_node_id=host_backend_id)
        )
        host_object_id = host_response['result']['object']['objectId']
        host_attrs = await self._get_object_attributes(object_id=host_object_id)
        return WebElement(
            host_object_id, self._connection_handler, attributes_list=host_attrs, mouse=self._mouse
        )

    async def _collect_oopif_shadow_roots(self) -> list[ShadowRoot]:
        """发现跨源 iframe (OOPIF) 内的影子根。"""
        browser_handler = ConnectionHandler(connection_port=self._connection_port)
        targets_response: GetTargetsResponse = await browser_handler.execute_command(
            TargetCommands.get_targets()
        )

        target_infos = targets_response.get('result', {}).get('targetInfos', [])
        iframe_targets = [t for t in target_infos if t.get('type') == 'iframe']

        if not iframe_targets:
            logger.debug('No OOPIF targets found')
            return []

        shadow_roots: list[ShadowRoot] = []
        for target in iframe_targets:
            roots = await self._collect_shadow_roots_from_oopif_target(target, browser_handler)
            shadow_roots.extend(roots)

        logger.debug(f'Found {len(shadow_roots)} shadow roots in OOPIFs')
        return shadow_roots

    async def _collect_shadow_roots_from_oopif_target(
        self,
        target: TargetInfo,
        browser_handler: ConnectionHandler,
    ) -> list[ShadowRoot]:
        """从单个 OOPIF 目标收集影子根。"""
        target_id = target.get('targetId', '')
        try:
            attach_response: AttachToTargetResponse = await browser_handler.execute_command(
                TargetCommands.attach_to_target(target_id=target_id, flatten=True)
            )
            session_id = attach_response.get('result', {}).get('sessionId')
            if not session_id:
                return []
        except (CommandExecutionTimeout, WebSocketConnectionClosed):
            logger.debug(f'Failed to attach to OOPIF target: {target_id}')
            return []

        try:
            get_doc_command = DomCommands.get_document(depth=-1, pierce=True)
            get_doc_command['sessionId'] = session_id
            doc_response: GetDocumentResponse = await browser_handler.execute_command(
                get_doc_command
            )
            root_node = doc_response.get('result', {}).get('root', {})
        except (CommandExecutionTimeout, WebSocketConnectionClosed):
            logger.debug(f'Failed to get document from OOPIF target: {target_id}')
            return []

        entries: list[tuple[Node, int | None]] = []
        self._collect_shadow_roots_from_tree(root_node, entries)

        iframe_context = IFrameContext(
            frame_id=target_id,
            session_handler=browser_handler,
            session_id=session_id,
        )

        results: list[ShadowRoot] = []
        for shadow_data, host_backend_id in entries:
            sr = await self._resolve_oopif_shadow_entry(
                shadow_data, host_backend_id, browser_handler, session_id, iframe_context
            )
            if sr:
                results.append(sr)
        return results

    async def _resolve_oopif_shadow_entry(
        self,
        shadow_data: Node,
        host_backend_id: int | None,
        browser_handler: ConnectionHandler,
        session_id: str,
        iframe_context: IFrameContext,
    ) -> ShadowRoot | None:
        """从 OOPIF 解析单个影子根条目。"""
        backend_node_id = shadow_data.get('backendNodeId')
        if not backend_node_id:
            return None

        try:
            resolve_command = DomCommands.resolve_node(backend_node_id=backend_node_id)
            resolve_command['sessionId'] = session_id
            resolve_response: ResolveNodeResponse = await browser_handler.execute_command(
                resolve_command
            )
            shadow_object_id = resolve_response['result']['object']['objectId']
        except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
            logger.debug(f'Failed to resolve OOPIF shadow root: backend_node_id={backend_node_id}')
            return None

        host_element = await self._resolve_oopif_shadow_host(
            host_backend_id, browser_handler, session_id
        )

        if host_element:
            host_element._iframe_context = iframe_context

        mode = ShadowRootType(shadow_data.get('shadowRootType', 'open'))
        sr = ShadowRoot(
            object_id=shadow_object_id,
            connection_handler=self._connection_handler,
            mode=mode,
            host_element=host_element,
        )

        if not host_element:
            sr._iframe_context = iframe_context

        return sr

    async def _resolve_oopif_shadow_host(
        self,
        host_backend_id: int | None,
        browser_handler: ConnectionHandler,
        session_id: str,
    ) -> WebElement | None:
        """解析 OOPIF 内影子根的主机元素（尽力而为）。"""
        if not host_backend_id:
            return None

        try:
            resolve_command = DomCommands.resolve_node(backend_node_id=host_backend_id)
            resolve_command['sessionId'] = session_id
            host_response: ResolveNodeResponse = await browser_handler.execute_command(
                resolve_command
            )
            host_object_id = host_response['result']['object']['objectId']

            describe_command = DomCommands.describe_node(object_id=host_object_id)
            describe_command['sessionId'] = session_id
            describe_response: DescribeNodeResponse = await browser_handler.execute_command(
                describe_command
            )
            node_info = describe_response.get('result', {}).get('node', {})
            attributes = node_info.get('attributes', [])
            tag_name = node_info.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            return WebElement(
                host_object_id,
                self._connection_handler,
                attributes_list=attributes,
                mouse=self._mouse,
            )
        except (CommandExecutionTimeout, WebSocketConnectionClosed, KeyError):
            logger.debug(f'Failed to resolve OOPIF shadow host: backend_node_id={host_backend_id}')
            return None

    @staticmethod
    def _collect_shadow_roots_from_tree(node: Node, results: list[tuple[Node, int | None]]) -> None:
        """递归地遍历 DOM 树，收集影子根条目。"""
        host_backend_id = node.get('backendNodeId')
        for shadow_root in node.get('shadowRoots', []):
            results.append((shadow_root, host_backend_id))
            Tab._collect_shadow_roots_from_tree(shadow_root, results)

        for child in node.get('children', []):
            Tab._collect_shadow_roots_from_tree(child, results)

        content_doc = node.get('contentDocument')
        if content_doc:
            Tab._collect_shadow_roots_from_tree(content_doc, results)

    async def bring_to_front(self):
        """将页面置于前面。"""
        logger.info('Bringing page to front')
        return await self._execute_command(PageCommands.bring_to_front())

    async def get_cookies(self) -> list[Cookie]:
        """获取当前页面可访问的所有 cookie。"""
        logger.debug('Fetching cookies for current page')
        if self._browser_context_id:
            response_storage: StorageGetCookiesResponse = await self._execute_command(
                StorageCommands.get_cookies(self._browser_context_id)
            )
            cookies = response_storage['result']['cookies']
            logger.debug(f'Fetched {len(cookies)} cookies')
            return cookies

        response_network: NetworkGetCookiesResponse = await self._execute_command(
            NetworkCommands.get_cookies()
        )
        cookies = response_network['result']['cookies']
        logger.debug(f'Fetched {len(cookies)} cookies')
        return cookies

    async def get_network_response_body(self, request_id: str) -> str:
        """获取给定请求 ID 的响应正文。

        参数：
            request_id：获取响应正文的请求 ID。

        返回：
            给定请求 ID 的响应正文。

        加薪：
            NetworkEventsNotEnabled：如果未启用网络事件。"""
        if not self.network_events_enabled:
            raise NetworkEventsNotEnabled('Network events must be enabled to get response body')

        response: GetResponseBodyResponse = await self._execute_command(
            NetworkCommands.get_response_body(request_id)
        )
        logger.debug(f'Retrieved network response body for request_id={request_id}')
        return response['result']['body']

    async def get_network_logs(self, filter: Optional[str] = None) -> list[RequestWillBeSentEvent]:
        """获取网络日志。

        参数：
            过滤器：应用于网络日志的过滤器。

        返回：
            网络日志。

        加薪：
            NetworkEventsNotEnabled：如果未启用网络事件。"""
        if not self.network_events_enabled:
            raise NetworkEventsNotEnabled('Network events must be enabled to get network logs')

        logs = self._connection_handler.network_logs
        if filter:
            logs = [
                log for log in logs if filter in log['params'].get('request', {}).get('url', '')
            ]
        logger.debug(f'Returning {len(logs)} network logs (filtered={bool(filter)})')
        return logs

    async def set_cookies(self, cookies: list[CookieParam]):
        """为当前页面设置多个cookie。

        参数：
            cookies：Cookie 参数（名称/值必填，其他可选）。

        注意：
            如果未指定，则默认为当前页面的域。"""
        logger.info(f'Setting {len(cookies)} cookies on current page')
        return await self._execute_command(
            StorageCommands.set_cookies(cookies, self._browser_context_id)
        )

    async def delete_all_cookies(self):
        """从当前浏览器上下文中删除所有 cookie。"""
        logger.info('从当前浏览器上下文中删除所有 cookie')
        return await self._execute_command(StorageCommands.clear_cookies(self._browser_context_id))

    async def go_to(self, url: str, timeout: int = 300):
        """导航到 URL 并等待加载完成。

        参数：
            url：要导航到的目标 URL。
            timeout：等待页面加载的最大秒数（默认 300）。

        加薪：
            NavigationError：如果导航失败（例如 DNS 错误）。
            PageLoadTimeout：如果页面在超时时间内未完成加载。"""
        logger.debug(f'Navigating to URL: {url} (timeout={timeout}s)')
        async with self._wait_page_load(timeout=timeout):
            response: NavigateResponse = await self._execute_command(PageCommands.navigate(url))
            error_text = response['result'].get('errorText')
            if error_text:
                raise NavigationError(url, error_text)
        logger.debug(f'Navigation complete: {url}')


    async def refresh(
        self,
        ignore_cache: bool = False,
        script_to_evaluate_on_load: Optional[str] = None,
    ):
        """重新加载当前页面并等待完成。

        参数：
            ignore_cache：如果为 True，则绕过浏览器缓存。
            script_to_evaluate_on_load：加载后执行的 JavaScript。

        加薪：
            PageLoadTimeout：如果页面在超时时间内未完成加载。"""
        logger.info(
            f'Reloading page (ignore_cache={ignore_cache}, '
            f'script_on_load={bool(script_to_evaluate_on_load)})'
        )
        async with self._wait_page_load():
            await self._execute_command(
                PageCommands.reload(
                    ignore_cache=ignore_cache,
                    script_to_evaluate_on_load=script_to_evaluate_on_load,
                )
            )
        logger.info('Page reloaded successfully')

    async def take_screenshot(
        self,
        path: Optional[str | Path] = None,
        quality: int = 100,
        beyond_viewport: bool = False,
        as_base64: bool = False,
    ) -> Optional[str]:
        """捕获当前页面的屏幕截图。

        参数：
            path：截图的文件路径（扩展名决定格式）。
            质量：图像质量 0-100（默认 100）。
            Beyond_viewport：页面会滚动到底部并截图
                包括整个页面
            as_base64：返回为 base64 字符串而不是保存文件。

        返回：
            如果 as_base64=True，则 Base64 屏幕截图数据，否则无。

        加薪：
            InvalidFileExtension：如果不支持文件扩展名。
            MissingScreenshotPath：如果路径为 None 并且 as_base64 为 False。"""
        if not path and not as_base64:
            raise MissingScreenshotPath()

        if path and isinstance(path, str):
            output_extension = path.split('.')[-1]
        elif path and isinstance(path, Path):
            output_extension = path.suffix.lstrip('.')
        else:
            output_extension = ScreenshotFormat.JPEG

        #将 jpg 标准化为 jpeg（CDP 仅接受 jpeg）
        output_extension = (
            output_extension.replace('jpg', 'jpeg')
            if output_extension == 'jpg'
            else output_extension
        )

        if not ScreenshotFormat.has_value(output_extension):
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        output_format = ScreenshotFormat.get_value(output_extension)

        logger.info(
            f'Taking screenshot: path={path}, quality={quality}, '
            f'beyond_viewport={beyond_viewport}, as_base64={as_base64}'
        )
        response: CaptureScreenshotResponse = await self._execute_command(
            PageCommands.capture_screenshot(
                format=output_format,
                quality=quality,
                capture_beyond_viewport=beyond_viewport,
            )
        )

        try:
            screenshot_data = response['result']['data']
        except KeyError:
            raise TopLevelTargetRequired(
                'Command can only be executed on top-level targets. Please use '
                'take_screenshot method on the WebElement object instead.'
            )

        if as_base64:
            logger.info('Screenshot captured and returned as base64')
            return screenshot_data

        if path:
            screenshot_bytes = decode_base64_to_bytes(screenshot_data)
            async with aiofiles.open(str(path), 'wb') as file:
                await file.write(screenshot_bytes)
            logger.info(f'Screenshot saved to: {path}')

        return None

    async def print_to_pdf(
        self,
        path: Optional[str | Path] = None,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        as_base64: bool = False,
    ) -> Optional[str]:
        """生成当前页面的 PDF。

        参数：
            路径：PDF 输出的文件路径。如果 as_base64=False，则为必需。
            横向：使用横向方向。
            display_header_footer：包括页眉/页脚。
            print_background：包括背景图形。
            比例：比例因子 (0.1-2.0)。
            as_base64：作为base64字符串返回而不是保存。

        返回：
            如果 as_base64=True，则 Base64 PDF 数据，否则无。

        加薪：
            ValueError：如果 as_base64=False 时未提供路径。"""
        logger.info(
            f'Generating PDF: path={path}, landscape={landscape}, '
            f'header_footer={display_header_footer}, print_bg={print_background}, '
            f'scale={scale}, as_base64={as_base64}'
        )
        response: PrintToPDFResponse = await self._execute_command(
            PageCommands.print_to_pdf(
                landscape=landscape,
                display_header_footer=display_header_footer,
                print_background=print_background,
                scale=scale,
            )
        )
        pdf_data = response['result']['data']
        if as_base64:
            logger.info('PDF generated and returned as base64')
            return pdf_data

        if path is None:
            raise ValueError('path is required when as_base64=False')

        pdf_bytes = decode_base64_to_bytes(pdf_data)
        async with aiofiles.open(path, 'wb') as file:
            await file.write(pdf_bytes)
        logger.info(f'PDF saved to: {path}')

        return None

    async def save_bundle(self, path: str | Path, inline_assets: bool = False) -> None:
        """将当前页面及其资源保存为 .zip 包以供离线查看。

        捕获页面 HTML 以及 CSS、JS、图像、字体和媒体
        到单个 zip 存档中。该档案包含一个“index.html”
        重写 URL 以引用本地资源文件。

        参数：
            路径：``.zip`` 文件的目标路径。
            inline_assets：为 True 时，将所有资源直接嵌入到
                ``index.html`` 使用数据 URI、``<style>`` 和 ``<script>``
                标签而不是将它们保存为单独的文件。

        加薪：
            InvalidFileExtension：如果路径不以“.zip”结尾。"""
        path = Path(path)
        if path.suffix.lower() != '.zip':
            raise InvalidFileExtension(f'Expected .zip extension, got {path.suffix!r}')

        logger.info(f'Saving page bundle: path={path}, inline={inline_assets}')

        page_was_enabled = self.page_events_enabled
        if not page_was_enabled:
            await self.enable_page_events()

        try:
            tree_response: GetResourceTreeResponse = await self._execute_command(
                PageCommands.get_resource_tree()
            )
            frame_tree: FrameResourceTree = tree_response['result']['frameTree']
            page_url = frame_tree['frame']['url']
            html = await self._fetch_document_html(frame_tree)
            asset_map = await self._fetch_bundle_assets(frame_tree, page_url)

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                if inline_assets:
                    html = inline_all_assets(html, asset_map)
                else:
                    html = rewrite_html_urls(html, asset_map)
                zf.writestr('index.html', html.encode('utf-8'))
                if not inline_assets:
                    for _url, (filename, data, _mime, _rtype) in asset_map.items():
                        zf.writestr(f'assets/{filename}', data)

            async with aiofiles.open(path, 'wb') as f:
                await f.write(buf.getvalue())
            logger.info(f'Page bundle saved to: {path}')
        finally:
            if not page_was_enabled:
                await self.disable_page_events()

    async def _fetch_document_html(self, frame_tree: FrameResourceTree) -> str:
        """从框架树中获取主文档 HTML。"""
        frame_id = frame_tree['frame']['id']
        page_url = frame_tree['frame']['url']
        try:
            doc_response: GetResourceContentResponse = await self._execute_command(
                PageCommands.get_resource_content(frame_id, page_url)
            )
            result = doc_response['result']
            html = result['content']
            if result.get('base64Encoded'):
                html = _b64.b64decode(html).decode('utf-8', errors='replace')
            return html
        except Exception:
            logger.debug('getResourceContent failed for document, falling back to JS')
            response = await self.execute_script('return document.documentElement.outerHTML')
            return cast(str, response['result']['result']['value'])

    async def _fetch_bundle_assets(
        self,
        frame_tree: FrameResourceTree,
        page_url: str,
    ) -> dict[str, tuple[str, bytes, str, ResourceType]]:
        """获取所有可捆绑资源并返回资产地图。"""
        all_resources = collect_frame_resources(frame_tree)
        fetchable = filter_fetchable_resources(all_resources, page_url)

        fetch_tasks: list[Awaitable[GetResourceContentResponse]] = [
            self._execute_command(PageCommands.get_resource_content(fid, res['url']))
            for fid, res in fetchable
        ]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        asset_map: dict[str, tuple[str, bytes, str, ResourceType]] = {}
        for idx, ((_fid, res), result) in enumerate(zip(fetchable, results)):
            if isinstance(result, BaseException):
                logger.warning(f'Failed to fetch resource {res["url"]}: {result}')
                continue
            response: GetResourceContentResponse = result
            content_result = response.get('result')
            if content_result is None:
                logger.warning(f'No result for resource {res["url"]}: {response.get("error")}')
                continue
            raw_content: str = content_result['content']
            is_base64: bool = content_result.get('base64Encoded', False)
            data = _b64.b64decode(raw_content) if is_base64 else raw_content.encode('utf-8')
            filename = build_asset_filename(res['url'], res['mimeType'], idx)
            asset_map[res['url']] = (filename, data, res['mimeType'], res['type'])
        return asset_map

    async def has_dialog(self) -> bool:
        """检查当前是否显示 JavaScript 对话框。

        注意：
            必须启用页面事件才能检测对话框。"""
        if self._connection_handler.dialog:
            logger.debug('Dialog present')
            return True

        return False

    async def get_dialog_message(self) -> str:
        """从当前 JavaScript 对话框获取消息文本。

        加薪：
            NoDialogPresent：如果当前没有显示对话框。"""
        if not await self.has_dialog():
            raise NoDialogPresent()
        message = self._connection_handler.dialog['params']['message']
        logger.debug(f'Dialog message retrieved: {message}')
        return message

    async def handle_dialog(self, accept: bool, prompt_text: Optional[str] = None):
        """响应 JavaScript 对话框。

        参数：
            接受：如果为 True，则接受/确认对话框；如果为 False，则关闭/取消。
            Prompt_text：提示对话框的文本（警报/确认时忽略）。

        加薪：
            NoDialogPresent：如果当前没有显示对话框。

        注意：
            必须启用页面事件才能处理对话框。"""
        if not await self.has_dialog():
            raise NoDialogPresent()
        logger.info(f'Handling dialog: accept={accept}, has_prompt_text={bool(prompt_text)}')
        return await self._execute_command(
            PageCommands.handle_javascript_dialog(accept=accept, prompt_text=prompt_text)
        )

    @overload
    async def execute_script(
        self,
        script: str,
        *,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> EvaluateResponse: ...

    @overload
    async def execute_script(
        self,
        script: str,
        element: WebElement,
        *,
        arguments: Optional[list[CallArgument]] = None,
        silent: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        throw_on_side_effect: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> CallFunctionOnResponse: ...

    async def execute_script(
        self,
        script: str,
        element: Optional[WebElement] = None,
        *,
        arguments: Optional[list[CallArgument]] = None,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> Union[EvaluateResponse, CallFunctionOnResponse]:
        """在页面上下文中执行 JavaScript。

        参数：
            script (str)：要执行的 JavaScript 代码。
            元素（可选[WebElement]）：用于执行脚本的可选 WebElement。
            参数（可选[list[CallArgument]]）：传递给函数的参数。
            object_group（可选[str]）：结果的符号组名称（Runtime.evaluate）。
            include_command_line_api (可选[bool]): 是否包含命令行 API
                （运行时.评估）。
            silent（可选[bool]）：是否静默异常（Runtime.evaluate）。
            context_id（可选[int]）：要评估的执行上下文的 ID
                （运行时.评估）。
            return_by_value (Optional[bool]): 是否按值返回结果而不是
                参考（运行时.评估）。
            generate_preview (Optional[bool]): 是否生成结果预览
                （运行时.评估）。
            user_gesture (Optional[bool]): 是否将评估视为由用户发起
                手势（运行时.评估）。
            wait_promise (Optional[bool]): 是否等待promise结果(Runtime.evaluate)。
            execution_context_id（可选[int]）：调用的执行上下文的ID
                函数在.
            throw_on_side_effect (可选[bool]): 如果无法产生副作用，是否抛出
                排除（Runtime.evaluate）。
            超时（可选[float]）：超时以毫秒为单位（Runtime.evaluate）。
            disable_breaks（可选[bool]）：是否在评估期间禁用断点
                （运行时.评估）。
            repl_mode (可选[bool]): 是否以REPL模式执行(Runtime.evaluate)。
            allow_unsafe_eval_blocked_by_csp（可选[bool]）：允许不安全评估
                （运行时.评估）。
            unique_context_id（可选[str]）：用于评估的唯一上下文ID
                （运行时.评估）。
            Serialization_options（可选[SerializationOptions]）：序列化选项
                结果（运行时.评估）。

        返回：
            Union[EvaluateResponse, CallFunctionOnResponse]：脚本执行的结果。

        加薪：
            InvalidScriptWithElement：如果脚本使用“argument”关键字但未提供元素。

        示例：
            # 执行一个简单的脚本来记录消息
            等待 page.execute_script('console.log("Hello World")')

            # 执行返回页面标题的脚本
            等待 page.execute_script('返回 document.title')

            # 在元素上执行脚本以单击它
            等待 page.execute_script('argument.click()', element)

            # 在元素上执行脚本以设置其值
            等待 page.execute_script('argument.value = "Hello"', element)"""
        logger.debug(f'Executing script: with_element={bool(element)}, length={len(script)}')
        if element is not None:
            warnings.warn(
                'Passing a WebElement to Tab.execute_script() is deprecated. '
                'Use WebElement.execute_script() instead.',
                DeprecationWarning,
                stacklevel=2,
            )

            return await element.execute_script(
                script,
                arguments=arguments,
                silent=silent,
                return_by_value=return_by_value,
                generate_preview=generate_preview,
                user_gesture=user_gesture,
                await_promise=await_promise,
                execution_context_id=execution_context_id,
                object_group=object_group,
                throw_on_side_effect=throw_on_side_effect,
                unique_context_id=unique_context_id,
                serialization_options=serialization_options,
            )

        if has_return_outside_function(script):
            script = f'(function(){{ {script} }})()'

        command = self._get_evaluate_command(
            script,
            object_group=object_group,
            include_command_line_api=include_command_line_api,
            silent=silent,
            context_id=context_id,
            return_by_value=return_by_value,
            generate_preview=generate_preview,
            user_gesture=user_gesture,
            await_promise=await_promise,
            throw_on_side_effect=throw_on_side_effect,
            timeout=timeout,
            disable_breaks=disable_breaks,
            repl_mode=repl_mode,
            allow_unsafe_eval_blocked_by_csp=allow_unsafe_eval_blocked_by_csp,
            unique_context_id=unique_context_id,
            serialization_options=serialization_options,
        )
        logger.debug(f'Executing script without element: length={len(script)}')
        result: Union[EvaluateResponse, CallFunctionOnResponse] = await self._execute_command(
            command
        )
        self._validate_argument_error(result)
        return result

    #TODO：考虑如何删除这些与基类的重复项
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
        logger.debug(f'Continue request on tab: id={request_id}')
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
        logger.debug(f'Fail request on tab: id={request_id}, reason={error_reason}')
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
            f'Fulfill request on tab: id={request_id}, code={response_code}, '
            f'headers_set={bool(response_headers)}, body_set={bool(body)}'
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

    async def continue_with_auth(
        self,
        request_id: str,
        auth_challenge_response: AuthChallengeResponseType,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ):
        """继续暂停的请求以回复身份验证质询。

        当启用 Fetch 时，对于代理身份验证 (407) 或服务器身份验证 (401) 很有用
        与handle_auth = True。"""
        logger.debug(
            f'Continue with auth on tab: id={request_id}, response={auth_challenge_response}, '
            f'user_set={bool(proxy_username)}'
        )
        return await self._execute_command(
            FetchCommands.continue_request_with_auth(
                request_id=request_id,
                auth_challenge_response=auth_challenge_response,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )

    @asynccontextmanager
    async def expect_file_chooser(
        self, files: str | Path | list[str | Path]
    ) -> AsyncGenerator[None, None]:
        """用于自动文件上传处理的上下文管理器。

        参数：
            files：用于上传的文件路径。"""

        async def event_handler(event: FileChooserOpenedEvent):
            logger.info('File chooser opened; setting files')
            file_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]
            await self._execute_command(
                DomCommands.set_file_input_files(
                    files=file_list,
                    backend_node_id=event['params']['backendNodeId'],
                )
            )
            logger.debug(f'Files set on input: {file_list}')

        if self.page_events_enabled is False:
            _before_page_events_enabled = False
            await self.enable_page_events()
        else:
            _before_page_events_enabled = True

        if self.intercept_file_chooser_dialog_enabled is False:
            await self.enable_intercept_file_chooser_dialog()

        logger.info('Waiting for file chooser to open')
        await self.on(
            PageEvent.FILE_CHOOSER_OPENED,
            cast(Callable[[dict], Any], event_handler),
            temporary=True,
        )

        yield

        if self.intercept_file_chooser_dialog_enabled is True:
            await self.disable_intercept_file_chooser_dialog()

        if _before_page_events_enabled is False:
            await self.disable_page_events()

    @asynccontextmanager
    async def expect_and_bypass_cloudflare_captcha(
        self,
        custom_selector: Optional[tuple[By, str]] = None,
        time_before_click: Optional[float] = None,
        time_to_wait_captcha: float = 5,
    ) -> AsyncGenerator[None, None]:
        """自动绕过 Cloudflare 验证码的上下文管理器。

        参数：
            custom_selector：已弃用 — 被忽略。 Cloudflare Turnstile 现已上线
                通过影子根检查自动检测到。
            time_before_click：已弃用 — 已忽略。复选框现在是
                通过影子根轮询定位并立即单击。
            time_to_wait_captcha：验证码检测超时（默认5秒）。"""
        if custom_selector is not None:
            warnings.warn(
                'custom_selector is deprecated and ignored. Cloudflare Turnstile is now '
                'detected automatically via shadow root inspection.',
                DeprecationWarning,
                stacklevel=2,
            )

        if time_before_click is not None:
            warnings.warn(
                'time_before_click is deprecated and ignored. The checkbox is now '
                'located via shadow root polling and clicked immediately.',
                DeprecationWarning,
                stacklevel=2,
            )

        captcha_processed = asyncio.Event()

        async def bypass_cloudflare(_: dict):
            try:
                await self._bypass_cloudflare(
                    _,
                    time_to_wait_captcha=time_to_wait_captcha,
                )
            finally:
                captcha_processed.set()

        _before_page_events_enabled = self.page_events_enabled

        if not _before_page_events_enabled:
            await self.enable_page_events()

        logger.info('Expecting and bypassing Cloudflare captcha if present')
        callback_id = await self.on(PageEvent.LOAD_EVENT_FIRED, bypass_cloudflare)

        try:
            yield
            await captcha_processed.wait()
        finally:
            await self._connection_handler.remove_callback(callback_id)
            if not _before_page_events_enabled:
                await self.disable_page_events()

    @asynccontextmanager
    async def expect_download(
        self,
        keep_file_at: Optional[Union[str, Path]] = None,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[_DownloadHandle, None]:
        """用于处理块内触发的文件下载的上下文管理器。

        行为：
        - 如果提供了 keep_file_at，则配置浏览器以保存到该目录并保留文件。
        - 否则，将使用临时目录并在上下文之后清理。

        参数：
            keep_file_at：保存文件的目录。如果没有，则使用临时
                目录并随后清理它。
            timeout：等待下载完成的最大秒数。默认为 60。

        产量：
            _DownloadHandle：读取下载文件（字节/base64）并检查其路径的句柄。"""
        download_timeout = 60.0 if timeout is None else float(timeout)

        cleanup_dir = False
        if keep_file_at is None:
            download_dir = mkdtemp(prefix='pydoll-download-')
            cleanup_dir = True
        else:
            download_dir = str(Path(keep_file_at))
            Path(download_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f'Expecting download (dir={download_dir}, timeout={download_timeout}s)')
        await self._browser.set_download_behavior(
            behavior=DownloadBehavior.ALLOW,
            download_path=download_dir,
            browser_context_id=self._browser_context_id,
        )

        _page_events_was_enabled = True
        if not self._page_events_enabled:
            _page_events_was_enabled = False
            await self.enable_page_events()

        loop = asyncio.get_event_loop()
        will_begin: asyncio.Future[bool] = loop.create_future()
        done: asyncio.Future[bool] = loop.create_future()
        state: dict[str, Any] = {
            'guid': None,
            'url': None,
            'suggestedFilename': None,
            'filePath': None,
            'dir': download_dir,
        }

        async def on_will_begin(event: DownloadWillBeginEvent):
            params = event['params']
            state['guid'] = params['guid']
            state['url'] = params['url']
            state['suggestedFilename'] = params['suggestedFilename']
            if not will_begin.done():
                will_begin.set_result(True)
            logger.info(
                f'Download will begin: url={state["url"]}, filename={state["suggestedFilename"]}'
            )

        async def on_progress(event: DownloadProgressEvent):
            params = event['params']
            guid = params['guid']
            if (
                state.get('guid')
                and guid != state['guid']
                or params['state'] != DownloadProgressState.COMPLETED
            ):
                return
            file_path = params.get('filePath')
            if not file_path:
                file_path = str(Path(download_dir) / state['suggestedFilename'])
            state['filePath'] = file_path
            if not done.done():
                done.set_result(True)
            logger.info(f'Download completed: {file_path}')

        await self.on(
            PageEvent.DOWNLOAD_WILL_BEGIN,
            cast(Callable[[dict], Awaitable[Any]], on_will_begin),
            True,
        )
        cb_id_progress = await self.on(
            PageEvent.DOWNLOAD_PROGRESS,
            cast(Callable[[dict], Awaitable[Any]], on_progress),
            False,
        )

        handle = _DownloadHandle(
            state=state,
            will_begin_future=will_begin,
            done_future=done,
            timeout=download_timeout,
        )

        try:
            yield handle
            try:
                await asyncio.wait_for(done, timeout=download_timeout)
            except asyncio.TimeoutError as exc:
                raise DownloadTimeout() from exc
        finally:
            await self._cleanup_download_context(
                cb_id_progress,
                _page_events_was_enabled,
                cleanup_dir,
                state,
                download_dir,
            )

    async def _cleanup_download_context(
        self,
        cb_id_progress: int,
        page_events_was_enabled: bool,
        cleanup_dir: bool,
        state: dict[str, Any],
        download_dir: str,
    ) -> None:
        await self.remove_callback(cb_id_progress)
        await self._browser.set_download_behavior(
            behavior=DownloadBehavior.DEFAULT,
            browser_context_id=self._browser_context_id,
        )

        if cleanup_dir:
            file_path = state['filePath']
            if not file_path:
                return
            Path(file_path).unlink(missing_ok=True)
            shutil.rmtree(download_dir, ignore_errors=True)

        if not page_events_was_enabled:
            await self.disable_page_events()

    @overload
    async def on(
        self, event_name: str, callback: Callable[[dict], Any], temporary: bool = False
    ) -> int: ...
    @overload
    async def on(
        self, event_name: str, callback: Callable[[dict], Awaitable[Any]], temporary: bool = False
    ) -> int: ...
    async def on(
        self,
        event_name,
        callback,
        temporary=False,
    ) -> int:
        """注册 CDP 事件监听器。

        回调在后台任务中运行以防止阻塞。

        参数：
            event_name：CDP 事件名称（例如“Page.loadEventFired”）。
            回调：事件调用的函数（同步或异步）。
            临时：第一次调用后删除。

        返回：
            用于删除的回调 ID。

        注意：
            在事件触发之前必须启用相应的域。"""

        async def callback_wrapper(event):
            asyncio.create_task(callback(event))

        if asyncio.iscoroutinefunction(callback):
            function_to_register = callback_wrapper
        else:
            function_to_register = callback

        logger.debug(
            f'Registering callback on tab: event={event_name}, temporary={temporary}, '
            f'async={asyncio.iscoroutinefunction(callback)}'
        )
        return await self._connection_handler.register_callback(
            event_name, function_to_register, temporary
        )

    async def remove_callback(self, callback_id: int):
        """从选项卡中删除回调。"""
        logger.debug(f'Removing callback from tab: id={callback_id}')
        return await self._connection_handler.remove_callback(callback_id)

    async def clear_callbacks(self):
        """清除所有已注册的事件回调。"""
        logger.debug('Clearing all callbacks from tab')
        await self._connection_handler.clear_callbacks()

    def _get_connection_handler(self) -> ConnectionHandler:
        if self._ws_address:
            logger.debug('Using WebSocket address for connection handler')
            return ConnectionHandler(ws_address=self._ws_address)
        logger.debug(
            'Using port/target for connection handler: '
            f'port={self._connection_port}, target_id={self._target_id}'
        )
        return ConnectionHandler(self._connection_port, self._target_id)

    @staticmethod
    def _get_evaluate_command(
        script: str,
        *,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ):
        """使用给定参数创建评估命令。"""
        return RuntimeCommands.evaluate(
            expression=script,
            object_group=object_group,
            include_command_line_api=include_command_line_api,
            silent=silent,
            context_id=context_id,
            return_by_value=return_by_value,
            generate_preview=generate_preview,
            user_gesture=user_gesture,
            await_promise=await_promise,
            throw_on_side_effect=throw_on_side_effect,
            timeout=timeout,
            disable_breaks=disable_breaks,
            repl_mode=repl_mode,
            allow_unsafe_eval_blocked_by_csp=allow_unsafe_eval_blocked_by_csp,
            unique_context_id=unique_context_id,
            serialization_options=serialization_options,
        )

    @staticmethod
    def _validate_argument_error(response: EvaluateResponse) -> None:
        """验证脚本未因有关“参数”未定义的 ReferenceError 而失败。

        加薪：
            InvalidScriptWithElement：如果脚本使用“argument”关键字但未提供元素。"""
        evaluate_result = response.get('result')
        if not isinstance(evaluate_result, dict):
            return

        remote_object = evaluate_result.get('result')
        if not isinstance(remote_object, dict):
            return

        if not (
            remote_object.get('type') == 'object'
            and remote_object.get('subtype') == 'error'
            and remote_object.get('className') == 'ReferenceError'
        ):
            return

        description = remote_object.get('description', '')
        if 'argument is not defined' in description:
            raise InvalidScriptWithElement('Script contains "argument" but no element was provided')

    _PAGE_LOAD_EVENT_MAP = {
        PageLoadState.INTERACTIVE: PageEvent.DOM_CONTENT_EVENT_FIRED,
        PageLoadState.COMPLETE: PageEvent.LOAD_EVENT_FIRED,
    }

    @asynccontextmanager
    async def _wait_page_load(self, timeout: int = 300):
        """使用 CDP 事件等待页面达到配置的加载状态。

        **在**产生之前注册 CDP 事件侦听器，以便导航
        命令可以在“async with”块内发出，无需竞争
        条件。  这取代了以前的“document.readyState”轮询
        循环，消除了页面期间对“Runtime.evaluate”的依赖
        负载和内部命令超时的风险。

        使用的 CDP 事件取决于“browser.options.page_load_state”：

        * ``INTERACTIVE`` — 等待``Page.domContentEventFired``。
        *“COMPLETE”——等待“Page.loadEventFired”。

        参数：
            timeout：等待目标加载状态的最大秒数。

        加薪：
            PageLoadTimeout：如果页面没有及时达到目标状态。"""
        target_state = self._browser.options.page_load_state

        page_loaded = asyncio.Event()
        event_name = self._PAGE_LOAD_EVENT_MAP[target_state]
        cleanup_page_events = not self._page_events_enabled

        if cleanup_page_events:
            await self.enable_page_events()

        def on_loaded(_: dict):
            page_loaded.set()

        callback_id = await self.on(event_name, on_loaded)
        logger.debug(f'Waiting for page load via {event_name} (timeout={timeout}s)')

        try:
            yield
            await asyncio.wait_for(page_loaded.wait(), timeout=timeout)
            logger.debug(f'Page load event received: {event_name}')
        except asyncio.TimeoutError:
            logger.error(f'Page load timeout after {timeout}s waiting for {event_name}')
            raise PageLoadTimeout()
        finally:
            with contextlib.suppress(Exception):
                await self.remove_callback(callback_id)
            if cleanup_page_events:
                with contextlib.suppress(Exception):
                    await self.disable_page_events()

    async def _find_cloudflare_shadow_root(self, timeout: float) -> ShadowRoot:
        """轮询 Cloudflare Turnstile 影子根。

        重复调用“find_shadow_roots(deep=False)”并检查每个
        Cloudflare 挑战域的shadow root ``inner_html``。

        参数：
            timeout：等待影子根的最大秒数。

        返回：
            其内部 HTML 包含的第一个 ShadowRoot
            “challenges.cloudflare.com”。

        加薪：
            WaitElementTimeout：如果在时间内没有找到匹配的影子根
                *超时*秒。"""
        start_time = asyncio.get_event_loop().time()
        while True:
            shadow_roots = await self.find_shadow_roots(deep=False)
            for sr in shadow_roots:
                html = await sr.inner_html
                if _CLOUDFLARE_CHALLENGE_DOMAIN in html:
                    return sr

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'超时:{timeout}s waiting for Cloudflare Turnstile shadow root'
                )
            await asyncio.sleep(0.5)

    async def _bypass_cloudflare(
        self,
        event: dict,
        time_to_wait_captcha: float = 5,
    ) -> None:
        """尝试通过影子根遍历绕过 Cloudflare Turnstile 验证码。

        遍历影子根以找到 Cloudflare iframe，导航到
        它，然后单击实际的复选框元素（``span.cb-i``）。"""
        try:
            timeout_int = int(time_to_wait_captcha)
            shadow_root = await self._find_cloudflare_shadow_root(
                timeout=time_to_wait_captcha
            )
            iframe = await shadow_root.query(_CLOUDFLARE_IFRAME_SELECTOR, timeout=timeout_int)
            body = await iframe.find(tag_name='body', timeout=timeout_int)
            inner_shadow = await body.get_shadow_root(timeout=time_to_wait_captcha)
            checkbox = await inner_shadow.query(_CLOUDFLARE_CHECKBOX_SELECTOR, timeout=timeout_int)
            await checkbox.click()
        except Exception as exc:
            logger.error(f'cloudflare验证错误: {exc}')

    async def cf(self,time_to_wait_captcha: float = 5) -> None:
        await self._bypass_cloudflare(event=None, time_to_wait_captcha=time_to_wait_captcha)


class _DownloadHandle:
    """由expect_download返回的句柄来访问下载的文件。"""

    def __init__(
        self,
        state: dict[str, Any],
        will_begin_future: asyncio.Future[bool],
        done_future: asyncio.Future[bool],
        timeout: float,
    ) -> None:
        self._state = state
        self._will_begin_future = will_begin_future
        self._done_future = done_future
        self._timeout = timeout

    @property
    def file_path(self) -> Optional[str]:
        return self._state.get('filePath')

    async def wait_started(self, timeout: Optional[float] = None) -> None:
        await asyncio.wait_for(self._will_begin_future, timeout=timeout or self._timeout)

    async def wait_finished(self, timeout: Optional[float] = None) -> None:
        await asyncio.wait_for(self._done_future, timeout=timeout or self._timeout)

    async def read_bytes(self) -> bytes:
        await self.wait_finished()
        if not self.file_path:
            raise FileNotFoundError('Download file path not available')
        async with aiofiles.open(self.file_path, 'rb') as f:  #类型：忽略[arg-type]
            return await f.read()

    async def read_base64(self) -> str:
        data = await self.read_bytes()
        return _b64.b64encode(data).decode('ascii')
