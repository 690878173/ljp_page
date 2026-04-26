from __future__ import annotations

from typing import Any
import sys

class LjpBaseException(Exception):
    """项目全局唯一自定义异常基类（增强版）"""

    def __init__(
        self,
        message: str,
        *,
        e: Exception | None = None,
        context: dict | None = None,
    ) -> None:
        self.e = e  # 原始异常
        self.context = context or {}

        frame = sys._getframe(1)  # 获取调用栈的上一帧
        class_name = None
        method_name = frame.f_code.co_name  # 当前方法名

        if "self" in frame.f_locals:
            self_obj = frame.f_locals["self"]
            class_name = self_obj.__class__.__name__  # 获取类名

        location = f"{class_name}.{method_name}" if class_name else method_name

        message = f"({location}): {message}"

        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()

        # 只在有 context 时追加（避免污染普通异常）
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base = f"{base} | [{ctx_str}]"

        if self.e:
            return f"{base} ==> {self.e}"
        return base


class No(LjpBaseException):
    """通用错误异常。"""

    def __init__(self, message: str = "出错", *args: Any, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)


class Yes(LjpBaseException):
    """预期错误异常。"""

    def __init__(self, message: str = "预期错误", *args: Any, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)


class ConfigError(LjpBaseException):
    """配置错误。"""

    def __init__(self, message: str = "配置错误", *args: Any, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)


class Notfound(LjpBaseException):
    """资源未找到异常。"""

    def __init__(
        self,
        message: str = "未找到资源",
        resource: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.resource = resource
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.resource is not None:
            msg += f" (资源: {self.resource})"
        return msg


class ParseError(LjpBaseException):
    """解析错误。"""

    def __init__(
        self,
        message: str = "数据解析失败",
        data_type: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.data_type = data_type
        if self.data_type is not None:
            message += f" (数据类型: {self.data_type})"
        super().__init__(message, *args, **kwargs)

class MeetCheckError(LjpBaseException):
    """反爬或风控检查异常。"""

    def __init__(
        self,
        message: str = "遇到反爬",
        check_type: str | None = None,
        url: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.check_type = check_type
        self.url = url
        if self.check_type is not None:
            message += f" (检测类型: {self.check_type})"
        if url is not None:
            message += f" (URL: {url})"
        super().__init__(message, *args, **kwargs)


class CaptchaException(LjpBaseException):
    """验证码异常。"""

    def __init__(
        self,
        message: str = "验证码识别失败",
        captcha_type: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.captcha_type = captcha_type
        if self.captcha_type is not None:
            message += f" (验证码类型: {self.captcha_type})"
        super().__init__(message, *args, **kwargs)


class NetworkException(LjpBaseException):
    """网络连接异常。"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        status_code: int | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.url = url
        self.status_code = status_code
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
        if self.status_code is not None:
            msg += f" (状态码: {self.status_code})"
        return msg


class TimeoutException(LjpBaseException):
    """超时异常。"""

    def __init__(
        self,
        message: str,
        timeout: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.timeout = timeout
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.timeout is not None:
            msg += f" (超时时间: {self.timeout}s)"
        return msg



class ResponseParseException(LjpBaseException):
    """响应解析异常。"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        parse_type: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.url = url
        self.parse_type = parse_type
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
        if self.parse_type is not None:
            msg += f" (解析类型: {self.parse_type})"
        return msg


ALL_EXCEPTIONS = (
    No,
    Yes,
    ConfigError,
    Notfound,
    ParseError,
    MeetCheckError,
    CaptchaException,
    NetworkException,
    TimeoutException,
    ResponseParseException,

)

__all__ = [
    "ALL_EXCEPTIONS",
    "CaptchaException",
    "ConfigError",
    "LjpBaseException",
    "MeetCheckError",
    "NetworkException",
    "No",
    "Notfound",
    "ParseError",
    "ResponseParseException",
    "TimeoutException",
    "Yes",
]
