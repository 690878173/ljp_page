from __future__ import annotations

import sys
from typing import Any

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    _file_path = str| Path|None

class LjpBaseException(Exception):  # noqa: N818
    """项目全局唯一自定义异常基类（增强版，支持子类继承）"""
    message:str = '异常'

    def __init__(self,message: str|None,*,context: dict | None = None,) -> None:

        self.context = context or {}
        message = message or self.message
        frame = self._get_real_caller_frame()

        class_name = None
        method_name = frame.f_code.co_name

        if "self" in frame.f_locals:
            self_obj = frame.f_locals["self"]
            class_name = self_obj.__class__.__name__

        location = f"{class_name}.{method_name}" if class_name else method_name
        self.message = f"({location}): {message}"

        super().__init__(self.message)

    @staticmethod
    def _get_real_caller_frame():
        """获取【真正抛异常的那一行】的栈帧，自动跳过子类 __init__"""
        depth = 1
        while True:
            try:
                frame = sys._getframe(depth)
                # 跳过所有异常类内部的 __init__ 方法（基类 + 子类）
                if frame.f_code.co_name == "__init__" and issubclass(
                    frame.f_locals.get("self").__class__, Exception
                ):
                    depth += 1
                else:
                    return frame
            except ValueError:
                return sys._getframe(1)

    def __str__(self) -> str:
        base = super().__str__()
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base = f"{base} | [{ctx_str}]"


        if self.__cause__:
            base = f"{base} ==> {self.__cause__}"

        return base


class No(LjpBaseException):
    """通用错误异常。"""
    message = '出错'

class Yes(LjpBaseException):
    message = '预期错误'

class ConfigError(LjpBaseException):
    message = '配置错误'


class Notfound(LjpBaseException):
    """资源未找到"""
    message = "未找到资源"
    def __init__(self, message: str | None = None, *, resource: str | None = None,** kwargs: Any) -> None:
        self.resource = resource
        super().__init__(message, **kwargs)
    def __str__(self) -> str:
        msg = super().__str__()
        if self.resource:
            msg += f" (资源: {self.resource})"
        return msg


class ParseError(LjpBaseException):
    """数据解析失败"""
    message = "数据解析失败"

class HtmlParseError(ParseError):
    """HTML 解析失败"""
    message = "HTML 解析失败"

class ResponseParseException(ParseError):
    """响应解析异常"""
    message = "响应解析失败"
    def __init__(self, message: str | None = None, *, url: str | None = None,** kwargs: Any) -> None:
        self.url = url
        super().__init__(message, **kwargs)
    def __str__(self) -> str:
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        return msg


class MeetCheckError(LjpBaseException):
    """触发风控/反爬"""
    message = "遇到反爬"
    def __init__(self, message: str | None = None, *, check_type: str | None = None, url: str | None = None,** kwargs: Any) -> None:
        self.check_type = check_type
        self.url = url
        msg = message or self.message
        if check_type:
            msg += f" (检测类型: {check_type})"
        if url:
            msg += f" (URL: {url})"
        super().__init__(msg, **kwargs)


class CaptchaException(LjpBaseException):
    """验证码异常"""
    message = "验证码识别失败"
    def __init__(self, message: str | None = None, *, captcha_type: str | None = None,** kwargs: Any) -> None:
        self.captcha_type = captcha_type
        msg = message or self.message
        if captcha_type:
            msg += f" (验证码类型: {captcha_type})"
        super().__init__(msg, **kwargs)


class NetworkException(LjpBaseException):
    """网络异常基类"""
    message = "网络异常"
    def __init__(self, message: str | None = None, *, url: str | None = None,** kwargs: Any) -> None:
        self.url = url
        super().__init__(message, **kwargs)
    def __str__(self) -> str:
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        return msg

class NetworkError(NetworkException):
    message = "网络错误"


class RequestException(NetworkException):
    message = "请求失败"


class ProxyException(NetworkException):
    message = "代理异常"


class SSLException(NetworkException):
    message = "SSL 异常"


class HTTPStatusException(NetworkException):
    message = "HTTP 状态异常"


class TimeoutException(LjpBaseException):
    """超时异常"""
    message = "执行超时"
    def __init__(self, message: str | None = None, *, timeout: float | None = None,** kwargs: Any) -> None:
        self.timeout = timeout
        msg = message or self.message
        super().__init__(msg, **kwargs)
    def __str__(self) -> str:
        msg = super().__str__()
        if self.timeout is not None:
            msg += f" (超时: {self.timeout}s)"
        return msg


class MaxRetriesException(TimeoutException):
    """超过最大重试次数"""
    message = "超过最大重试次数"


class EncodingException(LjpBaseException):
    message = "编码处理失败"


class OpenFileException(LjpBaseException):
    message = "文件打开失败"
    def __init__(self, message: str | None = None, *, file_path: _file_path = None,** kwargs: Any) -> None:
        self.file_path = file_path
        super().__init__(message, **kwargs)
    def __str__(self) -> str:
        msg = super().__str__()
        if self.file_path:
            msg += f" (路径: {self.file_path})"
        return msg


class CloseFileException(LjpBaseException):
    message = "文件关闭失败"
    def __init__(self, message: str | None = None, *, file_path: _file_path = None,** kwargs: Any) -> None:
        self.file_path = file_path
        super().__init__(message, **kwargs)
    def __str__(self) -> str:
        msg = super().__str__()
        if self.file_path:
            msg += f" (路径: {self.file_path})"
        return msg


ALL_EXCEPTIONS = (
    No, Yes, ConfigError, Notfound, ParseError, HtmlParseError, ResponseParseException,
    MeetCheckError, CaptchaException, NetworkException, NetworkError, RequestException,
    ProxyException, SSLException, HTTPStatusException, TimeoutException, MaxRetriesException,
    EncodingException, OpenFileException, CloseFileException
)

__all__ = [
    "LjpBaseException", "No", "Yes", "ConfigError", "Notfound", "ParseError", "HtmlParseError",
    "ResponseParseException", "MeetCheckError", "CaptchaException", "NetworkException",
    "NetworkError", "RequestException", "ProxyException", "SSLException",
    "HTTPStatusException", "TimeoutException", "MaxRetriesException", "EncodingException",
    "OpenFileException", "CloseFileException", "ALL_EXCEPTIONS"
]
