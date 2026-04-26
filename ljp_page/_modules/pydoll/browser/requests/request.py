"""该模块提供了一个模仿请求行为的 Request 类。
它允许使用浏览器的 fetch API 发出 HTTP 请求。"""

from __future__ import annotations

import json as jsonlib

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from ljp_page._modules.pydoll.browser.requests.har_recorder import HarCapture, HarRecorder
from ljp_page._modules.pydoll.browser.requests.response import Response
from ljp_page._modules.pydoll.commands.runtime_commands import RuntimeCommands
from ljp_page._modules.pydoll.constants import Scripts
from ljp_page._modules.pydoll.exceptions import HTTPError
from ljp_page._modules.pydoll.protocol.fetch.types import HeaderEntry
from ljp_page._modules.pydoll.protocol.network.events import (
    NetworkEvent,
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
    ResponseReceivedExtraInfoEventParams,
)
from ljp_page._modules.pydoll.protocol.network.types import CookieParam, ResourceType

from ljp_page.logger import logger

RequestReceivedEvent = Union[
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
]
RequestSentEvent = Union[
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
]

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.browser.tab import Tab
    from ljp_page._modules.pydoll.protocol.network.events import (
        RequestWillBeSentEventParams,
        RequestWillBeSentExtraInfoEventParams,
        ResponseReceivedEventParams,
    )
    from ljp_page._modules.pydoll.protocol.runtime.methods import EvaluateResponse

    RequestReceivedEventParams = Union[
        ResponseReceivedEventParams,
        ResponseReceivedExtraInfoEventParams,
    ]
    RequestSentEventParams = Union[
        RequestWillBeSentEventParams,
        RequestWillBeSentExtraInfoEventParams,
    ]


