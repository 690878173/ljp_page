"""用于声明性数据提取的 ExtractionModel 基类。"""

from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict

from ljp_page._module.request.brower.pydoll import InvalidExtractionModel
from ljp_page._module.request.brower.pydoll.extractor.field import ExtractionMetadata, pop_field_metadata


class ExtractionModel(BaseModel):
    """声明性提取模型的基类。

    继承自pydantic.BaseModel，获得自动验证，
    类型强制、序列化（model_dump、model_dump_json）和
    JSON 模式生成 (model_json_schema)。

    子类使用 Field() 描述符和选择器定义字段
    和/或语义描述。提取引擎使用这个
    元数据从网页中提取结构化数据。

    示例::

        类文章（提取模型）：
            title: str = Field(selector='h1', description='文章标题')
            作者：str = Field(selector='.author',description='作者姓名')"""

    _extraction_fields_cache: ClassVar[Optional[dict[str, ExtractionMetadata]]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def get_extraction_fields(cls) -> dict[str, ExtractionMetadata]:
        """获取所有字段的提取元数据，在首次访问时延迟收集。

        每个子类都有自己的缓存，即使父类已经有
        已被收集。这可确保正确包含继承的字段。

        返回：
            将字段名称映射到 ExtractionMetadata 的字典。

        加薪：
            InvalidExtractionModel：如果字段有元数据但缺少
                选择器和描述。"""
        #检查自己的 __dict__ 以避免通过 MRO 继承父级的缓存
        own_cache = cls.__dict__.get('_extraction_fields_cache')
        if own_cache is not None:
            return own_cache

        result = _collect_extraction_metadata(cls)
        cls._extraction_fields_cache = result
        return result


def _collect_extraction_metadata(
    cls: type[ExtractionModel],
) -> dict[str, ExtractionMetadata]:
    """通过注册表从 pydantic FieldInfo 对象读取 ExtractionMetadata。

    对于每个字段，检查 json_schema_extra 是否包含 _extraction_key
    映射到已注册的 ExtractionMetadata。验证每个
    提取字段至少有一个选择器或一个描述。

    参数：
        cls：要检查的 ExtractionModel 子类。

    返回：
        将字段名称映射到 ExtractionMetadata 的字典。

    加薪：
        InvalidExtractionModel：如果字段有元数据但缺少
            选择器和描述。"""
    result: dict[str, ExtractionMetadata] = {}
    for name, field_info in cls.model_fields.items():
        extra = field_info.json_schema_extra
        if not isinstance(extra, dict):
            continue

        key = extra.get('_extraction_key')
        if not isinstance(key, int):
            continue

        metadata = pop_field_metadata(key)
        if metadata is None:
            continue

        if not metadata.has_selector and not field_info.description:
            raise InvalidExtractionModel(
                f'Field "{name}" must have at least a selector or a description'
            )

        result[name] = metadata
    return result
