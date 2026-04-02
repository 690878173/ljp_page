# 04-01-20-08-00
"""JS 模块导出。"""

from .config import JsRuntimeConfig
from .js_handler import Js

__all__ = ["Js", "JsRuntimeConfig"]
