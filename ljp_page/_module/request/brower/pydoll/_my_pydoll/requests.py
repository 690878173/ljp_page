from __future__ import annotations

import json as jsonlib

from typing import TYPE_CHECKING, Any, Optional, Union

from ljp_page._module.request.brower.pydoll.browser.requests.response import Response
from ljp_page._module.request.brower.pydoll import RuntimeCommands
from ljp_page._module.request.brower.pydoll import Scripts
from ljp_page._module.request.brower.pydoll.exceptions import HTTPError
from fetch.types import HeaderEntry
from network.events import (
    RequestWillBeSentEvent,
    RequestWillBeSentExtraInfoEvent,
    ResponseReceivedEvent,
    ResponseReceivedExtraInfoEvent,
    ResponseReceivedExtraInfoEventParams,
)
from network.types import CookieParam

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
    from network.events import (
        RequestWillBeSentEventParams,
        RequestWillBeSentExtraInfoEventParams,
        ResponseReceivedEventParams,
    )
    from runtime.methods import EvaluateResponse

    RequestReceivedEventParams = Union[
        ResponseReceivedEventParams,
        ResponseReceivedExtraInfoEventParams,
    ]
    RequestSentEventParams = Union[
        RequestWillBeSentEventParams,
        RequestWillBeSentExtraInfoEventParams,
    ]

from ljp_page._module.request.brower.pydoll.browser.requests import Request as _Request

class Request(_Request):

    async def _execute_fetch_request(self, url: str, options: dict[str, Any]) -> EvaluateResponse:
        """使用浏览器的运行时执行获取请求。"""
        script = Scripts.MAKE_REQUEST.format(url=jsonlib.dumps(url), options=jsonlib.dumps(options))
        await self._register_callbacks()

        return await self.tab._execute_command(
            RuntimeCommands.evaluate(
                expression=script,
                return_by_value=True,
                await_promise=True,
            )
        )

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[dict[str, str]] = None,
        data: Optional[Union[dict, list, tuple, str, bytes]] = None,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[list[HeaderEntry]] = None,
        *,
        if_ky=False,
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
        try:
            result = await self._execute_fetch_request(final_url, options)
            received_headers = self._extract_received_headers()
            sent_headers = self._extract_sent_headers()
            cookies = self._extract_set_cookies()
            return self._build_response(result, received_headers, sent_headers, cookies)

        except Exception as exc:
            logger.error(f'Request failed: {exc}')
            raise HTTPError(f': {str(exc)}') from exc

        finally:
            await self._clear_callbacks()

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
        if 'error' in result_value:
            return Response(
                status_code = 777,
                content = bytes(result_value.get('content')) if result_value.get('content') else None,
                text = result_value.get('text', None),
                json = result_value.get('json', None),
                response_headers = response_headers,
                request_headers = request_headers,
                cookies = cookies,
                url = result_value.get(u'url', None),
            )
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



__all__ = [
    'Request'
]
