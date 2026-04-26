"""该模块使用浏览器的 fetch API 提供 HTTP 客户端功能。
它允许在浏览器上下文中发出 HTTP 请求，重用 cookie 和标头。"""

from .har_recorder import HarCapture
from .request import Request
from .response import Response

__all__ = ['HarCapture', 'Request', 'Response']
