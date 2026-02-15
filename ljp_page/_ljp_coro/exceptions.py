"""
LJP项目异常类定义
提供统一的异常处理体系，支持原始异常自动捕获和格式化
"""
class LjpBaseException(Exception):
    """LJP项目基础异常类

    所有LJP项目异常的基类，提供统一的异常格式化功能。
    自动捕获并格式化原始异常信息。
    """

    def __init__(self, message, f=None, e: Exception = None):
        self.e = e
        if f:
            message = f'({f.__name__}): {message}'

        super().__init__(message)

    def __str__(self):
        msg = super().__str__()
        if self.e:
            msg += f'==>{str(self.e)}'
        return msg

class No(LjpBaseException):
    def __init__(self, message='出错', *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class Yes(LjpBaseException):
    def __init__(self, message='预期错误', *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class ConfigError(LjpBaseException):
    """配置错误"""

    def __init__(self, message="配置错误", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class Notfound(LjpBaseException):
    """资源未找到异常"""

    def __init__(self, message="未找到资源", resource: str = None, *args, **kwargs):
        self.resource = resource
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.resource:
            msg += f" (资源: {self.resource})"
        return msg

class NetworkError(LjpBaseException):
    """网络相关错误（旧版，建议使用NetworkException）"""

    def __init__(self, message="网络连接错误", url: str = None, *args, **kwargs):
        self.url = url
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        return msg

class ParseError(LjpBaseException):
    """解析错误"""

    def __init__(self, message="数据解析失败", data_type: str = None, *args, **kwargs):
        self.data_type = data_type
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.data_type:
            msg += f" (数据类型: {self.data_type})"
        return msg

class MeetCheckError(LjpBaseException):
    """遇到反爬虫异常"""

    def __init__(self, message='遇到反爬虫', check_type: str = None,url=None, *args, **kwargs):
        self.check_type = check_type
        self.url = url
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.check_type:
            msg += f" (检测类型: {self.check_type},url:{self.url})"
        return msg


# ============== 请求相关异常类 ==============

class CaptchaException(LjpBaseException):
    """验证码异常"""

    def __init__(self, message="验证码识别失败", captcha_type: str = None, *args, **kwargs):
        self.captcha_type = captcha_type
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.captcha_type:
            msg += f" (验证码类型: {self.captcha_type})"
        return msg


class NetworkException(LjpBaseException):
    """网络连接异常（新版）"""

    def __init__(self, message, url: str = None, status_code: int = None, *args, **kwargs):
        self.url = url
        self.status_code = status_code
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        if self.status_code:
            msg += f" (状态码: {self.status_code})"
        return msg


class TimeoutException(LjpBaseException):
    """请求超时异常"""

    def __init__(self, message, url: str = None, timeout: float = None, *args, **kwargs):
        self.url = url
        self.timeout = timeout
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        if self.timeout:
            msg += f" (超时时间: {self.timeout}秒)"
        return msg


class ProxyException(LjpBaseException):
    """代理异常"""

    def __init__(self, message, proxy: str = None, *args, **kwargs):
        self.proxy = proxy
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.proxy:
            msg += f" (代理: {self.proxy})"
        return msg


class HTTPStatusException(NetworkException):
    """HTTP状态码异常"""

    def __init__(self, message, url: str = None, status_code: int = None, reason: str = None, *args, **kwargs):
        super().__init__(message, url=url, status_code=status_code, *args, **kwargs)
        self.reason = reason

    def __str__(self):
        msg = super().__str__()
        if self.reason:
            msg += f" (原因: {self.reason})"
        return msg


class EncodingException(LjpBaseException):
    """编码解码异常"""

    def __init__(self, message, url: str = None, encoding: str = None, *args, **kwargs):
        self.url = url
        self.encoding = encoding
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        if self.encoding:
            msg += f" (编码: {self.encoding})"
        return msg


class SSLException(LjpBaseException):
    """SSL证书异常"""

    def __init__(self, message, url: str = None, *args, **kwargs):
        self.url = url
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        return msg


class ResponseParseException(LjpBaseException):
    """响应解析异常"""

    def __init__(self, message, url: str = None, parse_type: str = None, *args, **kwargs):
        self.url = url
        self.parse_type = parse_type
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        if self.parse_type:
            msg += f" (解析类型: {self.parse_type})"
        return msg


class MaxRetriesException(LjpBaseException):
    """最大重试次数异常"""

    def __init__(self, message, url: str = None, max_retries: int = None, *args, **kwargs):
        self.url = url
        self.max_retries = max_retries
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        msg = super().__str__()
        if self.url:
            msg += f" (URL: {self.url})"
        if self.max_retries:
            msg += f" (最大重试次数: {self.max_retries})"
        return msg


# ============== 异常类元组 ==============



ALL_EXCEPTIONS = (
    No,
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
    MaxRetriesException
)


__all__ = [
    'LjpBaseException',
    'No',
    'ConfigError',
    'Notfound',
    'NetworkError',
    'ParseError',
    'MeetCheckError',
    'CaptchaException',
    'NetworkException',
    'TimeoutException',
    'ProxyException',
    'HTTPStatusException',
    'EncodingException',
    'SSLException',
    'ResponseParseException',
    'MaxRetriesException',
    'ALL_EXCEPTIONS',
]
