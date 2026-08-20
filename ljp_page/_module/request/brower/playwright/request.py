"""CDP fetch 请求适配器 —— 从 brower/request.py 提取，自包含在 playwright 包内。"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional, Union

from ljp_page._core.logger import loguru_logger
from ..request import Request
from ..exceptions import HTTP_Fetch_error

if TYPE_CHECKING:
    from .page import Ljp_Page


class FetchError(RuntimeError):
    """fetch 请求失败异常。"""


class FetchRequest(Request):
    """通过浏览器fetch API 发出 HTTP 请求。

    委托 page.execute_command 在浏览器 JS 上下文中执行，
    继承浏览器的 cookie、认证头等会话状态。
    """

    def __init__(self, page: "Ljp_Page") -> None:
        super().__init__(page)
        self.verify_gate = None

    def set_verify_gate(self, gate: Any) -> None:
        self.verify_gate = gate

    async def request(self,method: str,url: str,params: Optional[dict[str, str]] = None,data: Optional[Union[dict, list, tuple, str, bytes]] = None,json: Optional[dict[str, Any]] = None,headers = None,**kwargs,):
        check_fp = bool(kwargs.pop("check_fp", True))
        verify_response = bool(kwargs.pop("verify_response", check_fp))
        verify_max_retries = kwargs.pop("verify_max_retries", None)
        cf_refresh = bool(kwargs.pop("cf_refresh", True))
        cf_time_to_wait_captcha = kwargs.pop("cf_time_to_wait_captcha", 5)
        cf_max_retries = kwargs.pop("cf_max_retries", 3)
        cf_wait_after_click = kwargs.pop("cf_wait_after_click", 30)

        final_url = self._build_url_with_params(url, params)
        options = self._build_request_options(method, headers, json, data, **kwargs)


        send = self.build_send(final_url,options)


        try:
            if self.verify_gate is None:
                result = await send()

            else:
                result = await self.verify_gate.run(
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

            return self._check_response(result)

        except Exception as exc:
            loguru_logger.error(f'Request failed: {exc}')
            raise HTTP_Fetch_error(f'Request failed: {str(exc)}') from exc



















__all__ = ["FetchRequest", "FetchError"]
