from __future__ import annotations

import json as jsonlib

from typing import TYPE_CHECKING, Any, Optional, Union

from ljp_page._module.request.brower.pydoll.exceptions import HTTPError

__all__ = ['Response']

if TYPE_CHECKING:
    from fetch.types import HeaderEntry
    from network.types import CookieParam

from ljp_page.logger import loguru_logger

STATUS_CODE_RANGE_OK = range(200, 400)


class Response:
    """基于浏览器的获取请求的 HTTP 响应对象。

    此类提供了处理 HTTP 响应的标准化接口
    通过浏览器的fetch API获取。它模仿 requests.Response
    界面，同时保留所有浏览器特定的元数据，包括cookie，
    标头和网络计时信息。

    主要特点：
    - 兼容requests.Response API，方便迁移
    - 保留请求和响应标头以供分析
    - 从 Set-Cookie 标头中自动提取 cookie
    - 带缓存的惰性 JSON 解析
    - 浏览器上下文感知（尊重 CORS、安全策略）
    - 内容有多种格式（文本、字节、JSON）

    响应包含浏览器执行获取期间捕获的所有数据，
    包括重定向、身份验证流程和任何浏览器应用的转换。"""

    def __init__(
        self,
        status_code: int,
        content: bytes = b'',
        text: str = '',
        json: Optional[dict[str, Any]] = None,
        response_headers: Optional[list[HeaderEntry]] = None,
        request_headers: Optional[list[HeaderEntry]] = None,
        cookies: Optional[list[CookieParam]] = None,
        url: str = '',
    ):
        """使用浏览器获取结果初始化一个新的 Response 实例。

        参数：
            status_code：服务器返回的 HTTP 状态代码（例如 200、404、500）。
            内容：原始响应正文（以字节为单位）。用于二进制数据或当
                文本编码是不确定的。
            text：响应正文作为解码字符串。由浏览器的 fetch API 预先解码。
            json：如果响应 Content-Type 为 application/json，则预解析的 JSON 数据。
                如果没有， json() 方法将尝试根据需要解析文本。
            response_headers：从服务器接收到的标头，包括Set-Cookie，
                Content-Type 以及服务器发送的任何自定义标头。
            request_headers：请求中实际发送的标头，包括
                浏览器生成的标头（User-Agent、Accept 等）和自定义标头。
            cookies：响应期间从 Set-Cookie 标头中提取的 Cookie。
                这些代表来自此特定请求的新的/更新的 cookie。
            url：任何重定向后的最终 URL。可能与原始请求 URL 不同
                如果服务器在请求期间执行重定向。"""
        self._status_code = status_code
        self._content = content
        self._text = text
        self._json = json
        self._response_headers = response_headers or []
        self._request_headers = request_headers or []
        self._cookies = cookies or []
        self._url = url
        self._ok = status_code in STATUS_CODE_RANGE_OK
    @property
    def ok(self) -> bool:
        """检查请求是否成功（2xx 状态代码）。

        返回：
            如果状态代码在 200-399 范围内，则为 True，否则为 False。

        注意：
            这遵循 HTTP 约定，其中 2xx 代码表示成功
            和 3xx 代码表示重定向（仍被视为“正常”）。"""
        return self._ok

    @property
    def cookies(self) -> list[CookieParam]:
        """获取服务器在此响应期间设置的 cookie。

        返回：
            从 Set-Cookie 标头中提取的 cookie 列表。每个饼干
            包含名称和值，以及 cookie 属性（路径、域等）
            由浏览器自动处理。

        注意：
            这些只是此响应中的新/更新的 cookie。现有
            浏览器 cookie 由浏览器上下文自动管理。"""
        return self._cookies

    @property
    def request_headers(self) -> list[HeaderEntry]:
        """获取 HTTP 请求中实际发送的标头。

        返回：
            发送到服务器的标头列表，包括两个自定义标头
            由用户提供和浏览器自动添加的标头
            （用户代理、接受、授权等）。

        注意：
            这显示了发送的实际标头，这可能与实际标头不同
            最初是由于浏览器修改而指定的。"""
        return self._request_headers

    @property
    def headers(self) -> list[HeaderEntry]:
        """获取 HTTP 响应中从服务器收到的标头。

        返回：
            服务器发送的响应头列表，包括标准
            标头（内容类型、内容长度等）和任何自定义标头。

        注意：
            一些安全敏感的标头可能会被浏览器过滤
            由于 CORS 政策，不会出现在此列表中。"""
        return self._response_headers

    @property
    def status_code(self) -> int:
        """获取服务器返回的HTTP状态码。

        返回：
            整数状态代码（例如，200 表示正常，404 表示未找到，500 表示服务器错误）。"""
        return self._status_code

    @property
    def text(self) -> str:
        """获取解码字符串形式的响应内容。

        返回：
            响应正文解码为 UTF-8 字符串。如果没有提供文字
            在初始化期间，它将从原始内容中解码。

        注意：
            解码使用“替换”错误处理以避免崩溃
            无效的 UTF-8 序列。"""
        if not self._text and self.content:
            self._text = self.content.decode('utf-8', errors='replace')
        return self._text

    @property
    def content(self) -> bytes:
        """获取原始响应内容（以字节为单位）。

        返回：
            未修改的响应正文（以字节为单位）。对于二进制数据有用
            （图像、文件等）或当您需要手动处理编码时。"""
        return self._content

    @property
    def url(self) -> str:
        """获取任何重定向后响应的最终 URL。

        返回：
            最终访问的 URL，可能与实际访问的 URL 不同
            如果发生重定向，则为原始请求 URL。"""
        return self._url

    def json(self) -> Union[dict[str, Any], list]:
        """解析并以 JSON 数据形式返回响应内容。

        尝试将响应文本解析为 JSON。使用缓存来避免
        多次重新解析相同的内容。

        返回：
            将 JSON 数据解析为字典、列表或其他 JSON 兼容类型。

        加薪：
            ValueError：如果响应内容不是有效的 JSON 或者解析失败。

        注意：
            - 使用惰性解析：JSON 仅在首次访问时解析
            - 后续调用返回缓存结果以获得更好的性能
            - 如果在初始化期间预先解析了 JSON，则返回该结果"""
        if self._json is not None:
            return self._json

        try:
            self._json = jsonlib.loads(self.text)
            return self._json
        except jsonlib.JSONDecodeError as exc:
            loguru_logger.debug('Failed to decode response as JSON')
            raise ValueError('Response is not valid JSON') from exc

    def raise_for_status(self) -> None:
        """如果响应指示 HTTP 错误状态，则引发 HTTPError。

        检查状态代码并引发客户端错误异常 (4xx)
        和服务器错误 (5xx)。成功响应 (2xx) 和重定向 (3xx)
        不要引发异常。

        加薪：
            HTTPError：如果状态代码为 400 或更高，则表明发生错误。

        注意：
            此方法与 requests.Response.raise_for_status() 兼容
            以便从请求库轻松迁移。"""
        if self.status_code not in STATUS_CODE_RANGE_OK:
            loguru_logger.error(
                f'HTTP error status encountered: status={self.status_code}, url={self._url}'
            )
            raise HTTPError(f'{self.status_code} Client Error: for url {self._url}')
