# 04-01-20-05-00
"""项目全局异常定义。"""

from __future__ import annotations

from typing import Any


class LjpBaseException(Exception):
    """项目全局唯一自定义异常基类。"""

    def __init__(self, message: str, f: Any = None, e: Exception | None = None) -> None:
        self.e = e
        if f is not None:
            message = f"({getattr(f, '__name__', str(f))}): {message}"
        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()
        if self.e is None:
            return base
        return f"{base}==>{self.e}"


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


class NetworkError(LjpBaseException):
    """网络相关错误（旧版本，建议使用 NetworkException）。"""

    def __init__(
        self,
        message: str = "网络连接错误",
        url: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.url = url
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
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
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.data_type is not None:
            msg += f" (数据类型: {self.data_type})"
        return msg


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
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.check_type is not None:
            msg += f" (检测类型: {self.check_type}, url: {self.url})"
        return msg


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
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.captcha_type is not None:
            msg += f" (验证码类型: {self.captcha_type})"
        return msg


class NetworkException(LjpBaseException):
    """网络连接异常（新版本）。"""

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
    """请求超时异常。"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        timeout: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.url = url
        self.timeout = timeout
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
        if self.timeout is not None:
            msg += f" (超时时间: {self.timeout}s)"
        return msg


class ProxyException(LjpBaseException):
    """代理异常。"""

    def __init__(self, message: str, proxy: str | None = None, *args: Any, **kwargs: Any) -> None:
        self.proxy = proxy
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.proxy is not None:
            msg += f" (代理: {self.proxy})"
        return msg


class HTTPStatusException(NetworkException):
    """HTTP 状态码异常。"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        status_code: int | None = None,
        reason: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, url=url, status_code=status_code, *args, **kwargs)
        self.reason = reason

    def __str__(self) -> str:
        msg = super().__str__()
        if self.reason is not None:
            msg += f" (原因: {self.reason})"
        return msg


class EncodingException(LjpBaseException):
    """编码解码异常。"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        encoding: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.url = url
        self.encoding = encoding
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
        if self.encoding is not None:
            msg += f" (编码: {self.encoding})"
        return msg


class SSLException(LjpBaseException):
    """SSL 证书异常。"""

    def __init__(self, message: str, url: str | None = None, *args: Any, **kwargs: Any) -> None:
        self.url = url
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
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


class MaxRetriesException(LjpBaseException):
    """达到最大重试次数异常。"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        max_retries: int | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.url = url
        self.max_retries = max_retries
        super().__init__(message, *args, **kwargs)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.url is not None:
            msg += f" (URL: {self.url})"
        if self.max_retries is not None:
            msg += f" (最大重试次数: {self.max_retries})"
        return msg


class LjpRequestException(LjpBaseException):
    """请求链路异常，附带 trace_id 等上下文。"""

    def __init__(
        self,
        message: str,
        *,
        trace_id: str,
        method: str,
        url: str,
        category: str,
        retries: int = 0,
        elapsed: float | None = None,
        status_code: int | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        self.trace_id = trace_id
        self.method = method
        self.url = url
        self.category = category
        self.retries = retries
        self.elapsed = elapsed
        self.status_code = status_code
        self.original_exception = original_exception
        super().__init__(message, e=original_exception)

    def __str__(self) -> str:
        parts = [
            super().__str__(),
            f"trace_id={self.trace_id}",
            f"method={self.method}",
            f"url={self.url}",
            f"category={self.category}",
            f"retries={self.retries}",
        ]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.elapsed is not None:
            parts.append(f"elapsed={self.elapsed:.4f}s")
        return " | ".join(parts)


ALL_EXCEPTIONS = (
    No,
    Yes,
    ConfigError,
    Notfound,
    NetworkError,
    ParseError,
    MeetCheckError,
    CaptchaException,
    NetworkException,
    TimeoutException,
    ProxyException,
    HTTPStatusException,
    EncodingException,
    SSLException,
    ResponseParseException,
    MaxRetriesException,
    LjpRequestException,
)

__all__ = [
    "ALL_EXCEPTIONS",
    "CaptchaException",
    "ConfigError",
    "EncodingException",
    "HTTPStatusException",
    "LjpBaseException",
    "LjpRequestException",
    "MaxRetriesException",
    "MeetCheckError",
    "NetworkError",
    "NetworkException",
    "No",
    "Notfound",
    "ParseError",
    "ProxyException",
    "ResponseParseException",
    "SSLException",
    "TimeoutException",
    "Yes",
]
