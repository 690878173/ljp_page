"""HAR 1.2 格式类型定义。

基于 HAR 1.2 规范：http://www.softwareishard.com/blog/har-12-spec/
这些 TypedDict 定义了用于以下目的的 HAR（HTTP 存档）文件的结构：
记录和重放网络流量。"""

from __future__ import annotations

from typing_extensions import NotRequired, TypedDict


class HarTimings(TypedDict):
    """有关请求/响应往返的时间信息。"""

    blocked: float
    dns: float
    connect: float
    ssl: float
    send: float
    wait: float
    receive: float


class HarCookie(TypedDict):
    """请求或响应中使用的 Cookie。"""

    name: str
    value: str
    path: NotRequired[str]
    domain: NotRequired[str]
    expires: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]


class HarHeader(TypedDict):
    """HTTP 标头名称-值对。"""

    name: str
    value: str


class HarQueryParam(TypedDict):
    """URL 查询字符串参数。"""

    name: str
    value: str


class HarPostData(TypedDict):
    """发布数据信息。"""

    mimeType: str
    text: str
    params: NotRequired[list[dict]]


class HarRequest(TypedDict):
    """有关请求的详细信息。"""

    method: str
    url: str
    httpVersion: str
    cookies: list[HarCookie]
    headers: list[HarHeader]
    queryString: list[HarQueryParam]
    headersSize: int
    bodySize: int
    postData: NotRequired[HarPostData]


class HarContent(TypedDict):
    """响应内容正文信息。"""

    size: int
    mimeType: str
    text: NotRequired[str]
    encoding: NotRequired[str]


class HarResponse(TypedDict):
    """有关响应的详细信息。"""

    status: int
    statusText: str
    httpVersion: str
    cookies: list[HarCookie]
    headers: list[HarHeader]
    content: HarContent
    redirectURL: str
    headersSize: int
    bodySize: int


class HarCache(TypedDict, total=False):
    """请求/响应对的缓存状态。"""

    beforeRequest: dict
    afterRequest: dict


class HarEntry(TypedDict):
    """表示导出的 HTTP 请求。"""

    startedDateTime: str
    time: float
    request: HarRequest
    response: HarResponse
    cache: HarCache
    timings: HarTimings
    serverIPAddress: NotRequired[str]
    connection: NotRequired[str]
    _resourceType: NotRequired[str]


class HarPage(TypedDict):
    """代表导出的页面。"""

    startedDateTime: str
    id: str
    title: str


class HarCreator(TypedDict):
    """有关 HAR 文件创建者的信息。"""

    name: str
    version: str


class HarLog(TypedDict):
    """HAR 数据的根。"""

    version: str
    creator: HarCreator
    pages: list[HarPage]
    entries: list[HarEntry]


class Har(TypedDict):
    """顶级 HAR 对象。"""

    log: HarLog
