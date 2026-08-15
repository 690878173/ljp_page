from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ljp_page._module.request.brower.base.protocol.base import Command
from ljp_page._module.request.brower.base.protocol.fetch.methods import (
    AuthChallengeResponse,
    ContinueRequestParams,
    ContinueResponseParams,
    ContinueWithAuthParams,
    EnableParams,
    FailRequestParams,
    FetchMethod,
    FulfillRequestParams,
    GetResponseBodyParams,
    TakeResponseBodyAsStreamParams,
)
from ljp_page._module.request.brower.base.protocol.fetch.types import RequestPattern

__all__ = ['FetchCommands']

if TYPE_CHECKING:
    from ljp_page._module.request.brower.base.protocol.fetch.methods import (
        ContinueRequestCommand,
        ContinueResponseCommand,
        ContinueWithAuthCommand,
        DisableCommand,
        EnableCommand,
        FailRequestCommand,
        FulfillRequestCommand,
        GetResponseBodyCommand,
        TakeResponseBodyAsStreamCommand,
    )
    from ljp_page._module.request.brower.base.protocol.fetch.types import (
        AuthChallengeResponseType,
        HeaderEntry,
        RequestStage,
        ResourceType,
    )
    from ljp_page._module.request.brower.base.protocol.network.types import ErrorReason, RequestMethod


