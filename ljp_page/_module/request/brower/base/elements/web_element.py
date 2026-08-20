from __future__ import annotations

import asyncio
import json
from ljp_page.logger import loguru_logger
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import aiofiles
__all__ = ['WebElement']
from ..commands import (
    DomCommands,
    InputCommands,
    PageCommands,
    RuntimeCommands,
)
from ..connection import ConnectionHandler
from ljp_page._module.request.brower.pydoll.constants import (
    Key,
    Scripts,
)
from .mixins import FindElementsMixin
from ljp_page._module.request.brower.pydoll.elements.shadow_root import ShadowRoot
from ljp_page._module.request.brower.pydoll.exceptions import (
    ElementNotAFileInput,
    ElementNotFound,
    ElementNotInteractable,
    ElementNotVisible,
    InvalidFileExtension,
    InvalidIFrame,
    MissingScreenshotPath,
    ShadowRootNotFound,
    WaitElementTimeout,
)
from ljp_page._module.request.brower.pydoll.interactions.iframe import IFrameContext, IFrameContextResolver
from ljp_page._module.request.brower.pydoll.interactions.keyboard import Keyboard
from ..protocol.dom.types import ShadowRootType
from ljp_page._module.request.brower.base.protocol.input.types import (
    KeyEventType,
    KeyModifier,
    MouseButton,
    MouseEventType,
)
from ljp_page._module.request.brower.base.protocol.page.types import ScreenshotFormat, Viewport
from ljp_page._module.request.brower.base.protocol.runtime.methods import (
    CallFunctionOnResponse,
    EvaluateResponse,
    SerializationOptions,
)
from ljp_page._module.request.brower.base.protocol.runtime.types import CallArgument
from ljp_page._module.request.brower.pydoll.utils import (



    decode_base64_to_bytes,
    extract_text_from_html,
    is_script_already_function,
)

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.interactions.mouse import Mouse as MouseType
    from ljp_page._module.request.brower.base.protocol.dom.methods import (
        DescribeNodeResponse,
        GetBoxModelResponse,
        GetOuterHTMLResponse,
        ResolveNodeResponse,
    )
    from ljp_page._module.request.brower.base.protocol.dom.types import Quad
    from ljp_page._module.request.brower.base.protocol.page.methods import CaptureScreenshotResponse
    from ljp_page._module.request.brower.base.protocol.runtime.methods import GetPropertiesResponse




