from __future__ import annotations

import json as jsonlib
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Any, Optional, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


from ljp_page._core.logger import logger

from .exceptions import HTTP_Fetch_error
from ljp_page._core.utils.other import f_mark

if TYPE_CHECKING:
    from .protocol.fetch.types import HeaderEntry



from .constants import Scripts

class Request_need(ABC):

    @abstractmethod
    async def execute_command(self,expression,**kwargs):
        raise NotImplementedError()



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

    def __init__(self, page:Request_need):
        self.page = page

    async def get(self,url: str,params: Optional[dict[str, str]] = None, **kwargs,):
        """执行 GET 请求以检索数据。

        参数：
            url：从中检索数据的目标 URL。
            params：附加到 URL 的查询参数。
            **kwargs：附加获取选项。
            """
        return await self.request('GET', url, params=params, **kwargs)

    async def post(self,url: str,data: Optional[Union[dict, list, tuple, str, bytes]] = None,json: Optional[dict[str, Any]] = None,**kwargs,):
        """执行 POST 请求以创建或提交数据。

        参数：
            url：数据提交的目标URL。
            data：要提交的表单数据（URL 编码）。
            json：要提交的 JSON 数据。
            **kwargs：附加获取选项。
            """
        return await self.request('POST', url, data=data, json=json, **kwargs)

    async def put(self,url: str,data: Optional[Union[dict, list, tuple, str, bytes]] = None,json: Optional[dict[str, Any]] = None, **kwargs,):
        """执行 PUT 请求以更新/替换资源。

        参数：
            url：要更新的资源的目标 URL。
            data：用于更新的表单数据。
            json：用于更新的 JSON 数据。
            **kwargs：附加获取选项。
            。"""
        return await self.request('PUT', url, data=data, json=json, **kwargs)

    async def patch(self,url: str,data: Optional[Union[dict, list, tuple, str, bytes]] = None,json: Optional[dict[str, Any]] = None,**kwargs,):
        """执行部分资源更新的 PATCH 请求。

        参数：
            url：要部分更新的资源的目标 URL。
            数据：要应用更改的表单数据。
            json：要应用更改的 JSON 数据。
            **kwargs：附加获取选项。
            。"""
        return await self.request('PATCH', url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs):
        """执行删除资源的 DELETE 请求。

        参数：
            url：要删除的资源的目标 URL。
            **kwargs：附加获取选项。

        返回：
            确认删除的响应对象。"""
        return await self.request('DELETE', url, **kwargs)

    async def head(self, url: str, **kwargs):
        """执行 HEAD 请求以仅检索响应标头。

        对于检查资源是否存在、大小或修改日期很有用
        无需下载完整内容。

        参数：
            url：要检查标头的目标 URL。
            **kwargs：附加获取选项。

        返回：
            具有标头但没有正文内容的响应对象。"""
        return await self.request('HEAD', url, **kwargs)

    async def options(self, url: str, **kwargs):
        """执行 OPTIONS 请求以检查允许的方法和功能。

        用于 CORS 预检检查和发现服务器功能。

        参数：
            url：要检查选项的目标 URL。
            **kwargs：附加获取选项。

        返回：
            具有允许的方法和 CORS 标头的响应对象。"""
        return await self.request('OPTIONS', url, **kwargs)

    async def request(self,method: str,url: str,params: Optional[dict[str, str]] = None,data: Optional[Union[dict, list, tuple, str, bytes]] = None,json: Optional[dict[str, Any]] = None,headers: Optional[list[HeaderEntry]] = None,**kwargs,):
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
        check_fp = bool(kwargs.pop("check_fp", True))
        verify_response = bool(kwargs.pop("verify_response", check_fp))
        verify_max_retries = kwargs.pop("verify_max_retries", None)
        cf_refresh = bool(kwargs.pop("cf_refresh", True))
        cf_time_to_wait_captcha = kwargs.pop("cf_time_to_wait_captcha", 5)
        cf_max_retries = kwargs.pop("cf_max_retries", 3)
        cf_wait_after_click = kwargs.pop("cf_wait_after_click", 30)

        final_url = self._build_url_with_params(url, params)
        options = self._build_request_options(method, headers, json, data, **kwargs)
        # logger.info(f'Executing request: method={method.upper()}, url={final_url}')
        logger.debug(
            f'Executing request: method={method.upper()}, url={final_url}, '
            f'headers={bool(headers)}, json={json is not None}, data={data is not None}'
        )
        try:
            async def send():
                return await self._execute_fetch_request(final_url, options)

            verification_gate = getattr(self.page, "cdp_verification_gate", None)
            if verification_gate is None:
                result = await send()
            else:
                # CDP/fetch 请求统一走验证门闸，命中验证页后由页面完成验证再重发当前请求。
                result = await verification_gate.run(
                    send,
                    context={
                        "page": self.page,
                        "request": self,
                        "method": method.upper(),
                        "url": url,
                        "final_url": final_url,
                        "params": params,
                        "options": options,
                        "cf_refresh": cf_refresh,
                        "cf_time_to_wait_captcha": cf_time_to_wait_captcha,
                        "cf_max_retries": cf_max_retries,
                        "cf_wait_after_click": cf_wait_after_click,
                    },
                    verify_response=verify_response,
                    max_retries=verify_max_retries,
                )

            if isinstance(result, dict) and (result.get("error") or "content" not in result):
                raise HTTP_Fetch_error(str(result.get("error") or "响应缺少 content 字段"))
            return result

        except Exception as exc:
            logger.error(f'Request failed: {exc}')
            raise HTTP_Fetch_error(f'Request failed: {str(exc)}') from exc

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

    @f_mark('构建请求选项字典')
    def _build_request_options(self,method: str,headers: Optional[list[HeaderEntry]],json: Optional[dict[str, Any]],data: Optional[Union[dict, list, tuple, str, bytes]],**kwargs,) -> dict[str, Any]:
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

    @f_mark('添加请求正文和适当的 Content-Type 标头')
    def _add_request_body(self,options: dict[str, Any],json: Optional[dict[str, Any]],data: Optional[Union[dict, list, tuple, str, bytes]],) -> None:
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
    def _handle_data_options(options: dict[str, Any], data: Optional[Union[dict, list, tuple, str, bytes]]) -> None:
        """处理数据选项。"""
        if isinstance(data, (dict, list, tuple)):
            options['body'] = urlencode(data, doseq=True)
            options['headers'].setdefault('Content-Type', 'application/x-www-form-urlencoded')
            logger.debug('Request data encoded as form-urlencoded')
        else:
            options['body'] = data
            logger.debug('Request data set as raw payload')

    async def _execute_fetch_request(self, url: str, options: dict[str, Any]):
        """使用浏览器的运行时执行获取请求。"""
        script = Scripts.MAKE_REQUEST.format(url=jsonlib.dumps(url), options=jsonlib.dumps(options))
        # await self._register_callbacks()
        logger.debug('Registered network callbacks and executing fetch via Runtime.evaluate')

        return await self.page.execute_command(expression=script)

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