class FetchCommands:
    """此类封装了 Chrome DevTools 协议 (CDP) 的获取命令。

    CDP的Fetch域允许拦截和修改网络请求
    在应用层。这使得开发人员能够检查、修改和
    控制网络流量，这对于测试、调试、
    和先进的自动化场景。

    此类中定义的命令提供以下功能：
    - 启用和禁用获取请求拦截
    - 继续、履行或失败拦截的请求
    - 处理身份验证挑战
    - 检索和修改响应主体
    - 将响应数据作为流处理"""

    @staticmethod
    def continue_request(
        request_id: str,
        url: Optional[str] = None,
        method: Optional['RequestMethod'] = None,
        post_data: Optional[str] = None,
        headers: Optional[list['HeaderEntry']] = None,
        intercept_response: Optional[bool] = None,
    ) -> ContinueRequestCommand:
        """创建一个命令来继续暂停的获取请求。

        此命令允许浏览器恢复已执行的获取操作
        被拦截。可以修改fetch请求的URL、方法、
        继续之前的标题和正文。

        参数：
            request_id (str)：要继续的获取请求的 ID。
            url （可选[str]）：获取请求的新 URL。默认为无。
            method（可选[RequestMethod]）：要使用的 HTTP 方法（例如“GET”、
                '发布'）。默认为无。
            post_data（可选[dict]）：随提取一起发送的正文数据
                请求。默认为无。
            headers (可选[list[HeaderEntry]])：要包含的 HTTP 标头列表
                在获取请求中。默认为无。
            Intercept_response (Optional[bool]): 指示是否响应
                应该被拦截。默认为无。

        返回：
            Command[Response]：用于继续获取请求的命令。"""
        params = ContinueRequestParams(requestId=request_id)
        if url is not None:
            params['url'] = url
        if method is not None:
            params['method'] = method
        if post_data is not None:
            params['postData'] = post_data
        if headers is not None:
            params['headers'] = headers
        if intercept_response is not None:
            params['interceptResponse'] = intercept_response
        return Command(method=FetchMethod.CONTINUE_REQUEST, params=params)

    @staticmethod
    def continue_request_with_auth(
        request_id: str,
        auth_challenge_response: AuthChallengeResponseType,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ) -> ContinueWithAuthCommand:
        """创建一个命令来继续暂停的获取请求
        认证。

        当获取操作需要身份验证时使用此命令。
        它提供继续请求所需的凭据。

        参数：
            request_id (str)：要继续的获取请求的 ID。
            auth_challenge_response (AuthChallengeResponseType)：身份验证
                挑战响应类型。
            proxy_username（可选[str]）：代理身份验证的用户名。
                默认为无。
            proxy_password （可选[str]）：代理身份验证的密码。
                默认为无。

        返回：
            Command[Response]: 继续获取请求的命令
                认证。"""
        auth_challenge_response_dict = AuthChallengeResponse(response=auth_challenge_response)
        if proxy_username is not None:
            auth_challenge_response_dict['username'] = proxy_username
        if proxy_password is not None:
            auth_challenge_response_dict['password'] = proxy_password

        params = ContinueWithAuthParams(
            requestId=request_id,
            authChallengeResponse=auth_challenge_response_dict,
        )
        return Command(method=FetchMethod.CONTINUE_WITH_AUTH, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """创建一个命令来禁用获取拦截。

        此命令阻止浏览器拦截获取请求。

        返回：
            Command[Response]：禁用 fetch 拦截的命令。"""
        return Command(method=FetchMethod.DISABLE)

    @staticmethod
    def enable(
        handle_auth_requests: bool,
        url_pattern: str = '*',
        resource_type: Optional['ResourceType'] = None,
        request_stage: Optional['RequestStage'] = None,
    ) -> EnableCommand:
        """创建一个命令以启用获取拦截。

        该命令允许浏览器开始拦截获取请求。
        您可以指定是否处理身份验证质询以及
        要拦截的资源类型。

        参数：
            handle_auth_requests (bool): 指示是否进行身份验证请求
                应该处理。
            url_pattern (str)：匹配 URL 进行拦截的模式。默认为“*”。
            resource_type（可选[ResourceType]）：要拦截的资源类型。
                默认为无。
            request_stage（可选[RequestStage]）：要拦截的请求的阶段。
                默认为无。

        返回：
            Command[Response]：启用 fetch 拦截的命令。"""
        request_pattern = RequestPattern(urlPattern=url_pattern)
        if resource_type is not None:
            request_pattern['resourceType'] = resource_type
        if request_stage is not None:
            request_pattern['requestStage'] = request_stage

        params = EnableParams(patterns=[request_pattern], handleAuthRequests=handle_auth_requests)
        return Command(method=FetchMethod.ENABLE, params=params)

    @staticmethod
    def fail_request(request_id: str, error_reason: ErrorReason) -> FailRequestCommand:
        """创建一个命令来模拟提取请求中的失败。

        此命令允许您模拟特定提取的失败
        操作，提供失败的原因。

        参数：
            request_id (str)：失败的fetch请求的ID。
            error_reason(ErrorReason)：失败的原因。

        返回：
            Command[Response]：获取请求失败的命令。"""
        params = FailRequestParams(requestId=request_id, errorReason=error_reason)
        return Command(method=FetchMethod.FAIL_REQUEST, params=params)

    @staticmethod
    def fulfill_request(
        request_id: str,
        response_code: int,
        response_headers: Optional[list['HeaderEntry']] = None,
        body: Optional[str] = None,
        response_phrase: Optional[str] = None,
    ) -> FulfillRequestCommand:
        """创建一个命令来满足带有自定义响应的获取请求。

        此命令允许您为获取提供自定义响应
        操作，包括 HTTP 状态代码、标头和正文内容。

        参数：
            request_id (str)：要满足的获取请求的 ID。
            response_code (int)：要返回的 HTTP 状态代码。
            response_headers（可选[list[HeaderEntry]]）：响应标头列表。
                默认为无。
            body（可选[dict]）：响应的正文内容。默认为无。
            response_phrase（可选[str]）：响应短语（例如，“OK”，
                “未找到”）。默认为无。

        返回：
            Command[Response]：用于完成获取请求的命令。"""
        params = FulfillRequestParams(
            requestId=request_id,
            responseCode=response_code,
        )
        if response_headers is not None:
            params['responseHeaders'] = response_headers
        if body is not None:
            params['body'] = body
        if response_phrase is not None:
            params['responsePhrase'] = response_phrase
        return Command(method=FetchMethod.FULFILL_REQUEST, params=params)

    @staticmethod
    def get_response_body(request_id: str) -> GetResponseBodyCommand:
        """创建一个命令来检索获取请求的响应正文。

        此命令允许您访问已完成的提取的正文
        操作，这对于分析响应数据很有用。

        参数：
            request_id (str): 获取请求体的 fetch 请求的 ID
                从。

        返回：
            Command[GetResponseBodyResponse]：获取响应正文的命令。"""
        params = GetResponseBodyParams(requestId=request_id)
        return Command(method=FetchMethod.GET_RESPONSE_BODY, params=params)

    @staticmethod
    def continue_response(
        request_id: str,
        response_code: Optional[int] = None,
        response_headers: Optional[list['HeaderEntry']] = None,
        response_phrase: Optional[str] = None,
    ) -> ContinueResponseCommand:
        """创建一个命令以继续获取拦截的响应
        请求。

        该命令允许浏览器继续响应流
        特定的获取请求，包括自定义HTTP状态代码，
        标题和响应短语。

        参数：
            request_id (str): 继续获取请求的ID
                回应.
            response_code（可选[int]）：要发送的 HTTP 状态代码。
                默认为无。
            response_headers（可选[list[HeaderEntry]]）：响应标头列表。
                默认为无。
            response_phrase（可选[str]）：响应短语（例如“OK”）。
                默认为无。

        返回：
            Command[Response]：用于继续获取响应的命令。"""
        params = ContinueResponseParams(requestId=request_id)
        if response_code is not None:
            params['responseCode'] = response_code
        if response_headers is not None:
            params['responseHeaders'] = response_headers
        if response_phrase is not None:
            params['responsePhrase'] = response_phrase
        return Command(method=FetchMethod.CONTINUE_RESPONSE, params=params)

    @staticmethod
    def take_response_body_as_stream(
        request_id: str,
    ) -> TakeResponseBodyAsStreamCommand:
        """创建一个命令以将响应正文作为流。

        该命令允许您以流的形式接收响应正文
        这对于处理大型响应非常有用。

        参数：
            request_id (str)：获取响应的 fetch 请求的 ID
                体流自。

        返回：
            Command[TakeResponseBodyAsStreamResponse]：获取响应的命令
                身体如溪流。"""
        params = TakeResponseBodyAsStreamParams(requestId=request_id)
        return Command(method=FetchMethod.TAKE_RESPONSE_BODY_AS_STREAM, params=params)