class Request:
    """使用浏览器的 fetch API 发出 HTTP 请求的高级接口。

    该类提供了一个类似请求的接口，可以在
    浏览器的 JavaScript 上下文。所有请求都会继承浏览器的当前会话
    状态包括cookie、身份验证标头和其他自动浏览器
    行为。这允许与需要的网站进行无缝交互
    身份验证或具有复杂的 cookie 管理。

    主要特点：
    - 使用 fetch API 在浏览器的 JavaScript 上下文中执行请求
    - 自动包含浏览器cookie和会话状态
    - 保留浏览器的安全上下文和 CORS 策略
    - 捕获请求和响应标头以进行分析
    - 支持所有标准 HTTP 方法（GET、POST、PUT、DELETE 等）

    注意：
    - 传递给方法的标头是附加标头，而不是替换标头
    - 保留浏览器的自动标头（User-Agent、Accept 等）
    - Cookie 由浏览器自动管理"""

    def __init__(self, tab: Tab):
        """初始化绑定到浏览器选项卡的新 Request 实例。

        参数：
            tab：将执行请求的浏览器选项卡实例。
                该选项卡提供 JavaScript 执行上下文并维护
                浏览器的会话状态（cookie、身份验证等）。"""
        self.tab = tab
        self._network_events_enabled = False
        self._callback_ids: list[int] = []
        self._requests_sent: list[RequestSentEvent] = []
        self._requests_received: list[RequestReceivedEvent] = []
        logger.debug('Request helper initialized for tab')

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[dict[str, str]] = None,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[list[HeaderEntry]] = None,
        **kwargs,
    ) -> Response:
        """在浏览器的 JavaScript 上下文中执行 HTTP 请求。

        该方法使用浏览器的fetch API来发出请求，继承了所有
        浏览器会话状态包括 cookie、身份验证和安全上下文。
        该请求的执行就像浏览器本身发出的一样。

        参数：
            method：HTTP 方法（GET、POST、PUT、DELETE 等）。不区分大小写。
            url：请求的目标 URL。可以是相对的或绝对的。
            params：附加到 URL 的查询参数。这些是 URL 编码的
                并与 URL 中任何现有的查询字符串合并。
            data：请求主体数据。行为取决于类型：
                - dict/list/tuple：URL 编码为表单数据 (application/x-www-form-urlencoded)
                - str/bytes：按原样发送，没有内容类型修改
                与“json”参数互斥。
            json：要 JSON 序列化为请求正文的数据。自动设置
                内容类型为 application/json。与“数据”互斥。
            headers：要包含的附加标头。这些已添加到浏览器的
                自动标题，而不是替换。
                格式：[{'名称': 'X-Custom', '值': '值'}]
            **kwargs：其他获取 API 选项（例如，凭据、模式、缓存）。

        返回：
            包含状态、标头、内容和 cookie 的响应对象
            请求和响应阶段。

        加薪：
            HTTPError：如果请求执行失败或者发生网络错误。

        注意：
            - 自动包含浏览器cookie
            - CORS 策略由浏览器强制执行
            - 身份验证标头从浏览器会话中保留"""
        final_url = self._build_url_with_params(url, params)
        options = self._build_request_options(method, headers, json, data, **kwargs)
        logger.info(f'Executing request: method={method.upper()}, url={final_url}')
        logger.debug(
            f'Executing request: method={method.upper()}, url={final_url}, '
            f'headers={bool(headers)}, json={json is not None}, data={data is not None}'
        )
        try:
            result = await self._execute_fetch_request(final_url, options)
            received_headers = self._extract_received_headers()
            sent_headers = self._extract_sent_headers()
            cookies = self._extract_set_cookies()
            return self._build_response(result, received_headers, sent_headers, cookies)

        except Exception as exc:
            logger.error(f'Request failed: {exc}')
            raise HTTPError(f'Request failed: {str(exc)}') from exc

        finally:
            await self._clear_callbacks()

    async def get(
        self,
        url: str,
        params: Optional[dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        """执行 GET 请求以检索数据。

        参数：
            url：从中检索数据的目标 URL。
            params：附加到 URL 的查询参数。
            **kwargs：附加获取选项。

        返回：
            包含检索到的数据的响应对象。"""
        return await self.request('GET', url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> Response:
        """执行 POST 请求以创建或提交数据。

        参数：
            url：数据提交的目标URL。
            data：要提交的表单数据（URL 编码）。
            json：要提交的 JSON 数据。
            **kwargs：附加获取选项。

        返回：
            响应对象包含服务器对提交的响应。"""
        return await self.request('POST', url, data=data, json=json, **kwargs)

    async def put(
        self,
        url: str,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> Response:
        """执行 PUT 请求以更新/替换资源。

        参数：
            url：要更新的资源的目标 URL。
            data：用于更新的表单数据。
            json：用于更新的 JSON 数据。
            **kwargs：附加获取选项。

        返回：
            确认更新操作的响应对象。"""
        return await self.request('PUT', url, data=data, json=json, **kwargs)

    async def patch(
        self,
        url: str,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> Response:
        """执行部分资源更新的 PATCH 请求。

        参数：
            url：要部分更新的资源的目标 URL。
            数据：要应用更改的表单数据。
            json：要应用更改的 JSON 数据。
            **kwargs：附加获取选项。

        返回：
            确认部分更新的响应对象。"""
        return await self.request('PATCH', url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs) -> Response:
        """执行删除资源的 DELETE 请求。

        参数：
            url：要删除的资源的目标 URL。
            **kwargs：附加获取选项。

        返回：
            确认删除的响应对象。"""
        return await self.request('DELETE', url, **kwargs)

    async def head(self, url: str, **kwargs) -> Response:
        """执行 HEAD 请求以仅检索响应标头。

        对于检查资源是否存在、大小或修改日期很有用
        无需下载完整内容。

        参数：
            url：要检查标头的目标 URL。
            **kwargs：附加获取选项。

        返回：
            具有标头但没有正文内容的响应对象。"""
        return await self.request('HEAD', url, **kwargs)

    async def options(self, url: str, **kwargs) -> Response:
        """执行 OPTIONS 请求以检查允许的方法和功能。

        用于 CORS 预检检查和发现服务器功能。

        参数：
            url：要检查选项的目标 URL。
            **kwargs：附加获取选项。

        返回：
            具有允许的方法和 CORS 标头的响应对象。"""
        return await self.request('OPTIONS', url, **kwargs)

    @asynccontextmanager
    async def record(
        self,
        resource_types: list[ResourceType] | None = None,
    ) -> AsyncIterator[HarCapture]:
        """将网络流量记录为 HAR。

        捕获选项卡上所有网络活动的上下文管理器
        并生成一个 HarCapture 对象以供导出。

        参数：
            resource_types：要捕获的资源类型的可选列表。
                提供后，仅匹配这些类型的请求
                记录了。当无（默认）时，所有资源类型都是
                被捕获。

        用法::

            与 tab.request.record() 异步作为捕获：
                等待 tab.go_to('https://example.com')
            capture.save('流.har')

            # 只记录 fetch 和 XHR 请求
            与 tab.request.record( 异步
                resource_types=[资源类型.FETCH, 资源类型.XHR]
            ) 作为捕获：
                等待 tab.go_to('https://example.com')
            capture.save('api_calls.har')

        产量：
            HarCapture：带有 .save()、.to_dict() 和 .entries 的对象。"""
        recorder = HarRecorder(self.tab, resource_types=resource_types)
        capture = HarCapture(recorder)
        await recorder.start()
        try:
            yield capture
        finally:
            await recorder.stop()

    @staticmethod
    def _build_url_with_params(url: str, params: Optional[dict[str, str]]) -> str:
        """使用查询参数构建最终 URL。"""
        logger.debug(f'Building URL with params: url={url}, params={params}')
        if not params:
            return url

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key, value in params.items():
            query[key] = [value]

        return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    def _build_request_options(
        self,
        method: str,
        headers: Optional[list[HeaderEntry]],
        json: Optional[dict[str, Any]],
        data: Optional[Union[dict, list, tuple, str, bytes]],
        **kwargs,
    ) -> dict[str, Any]:
        """构建请求选项字典。"""
        headers_dict = self._convert_header_entries_to_dict(headers) if headers else {}
        options = {
            'method': method.upper(),
            'headers': headers_dict,
            **kwargs,
        }
        logger.debug(f'Building request options: options={options}')
        self._add_request_body(options, json, data)
        return options

    def _add_request_body(
        self,
        options: dict[str, Any],
        json: Optional[dict[str, Any]],
        data: Optional[Union[dict, list, tuple, str, bytes]],
    ) -> None:
        """添加请求正文和适当的 Content-Type 标头。"""
        if json is not None:
            self._handle_json_options(options, json)
        elif data is not None:
            self._handle_data_options(options, data)

    @staticmethod
    def _handle_json_options(options: dict[str, Any], json: Optional[dict[str, Any]]) -> None:
        """处理 JSON 选项。"""
        options['body'] = jsonlib.dumps(json)
        options['headers'].setdefault('Content-Type', 'application/json')
        logger.debug('Request JSON body set and content-type applied')

    @staticmethod
    def _handle_data_options(
        options: dict[str, Any], data: Optional[Union[dict, list, tuple, str, bytes]]
    ) -> None:
        """处理数据选项。"""
        if isinstance(data, (dict, list, tuple)):
            options['body'] = urlencode(data, doseq=True)
            options['headers'].setdefault('Content-Type', 'application/x-www-form-urlencoded')
            logger.debug('Request data encoded as form-urlencoded')
        else:
            options['body'] = data
            logger.debug('Request data set as raw payload')

    async def _execute_fetch_request(self, url: str, options: dict[str, Any]) -> EvaluateResponse:
        """使用浏览器的运行时执行获取请求。"""
        script = Scripts.MAKE_REQUEST.format(url=jsonlib.dumps(url), options=jsonlib.dumps(options))
        await self._register_callbacks()
        logger.debug('Registered network callbacks and executing fetch via Runtime.evaluate')

        return await self.tab._execute_command(
            RuntimeCommands.evaluate(
                expression=script,
                return_by_value=True,
                await_promise=True,
            )
        )

    @staticmethod
    def _build_response(
        result: EvaluateResponse,
        response_headers: list[HeaderEntry],
        request_headers: list[HeaderEntry],
        cookies: list[CookieParam],
    ) -> Response:
        """从获取结果构建 Response 对象。"""
        result_value = result['result']['result']['value']
        logger.debug(f'Building response: result_value={result_value}')
        return Response(
            status_code=result_value['status'],
            content=bytes(result_value.get('content', b'')),
            text=result_value['text'],
            json=result_value['json'],
            response_headers=response_headers,
            request_headers=request_headers,
            cookies=cookies,
            url=result_value['url'],
        )

    async def _register_callbacks(self) -> None:
        """注册网络事件侦听器以捕获请求/响应元数据。

        设置 CDP 事件侦听器以捕获期间的所有网络活动
        请求执行。这包括传出请求数据和传入请求数据
        响应数据，用于标头和 cookie 提取。

        注意：
            仅当选项卡上尚未激活网络事件时，才会启用网络事件。"""
        if not self.tab.network_events_enabled:
            await self.tab.enable_network_events()
            self._network_events_enabled = True
            logger.debug('Network events enabled on tab for request capture')

        def append_received_request(event: dict) -> None:
            self._requests_received.append(cast(RequestReceivedEvent, event))
            logger.debug(f'Appended received request: event={event}')

        def append_sent_request(event: dict) -> None:
            self._requests_sent.append(cast(RequestSentEvent, event))
            logger.debug(f'Appended sent request: event={event}')

        self._callback_ids = [
            await self.tab.on(
                NetworkEvent.REQUEST_WILL_BE_SENT,
                callback=append_sent_request,
            ),
            await self.tab.on(
                NetworkEvent.REQUEST_WILL_BE_SENT_EXTRA_INFO,
                callback=append_sent_request,
            ),
            await self.tab.on(
                NetworkEvent.RESPONSE_RECEIVED,
                callback=append_received_request,
            ),
            await self.tab.on(
                NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO,
                callback=append_received_request,
            ),
        ]

    async def _clear_callbacks(self) -> None:
        """清理网络事件侦听器并禁用网络监控。

        仅删除此请求实例注册的回调
        （手术切除）所以其他听众（例如 HarRecorder）
        不受影响。"""
        for callback_id in self._callback_ids:
            await self.tab.remove_callback(callback_id)
        self._callback_ids.clear()
        if self._network_events_enabled:
            await self.tab.disable_network_events()
            self._network_events_enabled = False
            logger.debug('Network events disabled on tab after request')

    def _extract_received_headers(self) -> list[HeaderEntry]:
        """从响应网络事件中提取标头。

        返回：
            响应期间从服务器收到的标头列表。"""
        event_extractors: dict[str, Callable[[Any], list[HeaderEntry]]] = {
            'response': self._extract_response_received_headers,
            'blockedCookies': self._extract_response_received_extra_info_headers,
        }

        return self._extract_headers_from_events(self._requests_received, event_extractors)

    def _extract_sent_headers(self) -> list[HeaderEntry]:
        """从请求网络事件中提取标头。

        返回：
            请求中实际发送的标头列表。"""
        event_extractors: dict[str, Callable[[Any], list[HeaderEntry]]] = {
            'request': self._extract_request_sent_headers,
            'associatedCookies': self._extract_request_sent_extra_info_headers,
        }

        return self._extract_headers_from_events(self._requests_sent, event_extractors)

    @staticmethod
    def _extract_headers_from_events(
        events: Union[list[RequestSentEvent], list[RequestReceivedEvent]],
        event_extractors: dict[str, Callable[[Any], list[HeaderEntry]]],
    ) -> list[HeaderEntry]:
        """使用适当的提取器从网络事件中提取标头。

        参数：
            events：要处理的网络事件列表。
            event_extractors：事件键到标头提取函数的映射。

        返回：
            所有匹配事件中的头的重复数据列表。

        注意：
            根据名称/值对对标头进行重复数据删除，以避免
            来自多个事件类型的重复条目。"""
        headers: list[HeaderEntry] = []
        seen = set()
        logger.debug(f'Extracting headers from events: events={events}')
        for event in events:
            params = event['params']
            for key, extractor in event_extractors.items():
                if key in params:
                    extracted_headers = extractor(params)
                    logger.debug(f'Extracted headers: extracted_headers={extracted_headers}')
                    for header in extracted_headers:
                        identity = (header['name'], header['value'])
                        logger.debug(f'Identity: identity={identity}')
                        if identity not in seen:
                            headers.append(header)
                            seen.add(identity)
                            logger.debug(f'Added header: header={header}')
                    break

        logger.debug(f'Headers extracted: headers={headers}')
        return headers

    def _extract_request_sent_headers(
        self, params: RequestWillBeSentEventParams
    ) -> list[HeaderEntry]:
        """从主请求事件中提取标头。

        参数：
            params：包含请求详细信息的事件参数。

        返回：
            随请求发送的标头列表。"""
        request = params['request']
        logger.debug(f'Extracting request sent headers: request={request}')
        return self._convert_dict_to_header_entries(request.get('headers', {}))

    def _extract_request_sent_extra_info_headers(
        self, params: RequestWillBeSentExtraInfoEventParams
    ) -> list[HeaderEntry]:
        """从额外请求信息事件中提取标头。

        此事件包含可能不包含的附加标头信息
        存在于主要请求事件中，例如与安全相关的标头。

        参数：
            params：包含附加标头的额外信息事件参数。

        返回：
            随请求发送的附加标头列表。"""
        logger.debug(f'Extracting request sent extra info headers: params={params}')
        return self._convert_dict_to_header_entries(params.get('headers', {}))

    def _extract_response_received_headers(
        self, params: ResponseReceivedEventParams
    ) -> list[HeaderEntry]:
        """从主响应事件中提取标头。

        参数：
            params：包含响应详细信息的事件参数。

        返回：
            从服务器接收的标头列表。"""
        response = params['response']
        logger.debug(f'Extracting response received headers: response={response}')
        return self._convert_dict_to_header_entries(response.get('headers', {}))

    def _extract_response_received_extra_info_headers(
        self, params: ResponseReceivedExtraInfoEventParams
    ) -> list[HeaderEntry]:
        """从额外响应信息事件中提取标头。

        该事件包含额外的响应头信息，包括
        Set-Cookie 标头和可能被过滤的安全相关标头
        来自主要响应事件。

        参数：
            params：包含附加标头的额外信息事件参数。

        返回：
            从服务器接收的附加标头列表。"""
        logger.debug(f'Extracting response received extra info headers: params={params}')
        return self._convert_dict_to_header_entries(params.get('headers', {}))

    @staticmethod
    def _convert_dict_to_header_entries(headers_dict: dict) -> list[HeaderEntry]:
        """将标头字典转换为标准化的 HeaderEntry 格式。

        参数：
            headers_dict：将标头名称映射到值的字典。

        返回：
            具有“name”和“value”键的 HeaderEntry 对象列表。"""
        logger.debug(f'Converting dictionary to header entries: headers_dict={headers_dict}')
        return [HeaderEntry(name=name, value=value) for name, value in headers_dict.items()]

    def _extract_set_cookies(self) -> list[CookieParam]:
        """从响应事件中提取并解析所有 Set-Cookie 标头。

        处理响应事件以查找 Set-Cookie 标头并转换它们
        到结构化 cookie 对象中。处理多个 Set-Cookie 标头
        和多行 cookie 声明。

        返回：
            从 Set-Cookie 标头中提取的唯一 cookie 列表。"""
        cookies: list[CookieParam] = []
        logger.debug(f'Extracting set cookies: cookies={cookies}')
        response_extra_info_events = self._filter_response_extra_info_events()
        logger.debug(
            f'Filtering response extra info events: '
            f'response_extra_info_events={response_extra_info_events}'
        )
        for event in response_extra_info_events:
            params = cast(ResponseReceivedExtraInfoEventParams, event['params'])
            headers = self._convert_dict_to_header_entries(params['headers'])
            logger.debug(f'Converting dictionary to header entries: headers={headers}')
            set_cookie_headers = [
                header['value'] for header in headers if header['name'] == 'Set-Cookie'
            ]
            logger.debug(f'Set cookie headers: set_cookie_headers={set_cookie_headers}')
            if set_cookie_headers:
                for set_cookie_header in set_cookie_headers:
                    self._add_unique_cookies(
                        cookies, self._parse_set_cookie_header(set_cookie_header)
                    )
        logger.debug(f'Set cookies extracted: cookies={cookies}')
        return cookies

    def _filter_response_extra_info_events(self) -> list[RequestReceivedEvent]:
        """过滤网络事件以查找包含 Set-Cookie 信息的网络事件。

        返回：
            包含额外响应信息（包括 cookie）的事件列表。"""
        logger.debug(
            f'Filtering response extra info events: requests_received={self._requests_received}'
        )
        return [
            event
            for event in self._requests_received
            if event['method'] == NetworkEvent.RESPONSE_RECEIVED_EXTRA_INFO
        ]

    def _parse_set_cookie_header(self, set_cookie_header: str) -> list[CookieParam]:
        """将 Set-Cookie 标头值解析为单独的 cookie 对象。

        处理单行和多行 Set-Cookie 标头，提取
        cookie 名称-值对，同时忽略路径、域等属性。

        参数：
            set_cookie_header：来自 HTTP 响应的原始 Set-Cookie 标头值。

        返回：
            包含名称和值的已解析 cookie 对象列表。"""
        cookies = []
        lines = set_cookie_header.split('\n')
        logger.debug(f'Parsing set cookie header: set_cookie_header={set_cookie_header}')
        for line in lines:
            cookie = self._parse_cookie_line(line)
            if cookie:
                logger.debug(f'Parsed cookie: cookie={cookie}')
                cookies.append(cookie)
        logger.debug(f'Parsed cookies: cookies={cookies}')
        return cookies

    @staticmethod
    def _parse_cookie_line(line: str) -> Optional[CookieParam]:
        """解析单个 cookie 行以提取名称和值。

        仅提取 cookie 名称和值，忽略所有 cookie 属性
        例如 Path、Domain、Secure、HttpOnly 等。拒绝名称为空的 cookie。

        参数：
            line：来自 Set-Cookie 标头的单行。

        返回：
            带有名称和值的 CookieParam 对象，如果解析失败或名称为空，则为 None 。"""
        if '=' not in line:
            return None

        name = line.split('=', 1)[0].strip()
        value = line.split('=', 1)[1].split(';', 1)[0].strip()

        #拒绝名称为空的 cookie
        if not name:
            return None

        return CookieParam(name=name, value=value)

    @staticmethod
    def _add_unique_cookies(cookies: list[CookieParam], new_cookies: list[CookieParam]) -> None:
        """将 cookie 添加到列表中，同时避免重复。

        参数：
            cookies：要添加到的现有 cookie 列表。
            new_cookies：要添加的新 cookie（如果尚未存在）。"""
        logger.debug(f'Adding unique cookies: cookies={cookies}, new_cookies={new_cookies}')
        for cookie in new_cookies:
            if cookie not in cookies:
                cookies.append(cookie)
                logger.debug(f'Added unique cookie: cookie={cookie}')
        logger.debug(f'Unique cookies added: cookies={cookies}')

    @staticmethod
    def _convert_header_entries_to_dict(headers: list[HeaderEntry]) -> dict[str, str]:
        """将 HeaderEntry 对象转换为普通字典格式。

        用于为 JavaScript fetch API 准备标头，该 API 需要
        将标头名称映射到值的简单对象。

        参数：
            headers：带有“name”和“value”键的 HeaderEntry 对象列表。

        返回：
            将标头名称映射到值的字典。"""
        logger.debug(f'Converting header entries to dictionary: headers={headers}')
        return {header['name']: header['value'] for header in headers}
