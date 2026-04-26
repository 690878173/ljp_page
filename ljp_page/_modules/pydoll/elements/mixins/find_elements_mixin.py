from __future__ import annotations

import asyncio
from ljp_page.logger import logger
from typing import TYPE_CHECKING, Optional, Union, cast, overload

from ljp_page._modules.pydoll.commands import (
    DomCommands,
    RuntimeCommands,
)
from ljp_page._modules.pydoll.connection.connection_handler import ConnectionHandler
from ljp_page._modules.pydoll.constants import By, Scripts
from ljp_page._modules.pydoll.elements.utils import SelectorParser
from ljp_page._modules.pydoll.exceptions import ElementNotFound, WaitElementTimeout

if TYPE_CHECKING:
    from typing import Literal, Optional, Union

    from ljp_page._modules.pydoll.elements.web_element import WebElement
    from ljp_page._modules.pydoll.interactions.iframe import IFrameContext
    from ljp_page._modules.pydoll.protocol.base import Command, T_CommandParams, T_CommandResponse
    from ljp_page._modules.pydoll.protocol.dom.methods import DescribeNodeResponse
    from ljp_page._modules.pydoll.protocol.dom.types import Node
    from ljp_page._modules.pydoll.protocol.runtime.methods import (
        CallFunctionOnParams,
        CallFunctionOnResponse,
        EvaluateParams,
        EvaluateResponse,
        GetPropertiesResponse,
    )


def create_web_element(*args, **kwargs):
    """创建 WebElement 实例，避免循环导入。

    在运行时动态导入 WebElement 的工厂方法
    以防止循环导入依赖。"""
    from ljp_page._modules.pydoll.elements.web_element import WebElement  #编号：PLC0415

    return WebElement(*args, **kwargs)