class WebElement(FindElementsMixin):  #编号：PLR0904
    """用于浏览器自动化的 DOM 元素包装器。

    提供元素交互、检查、
    以及使用 Chrome DevTools 协议命令进行操作。"""

    if TYPE_CHECKING:
        _routing_session_handler: Optional[ConnectionHandler]
        _routing_session_id: Optional[str]
        _routing_parent_frame_id: Optional[str]

    def __init__(
        self,
        object_id: str,
        connection_handler: ConnectionHandler,
        method: Optional[str] = None,
        selector: Optional[str] = None,
        attributes_list: list[str] = [],
        mouse: Optional['MouseType'] = None,
    ):
        """初始化 WebElement 包装器。

        参数：
            object_id：此 DOM 元素的唯一 CDP 对象标识符。
            connection_handler：浏览器通信的连接实例。
            method：用于查找该元素的搜索方法（用于调试）。
            选择器：用于查找此元素的选择器字符串（用于调试）。
            attribute_list：交替属性名称和值的平面列表。
            mouse：可选的 Mouse 实例，用于人性化的点击行为。

        注意：
            鼠标和键盘遵循不同的所有权策略。鼠标是共享的
            来自 Tab 的实例，向下传递到元素以保留光标位置状态
            跨互动。它通过 Tab._execute_command 调度命令，其中
            意味着它没有 iframe 上下文感知。键盘是按元素创建的，
            通过元素自己的 _execute_command 路由命令，正确处理
            iframe 路由。对于 iframe 元素，鼠标在执行过程中会被故意跳过
            人性化的点击（请参阅 click()）以避免将事件分派到错误的框架。"""
        self._object_id = object_id
        self._search_method = method
        self._selector = selector
        self._connection_handler = connection_handler
        self._attributes: dict[str, str] = {}
        self._keyboard: Optional[Keyboard] = None
        self._mouse = mouse
        self._iframe_context: Optional[IFrameContext] = None
        self._iframe_resolver: Optional[IFrameContextResolver] = None
        self._def_attributes(attributes_list)
        loguru_logger.debug(
            f'WebElement initialized: object_id={self._object_id}, '
            f'method={self._search_method}, selector={self._selector}, '
            f'attributes={len(self._attributes)}'
        )

    def _get_keyboard(self) -> Keyboard:
        """获取或创建键盘控制器。"""
        if self._keyboard is None:
            self._keyboard = Keyboard(self)
        return self._keyboard

    def _get_iframe_resolver(self) -> IFrameContextResolver:
        """获取或创建 iframe 上下文解析器。"""
        if self._iframe_resolver is None:
            self._iframe_resolver = IFrameContextResolver(self)
        return self._iframe_resolver

    @property
    def attributes(self) -> dict[str, str]:
        """元素的缓存属性的只读副本。"""
        return dict(self._attributes)

    @property
    def value(self) -> Optional[str]:
        """元素的 value 属性（对于表单元素）。"""
        return self._attributes.get('value')

    @property
    def class_name(self) -> Optional[str]:
        """元素的 CSS 类名称。"""
        return self._attributes.get('class_name')

    @property
    def id(self) -> Optional[str]:
        """元素的 ID 属性。"""
        return self._attributes.get('id')

    @property
    def tag_name(self) -> Optional[str]:
        """元素的 HTML 标签名称。"""
        return self._attributes.get('tag_name')

    @property
    def is_iframe(self) -> bool:
        """该元素是否代表 iframe。"""
        return self.tag_name in {'iframe', 'frame'}

    @property
    def is_enabled(self) -> bool:
        """元素是否启用（未禁用）。"""
        return bool('disabled' not in self._attributes.keys())

    @property
    async def text(self) -> str:
        """元素的可见文本内容。"""
        if self._is_inside_iframe():
            response: CallFunctionOnResponse = await self.execute_script(
                'return (this.textContent || "").trim()', return_by_value=True
            )
            text_value = response.get('result', {}).get('result', {}).get('value', '') or ''
            loguru_logger.debug(f'Extracted text length (iframe ctx): {len(text_value)}')
            return text_value

        outer_html = await self.inner_html
        text_value = extract_text_from_html(outer_html, strip=True)
        loguru_logger.debug(f'Extracted text length: {len(text_value)}')
        return text_value

    @property
    async def bounds(self) -> Quad:
        """元素的边界框坐标。

        返回相对于文档原点的 CSS 像素坐标。"""
        command = DomCommands.get_box_model(object_id=self._object_id)
        response: GetBoxModelResponse = await self._execute_command(command)
        content = response['result']['model']['content']
        loguru_logger.debug(f'Bounds retrieved (points={len(content)})')
        return content

    @property
    async def inner_html(self) -> str:
        if self.is_iframe:
            return await self._get_iframe_inner_html()

        if self._is_inside_iframe():
            response: CallFunctionOnResponse = await self.execute_script(
                'return this.outerHTML', return_by_value=True
            )
            return response.get('result', {}).get('result', {}).get('value', '')

        command = DomCommands.get_outer_html(object_id=self._object_id)
        response_get_outer_html: GetOuterHTMLResponse = await self._execute_command(command)
        return response_get_outer_html['result']['outerHTML']

    @property
    async def iframe_context(self) -> Optional[IFrameContext]:
        """当此元素是 <iframe> 时，返回已解析的 iframe 上下文。

        上下文包括：frame_id、document_url、execution_context_id、
        document_object_id，对于 OOPIF 目标，session_id 和
        session_handler 用于路由命令。上下文总是新鲜的
        解决了 iframe 导航后避免过时的执行上下文或
        重新加载。非 iframe 元素返回 None。

        返回：
            IFrameContext | None：已解析 iframe 上下文，或者对于非 iframe 为 None。"""
        if not self.is_iframe:
            return None

        resolver = self._get_iframe_resolver()
        self._iframe_context = await resolver.resolve()
        self._apply_routing_from_context()
        return self._iframe_context

    def get_attribute(self, name: str) -> Optional[str]:
        """获取元素属性值。

        注意：
            仅提供找到元素后可用的属性。
            对于动态属性，请考虑使用 JavaScript 执行。"""
        if name == 'class' and 'class_name' in self._attributes:
            return self._attributes.get('class_name')
        return self._attributes.get(name)

    async def get_bounds_using_js(self) -> dict[str, int]:
        """使用 JavaScript getBoundingClientRect() 获取元素边界。

        返回相对于视口的坐标（替代bounds属性）。"""
        response = await self.execute_script(Scripts.BOUNDS, return_by_value=True)
        bounds = json.loads(response['result']['result']['value'])
        loguru_logger.debug(f'Bounds via JS: {bounds}')
        return bounds

    async def get_parent_element(self) -> WebElement:
        """元素的父元素。"""
        loguru_logger.debug(f'Getting parent element for object_id={self._object_id}')
        result = await self.execute_script(Scripts.GET_PARENT_NODE)
        if not self._has_object_id_key(result):
            raise ElementNotFound(f'Parent element not found for element: {self}')

        object_id = result['result']['result']['objectId']
        attributes = await self._get_object_attributes(object_id=object_id)
        loguru_logger.debug(f'Parent element resolved: object_id={object_id}')
        return WebElement(
            object_id, self._connection_handler, attributes_list=attributes, mouse=self._mouse
        )

    async def get_shadow_root(self, timeout: float = 0) -> ShadowRoot:
        """获取附加到该元素的影子根。

        参数：
            timeout：等待影子根出现的最大秒数。
                当 > 0 时，重复轮询（每 0.5 秒）直到出现影子根
                被发现或超时。

        返回：
            用于遍历 Shadow DOM 的 ShadowRoot 实例。

        加薪：
            ShadowRootNotFound：如果没有附加影子根（当超时 = 0 时）。
            WaitElementTimeout：如果超时> 0并且没有出现影子根
                在规定的期限内。"""
        if not timeout:
            return await self._get_shadow_root()

        start_time = asyncio.get_event_loop().time()
        while True:
            try:
                return await self._get_shadow_root()
            except ShadowRootNotFound:
                pass

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise WaitElementTimeout(
                    f'超时{timeout}s 等待影子根元素'
                )

            await asyncio.sleep(0.5)

    async def _get_shadow_root(self) -> ShadowRoot:
        """获取附加到该元素的影子根（单次尝试）。"""
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=self._object_id, depth=1, pierce=True)
        )
        node_info = response.get('result', {}).get('node', {})
        shadow_roots = node_info.get('shadowRoots', [])
        if not shadow_roots:
            raise ShadowRootNotFound()

        shadow_root_data = shadow_roots[0]
        backend_node_id = shadow_root_data.get('backendNodeId')
        if not backend_node_id:
            raise ShadowRootNotFound('Shadow root found but backend node ID is unavailable')

        resolve_response: ResolveNodeResponse = await self._execute_command(
            DomCommands.resolve_node(backend_node_id=backend_node_id)
        )
        shadow_object_id = resolve_response['result']['object']['objectId']

        mode = ShadowRootType(shadow_root_data.get('shadowRootType', 'open'))

        loguru_logger.debug(f'Shadow root resolved: object_id={shadow_object_id}, mode={mode.value}')
        return ShadowRoot(
            object_id=shadow_object_id,
            connection_handler=self._connection_handler,
            mode=mode,
            host_element=self,
        )

    async def get_children_elements(
        self, max_depth: int = 1, tag_filter: list[str] = [], raise_exc: bool = False
    ) -> list[WebElement]:
        """检索该元素的所有直接和嵌套子元素。

        参数：
            max_深度（int，可选）：查找子项时要遍历的最大深度。
                仅直接子级默认为 1。
            tag_filter（list[str]，可选）：用于过滤结果的 HTML 标记名称列表。
                如果为空，则返回所有子元素，无论标签如何。默认为[]。

        返回：
            list[WebElement]：在指定范围内找到的子 WebElement 对象的列表
                深度和匹配标签过滤条件。

        加薪：
            ElementNotFound：如果没有找到该元素的子元素并且 raise_exc 为 True。"""
        loguru_logger.debug(
            f'Getting children: max_depth={max_depth}, '
            f'tag_filter={tag_filter}, raise_exc={raise_exc}'
        )
        children = await self._get_family_elements(
            script=Scripts.GET_CHILDREN_NODE, max_depth=max_depth, tag_filter=tag_filter
        )
        if not children and raise_exc:
            raise ElementNotFound(f'Child element not found for element: {self}')
        loguru_logger.debug(f'Children found: {len(children)}')
        return children

    async def get_siblings_elements(
        self, tag_filter: list[str] = [], raise_exc: bool = False
    ) -> list[WebElement]:
        """检索该元素的所有同级元素（同一 DOM 级别的元素）。

        参数：
            tag_filter（list[str]，可选）：用于过滤结果的 HTML 标记名称列表。
                如果为空，则返回所有同级元素，无论标签如何。默认为[]。

        返回：
            list[WebElement]：共享相同内容的同级 WebElement 对象列表
                父元素作为此元素并匹配标签过滤条件。

        加薪：
            ElementNotFound：如果没有找到该元素的同级元素
            并且 raise_exc 为 True。"""
        loguru_logger.debug(f'Getting siblings: tag_filter={tag_filter}, raise_exc={raise_exc}')
        siblings = await self._get_family_elements(
            script=Scripts.GET_SIBLINGS_NODE, tag_filter=tag_filter
        )
        if not siblings and raise_exc:
            raise ElementNotFound(f'Sibling element not found for element: {self}')
        loguru_logger.debug(f'Siblings found: {len(siblings)}')
        return siblings

    async def take_screenshot(
        self,
        path: Optional[str | Path] = None,
        quality: int = 100,
        as_base64: bool = False,
    ) -> Optional[str]:
        """仅捕获此元素的屏幕截图。

        在捕获之前自动将元素滚动到视图中。

        参数：
            path：截图的文件路径（扩展名决定格式）。
            质量：图像质量 0-100（默认 100）。
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
        if output_extension == 'jpg':
            output_extension = 'jpeg'

        if not ScreenshotFormat.has_value(output_extension):
            raise InvalidFileExtension(f'{output_extension} extension is not supported.')

        file_format = ScreenshotFormat.get_value(output_extension)

        bounds = await self.get_bounds_using_js()
        clip = Viewport(
            x=bounds['x'],
            y=bounds['y'],
            width=bounds['width'],
            height=bounds['height'],
            scale=1,
        )
        loguru_logger.debug(
            f'Taking element screenshot: path={path}, quality={quality}, as_base64={as_base64}, '
            f'clip={{x: {clip["x"]}, y: {clip["y"]}, w: {clip["width"]}, h: {clip["height"]}}}'
        )

        screenshot: CaptureScreenshotResponse = await self._connection_handler.execute_command(
            PageCommands.capture_screenshot(format=file_format, clip=clip, quality=quality)
        )

        screenshot_data = screenshot['result']['data']

        if as_base64:
            loguru_logger.info('Element screenshot captured and returned as base64')
            return screenshot_data

        if path:
            image_bytes = decode_base64_to_bytes(screenshot_data)
            async with aiofiles.open(str(path), 'wb') as file:
                await file.write(image_bytes)
            loguru_logger.info(f'Element screenshot saved: {path}')

        return None

    async def scroll_into_view(self):
        """将元素滚动到可见视口中。"""
        command = DomCommands.scroll_into_view_if_needed(object_id=self._object_id)
        loguru_logger.info(f'Scrolling element into view: object_id={self._object_id}')
        await self._execute_command(command)

    async def wait_until(
        self,
        *,
        is_visible: bool = False,
        is_interactable: bool = False,
        timeout: int = 0,
    ):
        """等待元素满足指定条件。

        加薪：
            ValueError：如果“is_visible”和“is_interactable”都不为 True。
            WaitElementTimeout：如果在“超时”内未满足条件。"""
        checks_map = [
            (is_visible, self.is_visible),
            (is_interactable, self.is_interactable),
        ]
        checks = [func for flag, func in checks_map if flag]
        if not checks:
            raise ValueError('At least one of is_visible or is_interactable must be True')

        condition_parts = []
        if is_visible:
            condition_parts.append('visible')
        if is_interactable:
            condition_parts.append('interactable')
        condition_msg = ' and '.join(condition_parts)

        loguru_logger.info(
            f'Waiting for element: visible={is_visible}, '
            f'interactable={is_interactable}, timeout={timeout}s'
        )
        loop = asyncio.get_event_loop()
        start_time = loop.time()
        while True:
            results = await asyncio.gather(*(check() for check in checks))
            if all(results):
                loguru_logger.info(f'Element condition satisfied: {condition_msg}')
                return

            if timeout and loop.time() - start_time > timeout:
                loguru_logger.error(f'Timeout waiting for element to become {condition_msg}')
                raise WaitElementTimeout(f'Timed out waiting for element to become {condition_msg}')

            await asyncio.sleep(0.5)

    async def click_using_js(self):
        """使用 JavaScript click() 方法单击元素。

        加薪：
            ElementNotVisible：如果元素不可见。
            ElementNotInteractable：如果无法单击元素。

        注意：
            对于 <option> 元素，使用专门的选择方法。
            元素会自动滚动到视图中。"""
        if await self._is_option_element():
            return await self._click_option_tag()

        await self.scroll_into_view()

        if not await self.is_visible():
            raise ElementNotVisible()

        loguru_logger.info(f'Clicking element via JS: object_id={self._object_id}')
        result = await self.execute_script(Scripts.CLICK, return_by_value=True)
        clicked = result['result']['result']['value']
        if not clicked:
            raise ElementNotInteractable()

    async def click(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        hold_time: float = 0.1,
        humanize: bool = False,
    ):
        """使用模拟鼠标事件单击元素。

        参数：
            x_offset：距元素中心的水平偏移。
            y_offset：距元素中心的垂直偏移。
            hold_time：按住鼠标按钮的持续时间（当 humanize=False 时使用）。
            humanize：当 True 且 Mouse 实例可用时，使用人性化
                贝塞尔曲线从当前跟踪位置移动到
                单击之前的元素中心。当为 False 时，调度原始 CDP
                直接 mousePressed/mouseReleased 事件。

        加薪：
            ElementNotVisible：如果元素不可见。

        注意：
            对于 <option> 元素，委托专门的 JavaScript 方法。
            元素会自动滚动到视图中。"""
        if await self._is_option_element():
            return await self._click_option_tag()

        if not await self.is_visible():
            raise ElementNotVisible()

        await self.scroll_into_view()

        try:
            element_bounds = await self.bounds
            position_to_click = self._calculate_center(element_bounds)
            position_to_click = (
                position_to_click[0] + x_offset,
                position_to_click[1] + y_offset,
            )
        except KeyError:
            element_bounds_js = await self.get_bounds_using_js()
            position_to_click = (
                element_bounds_js['x'] + element_bounds_js['width'] / 2 + x_offset,
                element_bounds_js['y'] + element_bounds_js['height'] / 2 + y_offset,
            )

        has_iframe_context = getattr(self, '_iframe_context', None) is not None
        if humanize and self._mouse is not None and not has_iframe_context:
            loguru_logger.info(
                f'Clicking element (humanized): x={position_to_click[0]}, y={position_to_click[1]}'
            )
            await self._mouse.click(position_to_click[0], position_to_click[1])
            return

        loguru_logger.info(
            f'Clicking element: x={position_to_click[0]}, '
            f'y={position_to_click[1]}, hold={hold_time}s'
        )
        press_command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_PRESSED,
            x=int(position_to_click[0]),
            y=int(position_to_click[1]),
            button=MouseButton.LEFT,
            click_count=1,
        )
        release_command = InputCommands.dispatch_mouse_event(
            type=MouseEventType.MOUSE_RELEASED,
            x=int(position_to_click[0]),
            y=int(position_to_click[1]),
            button=MouseButton.LEFT,
            click_count=1,
        )
        await self._execute_command(press_command)
        await asyncio.sleep(hold_time)
        await self._execute_command(release_command)

    async def focus(self):
        """通过 CDP DOM.focus 命令聚焦此元素。"""
        await self._execute_command(DomCommands.focus(object_id=self._object_id))

    async def clear(self):
        """清除元素的当前值。

        支持标准输入、文本区域和内容可编辑元素。
        调度“input”和“change”事件，以便框架检测更新。

        加薪：
            ElementNotInteractable：如果元素不接受文本输入。"""
        loguru_logger.info('Clearing element value')
        result = await self.execute_script(Scripts.CLEAR_INPUT, return_by_value=True)
        success = result['result'].get('result', {}).get('value', False)
        if not success:
            loguru_logger.error('Element does not accept text input')
            raise ElementNotInteractable('Element does not accept text input')
        if self._attributes.get('tag_name', '').lower() in {'input', 'textarea'}:
            self._attributes['value'] = ''

    async def insert_text(self, text: str):
        """使用 JavaScript 将文本插入到元素中。

        支持标准输入、文本区域、内容可编辑元素和富文本编辑器。
        在光标位置插入文本或替换选定的文本。

        参数：
            文本：要插入的文本。

        加薪：
            ElementNotInteractable：如果元素不接受文本输入。

        注意：
            使用 JavaScript 来最大程度地兼容所有输入类型。
            自动处理输入/文本区域和内容可编辑元素。"""
        loguru_logger.info(f'Inserting text (length={len(text)})')
        result = await self.execute_script(
            Scripts.INSERT_TEXT, return_by_value=True, arguments=[CallArgument(value=text)]
        )
        loguru_logger.debug(f'Insert text result: {result}')
        success = result['result'].get('result', {}).get('value', False)

        if not success:
            loguru_logger.error('Element does not accept text input')
            raise ElementNotInteractable('Element does not accept text input')
        #在常见情况下保持缓存属性一致（例如输入值）
        #这可以避免为简单断言强制进行 DOM 往返。
        if self._attributes.get('tag_name', '').lower() in {'input', 'textarea'}:
            #插入空字段时，结果值等于插入的文本。
            #对于复杂的情况（带插入符号的非空），测试通常检查非空。
            self._attributes['value'] = text

    async def set_input_files(self, files: str | Path | list[str | Path]):
        """设置文件输入元素的文件路径。

        参数：
            files：现有文件的绝对文件路径列表。

        加薪：
            ElementNotAFileInput：如果元素不是文件输入。"""
        if (
            self._attributes.get('tag_name', '').lower() != 'input'
            or self._attributes.get('type', '').lower() != 'file'
        ):
            raise ElementNotAFileInput()
        files_list = [str(file) for file in files] if isinstance(files, list) else [str(files)]
        loguru_logger.info(f'Setting input files: count={len(files_list)}')
        await self._execute_command(
            DomCommands.set_file_input_files(files=files_list, object_id=self._object_id)
        )

    async def type_text(
        self,
        text: str,
        humanize: bool = False,
        interval: Optional[float] = None,
    ):
        """逐个字符地键入文本。

        参数：
            text：要输入到元素中的文本。
            humanize：当为 True 时，模拟类似人类的打字。
            间隔：已弃用。使用 humanize=True 代替。"""
        loguru_logger.info(f'Typing text (length={len(text)}, humanize={humanize})')
        await self.click(humanize=humanize)
        keyboard = self._get_keyboard()
        await keyboard.type_text(text, humanize=humanize, interval=interval)

    async def key_down(self, key: Key, modifiers: Optional[KeyModifier] = None):
        """发送按键按下事件。

        .. 已弃用::
            此方法已被弃用。使用“tab.keyboard.down()”代替。

        注意：
            仅发送按键按下而不释放。与 key_up() 配对以实现完整的按键操作。"""
        warnings.warn(
            'WebElement.key_down() is deprecated. '
            'Use tab.keyboard API instead: await tab.keyboard.down(key, modifiers)',
            DeprecationWarning,
            stacklevel=2,
        )
        key_name, code = key
        loguru_logger.info(f'Key down: key={key_name} code={code} modifiers={modifiers}')
        await self._execute_command(
            InputCommands.dispatch_key_event(
                type=KeyEventType.KEY_DOWN,
                key=key_name,
                windows_virtual_key_code=code,
                native_virtual_key_code=code,
                modifiers=modifiers,
            )
        )

    async def key_up(self, key: Key):
        """发送 key up 事件（应遵循相应的 key_down()）。

        .. 已弃用::
            此方法已被弃用。使用“tab.keyboard.up()”代替。"""
        warnings.warn(
            'WebElement.key_up() is deprecated. '
            'Use tab.keyboard API instead: await tab.keyboard.up(key)',
            DeprecationWarning,
            stacklevel=2,
        )
        key_name, code = key
        loguru_logger.info(f'Key up: key={key_name} code={code}')
        await self._execute_command(
            InputCommands.dispatch_key_event(
                type=KeyEventType.KEY_UP,
                key=key_name,
                windows_virtual_key_code=code,
                native_virtual_key_code=code,
            )
        )

    async def press_keyboard_key(
        self,
        key: Key,
        modifiers: Optional[KeyModifier] = None,
        interval: float = 0.1,
    ):
        """按可配置的时间按下并释放键盘按键。

        .. 已弃用::
            此方法已被弃用。使用“tab.keyboard.press()”代替。

        对于特殊键（Enter、Tab 等）比 type_text() 更好。"""
        warnings.warn(
            'WebElement.press_keyboard_key() is deprecated. '
            'Use tab.keyboard API instead: await tab.keyboard.press(key, modifiers, interval)',
            DeprecationWarning,
            stacklevel=2,
        )
        await self.key_down(key, modifiers)
        await asyncio.sleep(interval)
        await self.key_up(key)

    async def is_editable(self) -> bool:
        """检查元素是否可以接受文本输入。

        返回：
            如果元素可编辑（输入、文本区域或内容可编辑），则为 True。"""
        result = await self.execute_script(Scripts.IS_EDITABLE, return_by_value=True)
        is_editable = result['result']['result']['value']
        loguru_logger.debug(f'Element editable check: {is_editable}')
        return is_editable

    async def is_visible(self):
        """使用全面的 JavaScript 可见性测试检查元素是否可见。"""
        result = await self.execute_script(Scripts.ELEMENT_VISIBLE, return_by_value=True)
        if 'error' in result:
            return False
        return bool(result.get('result', {}).get('result', {}).get('value', False))

    async def is_on_top(self):
        """检查元素是否位于其中心点的最上面（未被覆盖层覆盖）。"""
        result = await self.execute_script(Scripts.ELEMENT_ON_TOP, return_by_value=True)
        if 'error' in result:
            return False
        return bool(result.get('result', {}).get('result', {}).get('value', False))

    async def is_interactable(self):
        """根据可见性和位置检查元素是否可交互。"""
        result = await self.execute_script(Scripts.ELEMENT_INTERACTIVE, return_by_value=True)
        if 'error' in result:
            return False
        return bool(result.get('result', {}).get('result', {}).get('value', False))

    async def execute_script(
        self,
        script: str,
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
    ) -> CallFunctionOnResponse:
        """在元素上下文中执行 JavaScript。

        参数：
            script (str)：要执行的 JavaScript 代码。使用“this”来引用该元素。
            参数（可选[list[CallArgument]]）：传递给函数的参数
                （运行时.callFunctionOn）。
            silent（可选[bool]）：是否静默异常（Runtime.callFunctionOn）。
            return_by_value (Optional[bool]): 是否按值返回结果而不是
                参考（Runtime.callFunctionOn）。
            generate_preview (Optional[bool]): 是否生成结果预览
                （运行时.callFunctionOn）。
            user_gesture (Optional[bool]): 是否将呼叫视为由用户发起
                手势（Runtime.callFunctionOn）。
            wait_promise (Optional[bool]): 是否等待promise结果
                （运行时.callFunctionOn）。
            execution_context_id（可选[int]）：调用的执行上下文的ID
                (Runtime.callFunctionOn) 中的函数。
            object_group（可选[str]）：结果的符号组名称
                （运行时.callFunctionOn）。
            throw_on_side_effect (可选[bool]): 如果无法产生副作用，是否抛出
                排除（Runtime.callFunctionOn）。
            unique_context_id（可选[str]）：函数调用的唯一上下文ID
                （运行时.callFunctionOn）。
            Serialization_options（可选[SerializationOptions]）：序列化选项
                结果（Runtime.callFunctionOn）。

        返回：
            CallFunctionOnResponse：脚本执行的结果。

        示例：
            # 单击该元素
            等待 element.execute_script('this.click()')

            # 修改元素样式
            wait element.execute_script('this.style.border = "2px 纯红色"')

            # 获取元素文本
            result =等待element.execute_script('返回this.textContent', return_by_value=True)

            # 设置元素内容
            等待 element.execute_script('this.textContent = "Hello World"')"""
        if not is_script_already_function(script):
            script = f'function(){{ {script} }}'

        loguru_logger.debug(
            f'Executing script on element: return_by_value={return_by_value}, '
            f'length={len(script)}, args={len(arguments) if arguments else 0}'
        )
        command = RuntimeCommands.call_function_on(
            function_declaration=script,
            object_id=self._object_id,
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
        return await self._execute_command(command)

    def __repr__(self):
        """显示属性和对象 ID 的字符串表示形式。"""
        attrs = ', '.join(f'{k}={v!r}' for k, v in self._attributes.items())
        return f'{self.__class__.__name__}({attrs})(object_id={self._object_id})'

    def _is_inside_iframe(self) -> bool:
        """检查此元素是否位于 iframe 上下文内（而不是 iframe 本身）。"""
        return self._iframe_context is not None and not self.is_iframe

    async def _get_iframe_inner_html(self) -> str:
        """获取 iframe 元素的内部 HTML。"""
        iframe_context = await self.iframe_context
        if iframe_context is None:
            raise InvalidIFrame('Unable to resolve iframe context')
        response: EvaluateResponse = await self._execute_command(
            RuntimeCommands.evaluate(
                expression='document.documentElement.outerHTML',
                context_id=iframe_context.execution_context_id,
                return_by_value=True,
            )
        )
        return response['result']['result'].get('value', '')

    def _apply_routing_from_context(self) -> None:
        """从 iframe 上下文应用路由属性。

        iframe 上下文解析后，针对 *内容* 的命令
        iframe 应该通过``_iframe_context`` 路由（由
        ``_resolve_routing`` 优先考虑 ``_iframe_context``
        ``_routing_session_*``）。

        ``_routing_session_handler`` / ``_routing_session_id`` 属性
        必须保留：它们标识父 OOPIF 会话，其中
        ``<iframe>`` *元素本身*存在。  解析器需要它们
        在后续重新决议中重新描述该元素。"""

    async def _click_option_tag(self):
        """单击下拉列表中的 <option> 元素的专用方法。"""
        await self._execute_command(
            RuntimeCommands.call_function_on(
                object_id=self._object_id,
                function_declaration=Scripts.CLICK_OPTION_TAG,
                return_by_value=True,
            )
        )

    async def _get_family_elements(
        self, script: str, max_depth: int = 1, tag_filter: list[str] = []
    ) -> list[WebElement]:
        """检索该元素的所有族元素（同一 DOM 级别的元素）。

        参数：
            script (str)：执行以检索族元素的 CDP 脚本。
            tag_filter（list[str]，可选）：用于过滤结果的 HTML 标记名称列表。
                如果为空，则返回所有系列元素，无论标签如何。默认为[]。

        返回：
            list[WebElement]：共享相同内容的系列 WebElement 对象列表
                父元素作为此元素并匹配标签过滤条件。"""
        result = await self.execute_script(
            script.format(tag_filter=tag_filter, max_depth=max_depth)
        )
        if not self._has_object_id_key(result):
            return []

        array_object_id = result['result']['result']['objectId']

        get_properties_command = RuntimeCommands.get_properties(object_id=array_object_id)
        properties_response: GetPropertiesResponse = await self._execute_command(
            get_properties_command
        )

        family_elements: list[WebElement] = []
        for prop in properties_response['result']['result']:
            if not (prop['name'].isdigit() and 'objectId' in prop['value']):
                continue
            child_object_id = prop['value']['objectId']
            attributes = await self._get_object_attributes(object_id=child_object_id)
            family_elements.append(
                WebElement(
                    child_object_id,
                    self._connection_handler,
                    attributes_list=attributes,
                    mouse=self._mouse,
                )
            )

        loguru_logger.debug(f'Family elements found: {len(family_elements)}')
        return family_elements

    def _def_attributes(self, attributes_list: list[str]):
        """将平面属性列表处理为字典（将“class”重命名为“class_name”）。"""
        for i in range(0, len(attributes_list), 2):
            key = attributes_list[i]
            key = key if key != 'class' else 'class_name'
            value = attributes_list[i + 1]
            self._attributes[key] = value
        loguru_logger.debug(f'Attributes defined: count={len(self._attributes)}')

    def _is_option_tag(self):
        """检查元素是否是 <option> 标记。"""
        return self._attributes.get('tag_name', '').lower() == 'option'

    async def _is_option_element(self) -> bool:
        """对 <option> 元素进行稳健检查，当 tag_name 丢失时回退到 JS。"""
        tag = self._attributes.get('tag_name', '')
        if tag:
            return tag.lower() == 'option'

        #来自原始选择器/方法的启发式
        selector = str(getattr(self, '_selector', '') or '')
        method_raw = getattr(self, '_search_method', '')
        method = str(getattr(method_raw, 'value', method_raw) or '').lower()
        if method == 'tag_name' and selector.lower() == 'option':
            return True
        if method == 'xpath' and 'option' in selector.lower():
            return True

        result = await self.execute_script(Scripts.IS_OPTION_TAG, return_by_value=True)
        is_option = result.get('result', {}).get('result', {}).get('value', False)
        if is_option and not self._attributes.get('tag_name'):
            self._attributes['tag_name'] = 'option'
        return bool(is_option)

    @staticmethod
    def _calculate_center(bounds: list) -> tuple:
        """从边界框坐标计算中心点。"""
        x_values = [bounds[i] for i in range(0, len(bounds), 2)]
        y_values = [bounds[i] for i in range(1, len(bounds), 2)]
        x_center = sum(x_values) / len(x_values)
        y_center = sum(y_values) / len(y_values)
        return x_center, y_center
