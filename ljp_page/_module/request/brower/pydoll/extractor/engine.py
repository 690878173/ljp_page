"""协调 DOM 查询和模型构建的提取引擎。"""

from __future__ import annotations

import asyncio
import logging
import types
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Optional, TypeVar, Union, get_args, get_origin

from ljp_page._module.request.brower.pydoll import FindElementsMixin
from ljp_page._module.request.brower.pydoll.elements.web_element import WebElement
from ljp_page._module.request.brower.pydoll import FieldExtractionFailed
from ljp_page._module.request.brower.pydoll.extractor.field import ExtractionMetadata
from ljp_page._module.request.brower.pydoll import ExtractionModel

__all__ = ['ExtractionEngine']

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.tab import Tab

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ExtractionModel')


class ExtractionEngine:
    """通过查询 DOM 和构建模型实例来协调提取。

    Tab.extract() 和 Tab.extract_all() 使用的内部引擎。
    用户不直接与其交互。"""

    def __init__(self, tab: Tab) -> None:
        self._tab = tab

    async def extract(
        self,
        model: type[T],
        *,
        scope: Optional[str] = None,
        timeout: int = 0,
    ) -> T:
        """从页面中提取单个模型实例。

        参数：
            model：要填充的 ExtractionModel 子类。
            范围：可选的 CSS/XPath 选择器，用于限制提取区域。
            timeout：等待元素出现的秒数（0 = 不等待）。

        返回：
            已填充的模型实例。

        加薪：
            FieldExtractionFailed：如果无法提取必填字段。"""
        context: FindElementsMixin = self._tab
        if scope is not None:
            result = await self._tab.query(scope, timeout=timeout)
            if not isinstance(result, WebElement):
                raise ValueError(
                    f'Expected a single element for scope "{scope}", got {type(result)}'
                )
            context = result

        values = await self._extract_fields(model, context, timeout)
        return _build_instance(model, values)

    async def extract_all(
        self,
        model: type[T],
        *,
        scope: str,
        timeout: int = 0,
        limit: Optional[int] = None,
    ) -> list[T]:
        """从重复的容器中提取多个模型实例。

        每个元素匹配范围都会生成一个模型实例。

        参数：
            model：要填充的 ExtractionModel 子类。
            范围：重复容器的 CSS/XPath 选择器（必需）。
            timeout：等待元素出现的秒数（0 = 不等待）。
            limit：要提取的最大项目数（无=全部）。

        返回：
            已填充模型实例的列表。"""
        found = await self._tab.query(scope, find_all=True, timeout=timeout, raise_exc=False)
        if found is None or not found:
            return []

        containers: list[WebElement] = found if isinstance(found, list) else [found]

        if limit is not None:
            containers = containers[:limit]

        extraction_tasks = [
            self._extract_fields(model, container, timeout) for container in containers
        ]
        all_values = await asyncio.gather(*extraction_tasks)
        return [_build_instance(model, values) for values in all_values]

    async def _extract_fields(
        self,
        model: type[T],
        context: FindElementsMixin,
        timeout: int,
    ) -> dict[str, Union[str, int, float, bool, list[str], object]]:
        """同时从 DOM 中提取所有字段。

        使用 asyncio.gather 并行启动所有字段提取，
        然后收集结果并处理每个字段的错误。

        参数：
            model：具有提取字段的 ExtractionModel 子类。
            context：用于限定查询范围的 Tab 或 WebElement。
            timeout：等待每个元素出现的秒数。

        返回：
            字段名称字典 -> 提取值。"""
        field_names: list[str] = []
        coroutines: list[
            Coroutine[None, None, Union[str, int, float, bool, list[str], object]]
        ] = []

        for name, metadata in model.get_extraction_fields().items():
            if not metadata.has_selector:
                logger.debug(f'Skipping field "{name}" (no selector)')
                continue

            field_info = model.model_fields[name]
            annotation = field_info.annotation
            if annotation is None:
                continue

            field_names.append(name)
            coroutines.append(self._extract_field(metadata, annotation, context, timeout))

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        values: dict[str, Union[str, int, float, bool, list[str], object]] = {}
        for name, result in zip(field_names, results):
            if isinstance(result, BaseException):
                field_info = model.model_fields[name]
                if not field_info.is_required():
                    logger.debug(f'Optional field "{name}" extraction failed: {result}')
                    continue
                raise FieldExtractionFailed(
                    f'Required field "{name}" could not be extracted: {result}'
                ) from result
            values[name] = result

        return values

    async def _extract_field(
        self,
        metadata: ExtractionMetadata,
        annotation: type,
        context: FindElementsMixin,
        timeout: int,
    ) -> Union[str, int, float, bool, list[str], object]:
        """从 DOM 中提取单个字段值。

        处理标量类型、列表类型、嵌套 ExtractionModel、
        并列出[ExtractionModel]。

        参数：
            元数据：使用选择器/属性/转换提取元数据。
            注释：字段的解析类型注释。
            context：要在其中查询的选项卡或 WebElement。
            timeout：等待元素出现的秒数。

        返回：
            提取并可选择转换的值。"""
        unwrapped = _unwrap_optional(annotation)

        if _is_list_type(unwrapped):
            return await self._extract_list_field(metadata, unwrapped, context, timeout)

        if _is_extraction_model(unwrapped):
            return await self._extract_nested_model(metadata, unwrapped, context, timeout)

        return await _extract_scalar_field(metadata, context, timeout)

    async def _extract_list_field(
        self,
        metadata: ExtractionMetadata,
        annotation: type,
        context: FindElementsMixin,
        timeout: int,
    ) -> list[Union[str, int, float, bool, object]]:
        """从多个匹配元素中提取值列表。"""
        selector = metadata.selector
        if selector is None:
            return []

        found = await context.query(selector, find_all=True, timeout=timeout, raise_exc=False)
        if found is None or not found:
            return []

        elements: list[WebElement] = found if isinstance(found, list) else [found]
        inner_type = _get_inner_type(annotation)

        if _is_extraction_model(inner_type):
            all_field_values = await asyncio.gather(
                *(self._extract_fields(inner_type, el, timeout) for el in elements)
            )
            return [_build_instance(inner_type, fv) for fv in all_field_values]

        all_raw = await asyncio.gather(*(_extract_value(el, metadata) for el in elements))
        return [_apply_transform(raw, metadata) for raw in all_raw]

    async def _extract_nested_model(
        self,
        metadata: ExtractionMetadata,
        model: type[T],
        context: FindElementsMixin,
        timeout: int,
    ) -> T:
        """通过将范围限定到选择器元素来提取嵌套的 ExtractionModel。"""
        selector = metadata.selector
        if selector is None:
            raise FieldExtractionFailed('Nested model field has no selector')

        result = await context.query(selector, timeout=timeout, raise_exc=True)
        if not isinstance(result, WebElement):
            raise ValueError(f'Expected a single element for "{selector}", got {type(result)}')
        values = await self._extract_fields(model, result, timeout)
        return _build_instance(model, values)