class FindElementsMixin:
    """Mixin 提供全面的元素查找和等待功能。

    使用各种选择器策略（CSS、XPath 等）实现 DOM 元素定位
    支持单个/多个元素查找和可配置等待。
    使用此 mixin 的类无需实现即可获得强大的元素发现
    复杂的位置逻辑本身。"""

    _css_only: bool = False

    if TYPE_CHECKING:
        _connection_handler: ConnectionHandler

    @staticmethod
    def _build_text_expression(selector: str, method: str) -> Optional[str]:
        """使用脚本构建 JS 表达式，根据选择器类型提取文本内容。"""
        return SelectorParser.build_text_expression(selector, method)

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[True] = True,
        **attributes,
    ) -> WebElement: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[False] = False,
        **attributes,
    ) -> Optional[WebElement]: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[True] = True,
        **attributes,
    ) -> list[WebElement]: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[False] = False,
        **attributes,
    ) -> Optional[list[WebElement]]: ...

    @overload
    async def find(
        self,
        id: Optional[str] = ...,
        class_name: Optional[str] = ...,
        name: Optional[str] = ...,
        tag_name: Optional[str] = ...,
        text: Optional[str] = ...,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
        **attributes,
    ) -> Union[WebElement, list[WebElement], None]: ...

    async def find(
        self,
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
        **attributes: dict[str, str],
    ) -> Union[WebElement, list[WebElement], None]:
        """使用常见 HTML 属性的组合查找元素。

        使用标准属性的灵活元素位置。多种属性
        可以针对特定选择器进行组合（指定多个时构建 XPath）。

        参数：
            id：元素ID属性值。
            class_name：要匹配的 CSS 类名称。
            name：元素名称属性值。
            tag_name：HTML 标签名称（例如“div”、“input”）。
            text：元素内匹配的文本内容。
            timeout：等待元素出现的最大秒数。
            find_all：如果为 True，则返回所有匹配项；如果为 False，则仅第一个匹配。
            raise_exc：如果没有找到元素是否引发异常。
            **属性：要匹配的其他 HTML 属性。

        返回：
            WebElement、list[WebElement] 或 None 基于 find_all 和 raise_exc。

        加薪：
            ValueError：如果未提供搜索条件。
            ElementNotFound：如果没有找到元素且 raise_exc=True。
            WaitElementTimeout：如果指定了超时并且没有元素及时出现。
            NotImplementedError：如果在 ShadowRoot 上调用（使用带有 CSS 的 query() 代替）。"""
        if self._css_only:
            raise NotImplementedError(
                'find() is not supported on ShadowRoot. Use query() with a CSS selector instead.'
            )

        logger.debug(
            f'find() called with id={id}, class_name={class_name}, name={name}, '
            f'tag_name={tag_name}, text={text}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}, attrs={attributes}'
        )
        if not any([id, class_name, name, tag_name, text, *attributes.keys()]):
            raise ValueError(
                'At least one of the following arguments must be provided: id, '
                'class_name, name, tag_name, text'
            )

        by_map = {
            'id': By.ID,
            'class_name': By.CLASS_NAME,
            'name': By.NAME,
            'tag_name': By.TAG_NAME,
            'xpath': By.XPATH,
        }
        by, value = self._get_by_and_value(
            by_map, id, class_name, name, tag_name, text, **attributes
        )
        logger.debug(f'find() resolved to by={by} value={value}')
        return await self.find_or_wait_element(
            by, value, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[True] = True,
    ) -> WebElement: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[False] = False,
        raise_exc: Literal[False] = False,
    ) -> Optional[WebElement]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[True] = True,
    ) -> list[WebElement]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: Literal[True] = True,
        raise_exc: Literal[False] = False,
    ) -> Optional[list[WebElement]]: ...

    @overload
    async def query(
        self,
        expression: str,
        timeout: int = ...,
        find_all: bool = ...,
        raise_exc: bool = ...,
    ) -> Union[WebElement, list[WebElement], None]: ...

    async def query(
        self, expression: str, timeout: int = 0, find_all: bool = False, raise_exc: bool = True
    ) -> Union[WebElement, list[WebElement], None]:
        """使用原始 CSS 选择器或 XPath 表达式查找元素。

        使用 CSS 或 XPath 语法直接访问。自动选择器类型
        根据表达模式确定。

        参数：
            表达式：选择器表达式（CSS、XPath、带 # 的 ID、带 . 的类）。
            timeout：等待元素出现的最大秒数。
            find_all：如果为 True，则返回所有匹配项；如果为 False，则仅第一个匹配。
            raise_exc：如果没有找到元素是否引发异常。

        返回：
            WebElement、list[WebElement] 或 None 基于 find_all 和 raise_exc。

        加薪：
            ElementNotFound：如果没有找到元素且 raise_exc=True。
            WaitElementTimeout：如果指定了超时并且没有元素及时出现。
            NotImplementedError：如果在 ShadowRoot 上使用 XPath 调用。"""
        if self._css_only and self._get_expression_type(expression) == By.XPATH:
            raise NotImplementedError(
                'XPath is not supported on ShadowRoot. Use a CSS selector instead.'
            )

        logger.debug(
            f'query() called with expression={expression}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}'
        )
        by = self._get_expression_type(expression)
        logger.debug(f'query() resolved to by={by}')
        return await self.find_or_wait_element(
            by=by, value=expression, timeout=timeout, find_all=find_all, raise_exc=raise_exc
        )

    async def find_or_wait_element(
        self,
        by: By,
        value: str,
        timeout: int = 0,
        find_all: bool = False,
        raise_exc: bool = True,
    ) -> Union[WebElement, list[WebElement], None]:
        """具有可选等待功能的核心元素查找方法。

        搜索具有灵活等待的元素。如果指定超时，
        重复尝试以 0.5s 延迟查找元素，直到成功或超时。
        由更高级别的 find() 和 query() 方法使用。

        参数：
            by：选择器策略（CSS_SELECTOR、XPATH、ID等）。
            value：用于定位元素的选择器值。
            timeout：等待的最大秒数（0 = 不等待）。
            find_all：如果为 True，则返回所有匹配项；如果为 False，则仅第一个匹配。
            raise_exc：如果没有找到元素是否引发异常。

        返回：
            WebElement、list[WebElement] 或 None 基于 find_all 和 raise_exc。

        加薪：
            ElementNotFound：如果在 timeout=0 且 raise_exc=True 的情况下未找到元素。
            WaitElementTimeout：如果在超时内未找到元素且 raise_exc=True。"""
        logger.debug(
            f'find_or_wait_element(): by={by}, value={value}, timeout={timeout}, '
            f'find_all={find_all}, raise_exc={raise_exc}'
        )

        if by == By.XPATH:
            segments = SelectorParser.parse_iframe_segments_xpath(value)
        elif by == By.CSS_SELECTOR:
            segments = SelectorParser.parse_iframe_segments_css(value)
        else:
            segments = [(by, value)]

        if len(segments) > 1:
            return await self._find_across_iframes(segments, timeout, find_all, raise_exc)

        find_method = self._find_element if not find_all else self._find_elements
        start_time = asyncio.get_event_loop().time()

        if not timeout:
            logger.debug('No timeout specified; performing single attempt')
            return await find_method(by, value, raise_exc=raise_exc)

        while True:
            element = await find_method(by, value, raise_exc=False)
            if element:
                if isinstance(element, list):
                    logger.debug(f'Found {len(element)} elements within timeout window')
                else:
                    logger.debug('Found 1 element within timeout window')
                return element

            if asyncio.get_event_loop().time() - start_time > timeout:
                if raise_exc:
                    logger.error('Timeout while waiting for elements')
                    raise WaitElementTimeout(
                        f'Timed out after {timeout}s waiting for element '
                        f'(by={by.value}, value={value!r})'
                    )
                return None

            await asyncio.sleep(0.5)

    async def _find_across_iframes(
        self,
        segments: list[tuple[By, str]],
        timeout: int,
        find_all: bool,
        raise_exc: bool,
    ) -> Union[WebElement, list[WebElement], None]:
        """重试循环进行 iframe 交叉元素搜索。

        重复调用 _attempt_find_across_iframes` 直到找到目标
        找到元素或*超时*到期。

        参数：
            分段：有序的“（按，选择器）”对 — 每个 iframe 边界一对
                加上目标元素的最终选择器。
            timeout：等待的最大秒数（0 = 单次尝试）。
            find_all：如果为“True”，则最后一段使用“_find_elements”。
            raise_exc：失败时是否加注。

        返回：
            找到的元素，或者失败时的“None”/“[]”。

        加薪：
            ElementNotFound：如果“timeout=0”，则没有找到任何内容，并且“raise_exc=True”。
            WaitElementTimeout：如果超时且“raise_exc=True”。"""
        start_time = asyncio.get_event_loop().time()
        selector_repr = ' -> '.join(seg for _, seg in segments)

        while True:
            result = await self._attempt_find_across_iframes(segments, find_all)
            if result is not None and result != []:
                return result

            if not timeout:
                if raise_exc:
                    raise ElementNotFound(f'Element not found across iframes: {selector_repr}')
                return [] if find_all else None

            if asyncio.get_event_loop().time() - start_time > timeout:
                if raise_exc:
                    raise WaitElementTimeout(
                        f'Timed out after {timeout}s waiting for element '
                        f'across iframes: {selector_repr}'
                    )
                return [] if find_all else None

            await asyncio.sleep(0.5)

    async def _attempt_find_across_iframes(
        self,
        segments: list[tuple[By, str]],
        find_all: bool,
    ) -> Union[WebElement, list[WebElement], None]:
        """单次尝试遍历 iframe 段并找到目标元素。

        对于每个中间段，找到一个 iframe 元素并使用它
        作为下一段的搜索上下文。最后一段尊重
        *查找全部*。

        参数：
            段：有序的“（按，选择器）”对。
            find_all：最后一段是否应返回所有匹配项。

        返回：
            如果任何中间步骤失败，则找到元素或“无”/“[]”。"""
        current_context: FindElementsMixin = self
        for i, (by, selector) in enumerate(segments):
            is_last = i == len(segments) - 1
            if is_last:
                if find_all:
                    result = await current_context._find_elements(by, selector, raise_exc=False)
                    return result if result else []
                return await current_context._find_element(by, selector, raise_exc=False)

            element = await current_context._find_element(by, selector, raise_exc=False)
            if not element or not getattr(element, 'is_iframe', False):
                return None
            current_context = element
        return None

    async def _find_element(
        self, by: By, value: str, raise_exc: bool = True
    ) -> Optional[WebElement]:
        """找到第一个匹配选择器的元素。

        执行实际元素搜索的内部方法。可以直接调用
        用于细粒度控制。在文档上下文中或相对于
        当前元素（当从 WebElement 使用时）。

        参数：
            by：选择器策略（CSS_SELECTOR、XPATH、ID等）。
            value：定位元素的选择器值。
            raise_exc：如果未找到是否引发 ElementNotFound。

        返回：
            WebElement 实例，如果未找到且 raise_exc=False，则为 None。

        加薪：
            ElementNotFound：如果未找到元素且 raise_exc=True。"""
        logger.debug(f'_find_element(): by={by}, value={value}, raise_exc={raise_exc}')
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context

        if iframe_context:
            command = self._get_find_element_command(
                by,
                value,
                object_id=iframe_context.document_object_id or '',
                execution_context_id=iframe_context.execution_context_id,
            )
        elif hasattr(self, '_object_id'):
            command = self._get_find_element_command(by, value, self._object_id)
        else:
            command = self._get_find_element_command(by, value)

        response_for_command: Union[
            EvaluateResponse, CallFunctionOnResponse
        ] = await self._execute_command(command)

        if not self._has_object_id_key(response_for_command):
            if raise_exc:
                logger.debug('Element not found and raise_exc=True')
                raise ElementNotFound()
            return None

        object_id = response_for_command['result']['result']['objectId']
        attributes = await self._get_object_attributes(object_id=object_id)
        logger.debug(f'_find_element() found object_id={object_id}')
        element = create_web_element(
            object_id,
            self._connection_handler,
            by,
            value,
            attributes,
            mouse=getattr(self, '_mouse', None),
        )
        self._apply_iframe_context_to_element(
            element, iframe_context or getattr(self, '_iframe_context', None)
        )
        return element

    async def _find_elements(self, by: By, value: str, raise_exc: bool = True) -> list[WebElement]:
        """查找所有与选择器匹配的元素。

        执行实际多元素搜索的内部方法。可以直接调用
        用于细粒度控制。在文档上下文中或相对于
        当前元素（当从 WebElement 使用时）。

        参数：
            by：选择器策略（CSS_SELECTOR、XPATH、ID等）。
            value：用于定位元素的选择器值。
            raise_exc：如果没有找到，是否引发 ElementNotFound。

        返回：
            WebElement 实例列表（如果未找到且 raise_exc=False，则为空）。

        加薪：
            ElementNotFound：如果没有找到元素且 raise_exc=True。"""
        logger.debug(f'_find_elements(): by={by}, value={value}, raise_exc={raise_exc}')
        iframe_context = None
        if getattr(self, 'is_iframe', False):
            element_self = cast('WebElement', self)
            iframe_context = await element_self.iframe_context

        if iframe_context:
            command = self._get_find_elements_command(
                by,
                value,
                object_id=iframe_context.document_object_id or '',
                execution_context_id=iframe_context.execution_context_id,
            )
        elif hasattr(self, '_object_id'):
            command = self._get_find_elements_command(by, value, self._object_id)
        else:
            command = self._get_find_elements_command(by, value)

        response_for_command: Union[
            EvaluateResponse, CallFunctionOnResponse
        ] = await self._execute_command(command)

        if not response_for_command.get('result', {}).get('result', {}).get('objectId'):
            if raise_exc:
                logger.debug('No elements found and raise_exc=True')
                raise ElementNotFound()
            return []

        object_id = response_for_command['result']['result']['objectId']
        query_response: GetPropertiesResponse = await self._execute_command(
            RuntimeCommands.get_properties(object_id=object_id)
        )
        response: list[str] = []
        for query in query_response['result']['result']:
            if not (query['name'].isdigit() and 'objectId' in query['value']):
                continue
            response.append(query['value']['objectId'])

        inherited_context = iframe_context or getattr(self, '_iframe_context', None)
        elements = []
        for object_id in response:
            try:
                node_description = await self._describe_node(object_id=object_id)
            except KeyError:
                continue

            attributes = node_description.get('attributes', [])
            tag_name = node_description.get('nodeName', '').lower()
            attributes.extend(['tag_name', tag_name])

            child = create_web_element(
                object_id,
                self._connection_handler,
                by,
                value,
                attributes,
                mouse=getattr(self, '_mouse', None),
            )
            self._apply_iframe_context_to_element(child, inherited_context)
            elements.append(child)
        logger.debug(f'_find_elements() returning {len(elements)} elements')
        return elements

    async def _get_object_attributes(self, object_id: str) -> list[str]:
        """获取 DOM 节点的属性。"""
        node_description = await self._describe_node(object_id=object_id)
        if not node_description:
            #如果无法描述节点（例如，对象 id 不引用节点），
            #返回最少的属性以保持流量稳定。
            return ['tag_name', '']
        attributes = node_description.get('attributes', [])
        tag_name = node_description.get('nodeName', '').lower()
        attributes.extend(['tag_name', tag_name])
        return attributes

    def _get_by_and_value(
        self,
        by_map: dict[str, By],
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes,
    ) -> tuple[By, str]:
        """根据提供的参数确定适当的选择器策略和值。

        对于单个属性：使用直接选择器策略。
        对于多个属性：构建 XPath 表达式。"""
        logger.debug(
            f'_get_by_and_value(): id={id}, class_name={class_name}, name={name}, '
            f'tag_name={tag_name}, text={text}, attrs={attributes}'
        )
        xpath_raw = attributes.get('xpath')
        if isinstance(xpath_raw, str) and xpath_raw:
            logger.debug(f'Explicit XPath provided; using raw expression: {xpath_raw}')
            return By.XPATH, xpath_raw

        simple_selectors = {
            'id': id,
            'class_name': class_name,
            'name': name,
            'tag_name': tag_name,
        }
        provided_selectors = {key: value for key, value in simple_selectors.items() if value}

        if len(provided_selectors) == 1 and not text and not attributes:
            key, value = next(iter(provided_selectors.items()))
            by = by_map[key]
            logger.debug(f'Simple selector resolved: by={by}, value={value}')
            return by, value

        xpath = self._build_xpath(id, class_name, name, tag_name, text, **attributes)
        logger.debug(f'Complex selector resolved to XPath: {xpath}')
        return By.XPATH, xpath

    @staticmethod
    def _build_xpath(
        id: Optional[str] = None,
        class_name: Optional[str] = None,
        name: Optional[str] = None,
        tag_name: Optional[str] = None,
        text: Optional[str] = None,
        **attributes: str,
    ) -> str:
        """根据多个属性标准构建 XPath 表达式。

        使用“and”运算符组合多个条件来构造复杂的 XPath。
        正确处理空格分隔的类列表的类名。
        使用 contains() 进行文本匹配（部分文本支持）。

        注意：
            带下划线的属性名称会自动转换为连字符
            以匹配 HTML 属性命名约定（例如，data_test -> data-test）。"""
        return SelectorParser.build_xpath(id, class_name, name, tag_name, text, **attributes)

    @staticmethod
    def _get_expression_type(expression: str) -> By:
        """从表达式语法自动检测选择器类型。

        图案：
        - XPath：以 ./ 或 / 开头
        - 默认：CSS_SELECTOR"""
        return SelectorParser.get_expression_type(expression)

    async def _describe_node(self, object_id: str = '') -> Node:
        """使用 CDP DOM.describeNode 获取详细的 DOM 节点信息。

        在内部用于收集 WebElement 初始化的数据。"""
        response: DescribeNodeResponse = await self._execute_command(
            DomCommands.describe_node(object_id=object_id)
        )
        if 'error' in response:
            #当CDP报告objectId时返回空节点结构
            #未引用节点或发生任何其他描述错误。
            return {}
        return response.get('result', {}).get('node', {})

    def _apply_iframe_context_to_element(
        self, element: WebElement, iframe_context: IFrameContext | None
    ) -> None:
        """将 iframe 上下文传播到新创建的元素。
        - 如果元素也是 iframe，则配置会话路由。
        - 否则，注入 iframe 自己的上下文。"""
        if not iframe_context:
            return
        if getattr(element, 'is_iframe', False):
            routing_handler = iframe_context.session_handler or self._connection_handler
            element._routing_session_handler = routing_handler
            element._routing_session_id = iframe_context.session_id
            element._routing_parent_frame_id = iframe_context.frame_id
            return
        element._iframe_context = iframe_context

    def _resolve_routing(self) -> tuple[ConnectionHandler, Optional[str]]:
        """解析当前上下文的处理程序和 sessionId（iframe 路由或默认）。"""
        iframe_context = getattr(self, '_iframe_context', None)
        if iframe_context and getattr(iframe_context, 'session_handler', None):
            return iframe_context.session_handler, getattr(iframe_context, 'session_id', None)
        routing_handler = getattr(self, '_routing_session_handler', None)
        if routing_handler is not None:
            return routing_handler, getattr(self, '_routing_session_id', None)
        return self._connection_handler, None

    async def _execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse]
    ) -> T_CommandResponse:
        """通过已解析处理程序执行 CDP 命令（60 秒超时）。"""
        handler, session_id = self._resolve_routing()
        if session_id:
            command['sessionId'] = session_id
        return await handler.execute_command(command, timeout=60)

    def _get_find_element_command(
        self,
        by: By,
        value: str,
        object_id: str = '',
        execution_context_id: Optional[int] = None,
    ):
        """创建用于查找单个元素的 CDP 命令。

        处理不同选择器类型和上下文的特殊情况：
        - CLASS_NAME/ID：转换为 CSS 选择器
        - 相对搜索：对上下文元素使用不同的脚本
        - XPath：需要特殊处理
        - NAME：转换为 XPath 表达式"""
        escaped_value = value.replace('"', '\\"')
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
        match by:
            case By.CLASS_NAME:
                selector = f'.{escaped_value}'
            case By.ID:
                selector = f'#{escaped_value}'
            case _:
                selector = escaped_value
        if object_id and not by == By.XPATH:
            script = Scripts.RELATIVE_QUERY_SELECTOR.replace('{selector}', selector)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        elif by == By.XPATH:
            command = self._get_find_element_by_xpath_command(
                value, object_id=object_id, execution_context_id=execution_context_id
            )
        elif by == By.NAME:
            command = self._get_find_element_by_xpath_command(
                f'//*[@name="{escaped_value}"]',
                object_id=object_id,
                execution_context_id=execution_context_id,
            )
        else:
            command = RuntimeCommands.evaluate(
                expression=Scripts.QUERY_SELECTOR.replace('{selector}', selector),
                context_id=execution_context_id,
            )
        return command

    def _get_find_elements_command(
        self,
        by: By,
        value: str,
        object_id: str = '',
        execution_context_id: Optional[int] = None,
    ):
        """创建用于查找多个元素的 CDP 命令。

        与 _get_find_element_command 类似，但用于多个元素搜索。
        处理相同的特殊情况和选择器类型转换。"""
        escaped_value = value.replace('"', '\\"')
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
        match by:
            case By.CLASS_NAME:
                selector = f'.{escaped_value}'
            case By.ID:
                selector = f'#{escaped_value}'
            case _:
                selector = escaped_value
        if object_id and not by == By.XPATH:
            script = Scripts.RELATIVE_QUERY_SELECTOR_ALL.replace('{selector}', selector)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        elif by == By.XPATH:
            command = self._get_find_elements_by_xpath_command(
                value, object_id=object_id, execution_context_id=execution_context_id
            )
        else:
            command = RuntimeCommands.evaluate(
                expression=Scripts.QUERY_SELECTOR_ALL.replace('{selector}', selector),
                context_id=execution_context_id,
            )
        return command

    def _get_find_element_by_xpath_command(
        self,
        xpath: str,
        object_id: str,
        execution_context_id: Optional[int] = None,
    ):
        """专门为 XPath 单元素查找创建 CDP 命令。

        与 CSS 选择器相比，XPath 需要特殊处理。确保相对
        用于基于上下文的搜索的 XPath。"""
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
        escaped_value = xpath.replace('"', '\\"')
        if object_id:
            escaped_value = self._ensure_relative_xpath(escaped_value)
            script = Scripts.FIND_RELATIVE_XPATH_ELEMENT.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        else:
            script = Scripts.FIND_XPATH_ELEMENT.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.evaluate(expression=script, context_id=execution_context_id)
        return command

    def _get_find_elements_by_xpath_command(
        self,
        xpath: str,
        object_id: str,
        execution_context_id: Optional[int] = None,
    ):
        """专门为 XPath 多元素查找创建 CDP 命令。

        与 CSS 选择器相比，XPath 需要特殊处理。确保相对
        用于基于上下文的搜索的 XPath。"""
        escaped_value = xpath.replace('"', '\\"')
        command: Union[
            Command[CallFunctionOnParams, CallFunctionOnResponse],
            Command[EvaluateParams, EvaluateResponse],
        ]
        if object_id:
            escaped_value = self._ensure_relative_xpath(escaped_value)
            script = Scripts.FIND_RELATIVE_XPATH_ELEMENTS.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.call_function_on(
                function_declaration=script,
                object_id=object_id,
                return_by_value=False,
            )
        else:
            script = Scripts.FIND_XPATH_ELEMENTS.replace('{escaped_value}', escaped_value)
            command = RuntimeCommands.evaluate(expression=script, context_id=execution_context_id)
        return command

    @staticmethod
    def _ensure_relative_xpath(xpath: str) -> str:
        """如果需要，可以通过在前面添加点来确保 XPath 是相对的。

        将绝对 XPath 转换为相对 XPath 以进行基于上下文的搜索。"""
        return SelectorParser.ensure_relative_xpath(xpath)

    @staticmethod
    def _has_object_id_key(response: Union[EvaluateResponse, CallFunctionOnResponse]) -> bool:
        """检查响应是否具有 objectId 键。"""
        return bool(response.get('result', {}).get('result', {}).get('objectId'))
