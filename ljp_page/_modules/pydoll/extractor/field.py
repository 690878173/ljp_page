"""ExtractionModel 字段的字段描述符和提取元数据。"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Optional, Union, cast

from pydantic import Field as PydanticField
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from ljp_page._modules.pydoll.extractor.exceptions import InvalidExtractionModel

#模块级注册表：存储由唯一 int 键控的 ExtractionMetadata。
#Field() 注册元数据并将密钥存储在 pydantic 的 json_schema_extra 中。
#ExtractionModel.get_extraction_fields() 读取密钥以检索元数据。
_FIELD_METADATA_REGISTRY: dict[int, ExtractionMetadata] = {}
_field_id_counter = itertools.count(1)


@dataclass(frozen=True)
class ExtractionMetadata:
    """附加到 pydantic 字段的不可变提取元数据。

    通过 Field() 存储在模块级注册表中并通过
    ExtractionModel.get_extraction_fields() 通过存储的注册表项
    在字段的 json_schema_extra 中。"""

    selector: Optional[str] = None
    attribute: Optional[str] = None
    transform: Optional[Callable[[str], Union[str, int, float, bool, object]]] = None

    @property
    def has_selector(self) -> bool:
        """该字段是否有 CSS 或 XPath 选择器。"""
        return self.selector is not None


def pop_field_metadata(key: int) -> Optional[ExtractionMetadata]:
    """通过密钥从注册表中检索并删除 ExtractionMetadata。

    使用 pop 来防止注册表无限增长。
    每个键在模型类创建期间仅被消耗一次。

    参数：
        key：存储在 json_schema_extra['_extraction_key'] 中的注册表项。

    返回：
        如果找到，则为 ExtractionMetadata，否则为 None。"""
    return _FIELD_METADATA_REGISTRY.pop(key, None)


def Field(
    *,
    selector: Optional[str] = None,
    attribute: Optional[str] = None,
    description: Optional[str] = None,
    default: object = PydanticUndefined,
    transform: Optional[Callable[[str], Union[str, int, float, bool, object]]] = None,
) -> FieldInfo:
    """定义模型字段的提取元数据。

    包装 pydantic.Field() 并为引擎注册 ExtractionMetadata。
    从选择器语法中自动检测 CSS 与 XPath（与 Tab.query() 的逻辑相同）。

    必须至少提供“选择器”或“描述”之一：
    - 仅选择器：通过 CSS/XPath 提取。
    - 仅描述：用于未来 LLM 提取的元数据。
    - 两者：CSS 提取与未来汽车策略中的 LLM 后备。

    参数：
        选择器：CSS 或 XPath 选择器（自动检测，如 Tab.query()）。
        attribute：要提取的 HTML 属性（默认值：innerText）。
        描述：字段的语义描述。
        default：提取失败时的默认值。 PydanticUndefined 表示必需。
        转换：应用于原始提取字符串的后处理可调用。

    返回：
        Pydantic FieldInfo，在 json_schema_extra 中提取注册表项。

    加薪：
        InvalidExtractionModel：如果既没有提供选择器也没有提供描述。"""
    if selector is None and description is None:
        raise InvalidExtractionModel('Field must have at least a selector or a description')

    metadata = ExtractionMetadata(
        selector=selector,
        attribute=attribute,
        transform=transform,
    )

    key = _register_metadata(metadata)

    return cast(
        FieldInfo,
        PydanticField(
            default=default,
            description=description,
            json_schema_extra={'_extraction_key': key},
        ),
    )


def _register_metadata(metadata: ExtractionMetadata) -> int:
    """注册 ExtractionMetadata 并返回其唯一密钥。"""
    key = next(_field_id_counter)
    _FIELD_METADATA_REGISTRY[key] = metadata
    return key
