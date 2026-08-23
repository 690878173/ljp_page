"""requests backend adapter."""

from __future__ import annotations

from typing import Mapping

import requests

from ljp_page._core.exceptions import LjpBaseException, NetworkException, TimeoutException

from .model import BaseAdapter
from ..config import SessionConfig
from ..models import RequestArgs, RequestsReponse


class RequestsAdapter(BaseAdapter):
    """Owns a ``requests.Session`` used solely for connection reuse and cookies."""

    def __init__(self) -> None:
        self._session: requests.Session | None = None
        self._cookies: dict[str, str] = {}

    @property
    def closed(self) -> bool:
        return self._session is None

    def open(self, config: SessionConfig, cookies: Mapping[str, str]) -> None:
        if self._session is not None:
            return
        session = requests.Session()
        session.headers.clear()  # RequestArgs.headers is the only header source.
        session.trust_env = config.Request.trust_env
        session.cookies.update(self._cookies)
        self._session = session

    def close(self) -> None:
        if self._session is not None:
            self._cookies = self._session.cookies.get_dict()
            self._session.close()
            self._session = None

    def send(self, request: RequestArgs) -> RequestsReponse:

        if self._session is None:
            raise RuntimeError("RequestsAdapter is not open")
        try:
            response = self._session.request(
                method=request.method,
                url=request.url,
                params=request.params,
                data=request.data,
                json=request.json_data,
                headers=dict(request.headers),
                cookies=dict(request.cookies) if request.cookies else None,
                timeout=request.timeout,
                allow_redirects=request.allow_redirects,
                verify=request.verify_ssl,
                proxies=dict(request.proxies) if request.proxies else None,
                stream=request.stream,
                **dict(request.extra),
            )
        except Exception as exc:
            raise self.map_exception(exc, request) from exc

        return RequestsReponse(
            request_args=request,
            status_code=response.status_code,
            url=response.url,
            headers=dict(response.headers),
            content=response.content,
            encoding=response.encoding,
            cookies=self.get_cookies(),
            history=tuple(item.url for item in response.history),
        )

    def get_cookies(self) -> dict[str, str]:
        if self._session is None:
            return dict(self._cookies)
        return self._session.cookies.get_dict()

    def set_cookies(self, cookies: Mapping[str, str]) -> None:
        self._cookies = dict(cookies)
        if self._session is not None:
            self._session.cookies.clear()
            self._session.cookies.update(self._cookies)

    def update_cookies(self, cookies: Mapping[str, str]) -> None:
        self._cookies.update(cookies)
        if self._session is not None:
            self._session.cookies.update(cookies)

    def clear_cookies(self) -> None:
        self._cookies.clear()
        if self._session is not None:
            self._session.cookies.clear()

    @staticmethod
    def map_exception(exc: Exception, request: RequestArgs) -> Exception:
        if isinstance(exc, LjpBaseException):
            return exc
        context = {"method": request.method, "url": request.url, "attempt": request.attempt}
        if isinstance(exc, requests.Timeout):
            return TimeoutException("HTTP request timed out", timeout=sum(request.timeout), context=context)
        if isinstance(exc, requests.RequestException):
            return NetworkException("HTTP request failed", url=request.url, context=context)
        return NetworkException("HTTP backend failed", url=request.url, context=context)


__all__ = ["RequestsAdapter"]
