# 04-01-20-09-00
"""JS 运行配置。"""

from dataclasses import dataclass


@dataclass(slots=True)
class JsRuntimeConfig:
    """Js 模块默认配置。"""

    engine: str = "execjs"
    encoding: str = "utf-8"


__all__ = ["JsRuntimeConfig"]
