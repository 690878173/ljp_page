"""提取器模块的异常类。"""

from __future__ import annotations

from ljp_page._module.request.brower.pydoll.exceptions import PydollException


__all__ = ['ExtractionException', 'FieldExtractionFailed', 'InvalidExtractionModel']

class ExtractionException(PydollException):
    """与数据提取相关的异常的基类。"""

    message = 'An extraction error occurred'


class FieldExtractionFailed(ExtractionException):
    """当无法提取必填字段并且没有默认值时引发。"""

    message = 'Failed to extract required field'


class InvalidExtractionModel(ExtractionException):
    """当 ExtractionModel 定义无效时引发。"""

    message = 'Invalid extraction model definition'