async def _extract_scalar_field(
    metadata: ExtractionMetadata,
    context: FindElementsMixin,
    timeout: int,
) -> Union[str, int, float, bool, object]:
    """从 DOM 中提取单个标量值。"""
    selector = metadata.selector
    if selector is None:
        raise FieldExtractionFailed('Scalar field has no selector')

    result = await context.query(selector, timeout=timeout, raise_exc=True)
    if not isinstance(result, WebElement):
        raise ValueError(f'Expected a single element for "{selector}", got {type(result)}')
    raw = await _extract_value(result, metadata)
    return _apply_transform(raw, metadata)


async def _extract_value(
    element: WebElement,
    metadata: ExtractionMetadata,
) -> str:
    """从 WebElement 读取原始字符串值。

    如果设置了metadata.attribute，则读取该HTML 属性。
    否则读取 element.text (innerText)。

    参数：
        element：要读取的 WebElement。
        元数据：具有可选属性名称的字段元数据。

    返回：
        转换前的原始字符串值。"""
    if metadata.attribute is not None:
        return element.get_attribute(metadata.attribute) or ''
    return await element.text


def _apply_transform(
    raw: str,
    metadata: ExtractionMetadata,
) -> Union[str, int, float, bool, object]:
    """将metadata.transform应用于原始提取的字符串。

    参数：
        raw：来自 DOM 的原始字符串。
        元数据：具有可选转换可调用的字段元数据。

    返回：
        转换后的值，如果没有转换则为原始字符串。"""
    if metadata.transform is not None:
        return metadata.transform(raw)
    return raw


def _build_instance(
    model: type[T],
    values: dict[str, Union[str, int, float, bool, list[str], object]],
) -> T:
    """从提取的值构建模型实例。

    Pydantic 处理验证、类型强制和默认值。

    参数：
        model：ExtractionModel 子类。
        值：字段名称 -> 值映射。

    返回：
        已填充的模型实例。

    加薪：
        FieldExtractionFailed：如果 pydantic 验证失败。"""
    try:
        return model(**values)
    except Exception as exc:
        raise FieldExtractionFailed(f'Failed to build {model.__name__}: {exc}') from exc


def _unwrap_optional(annotation: type) -> type:
    """展开可选[X] 或 X | None 到 X。否则返回注释不变。

    处理 types.Optional (Union) 和 PEP 604 语法 (types.UnionType)。"""
    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, types.UnionType):
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _is_list_type(annotation: type) -> bool:
    """检查注释是否为列表[X]。"""
    return get_origin(annotation) is list


def _get_inner_type(annotation: type) -> type:
    """从列表[X]中获取X。"""
    args = get_args(annotation)
    if args:
        return args[0]
    return str


def _is_extraction_model(annotation: type) -> bool:
    """检查注释是否是 ExtractionModel 子类。"""
    try:
        return isinstance(annotation, type) and issubclass(annotation, ExtractionModel)
    except TypeError:
        return False
