"""HTTP 适配器抽象基类。"""

from __future__ import annotations

import abc
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...config import LjpConfig
    from ..models import AdapterResult, RequestContext


class BaseHttpAdapter(abc.ABC):
    """HTTP 适配器抽象基类，定义统一接口契约。"""

    @abc.abstractmethod
    def create_session(
        self,
        headers: dict[str, str],
        cookies: dict[str, str],
        config: "LjpConfig",
    ) -> Any:
        ...

    @abc.abstractmethod
    def close(self, session: Any | None) -> Any:
        """aiohttp/curl-cffi 返回 coroutine；requests 返回 None。"""
        ...

    @abc.abstractmethod
    def send(self, session: Any, context: "RequestContext") -> Any:
        """同步返回 AdapterResult；异步返回 Awaitable[AdapterResult]。"""
        ...

    @staticmethod
    @abc.abstractmethod
    def extract_cookies(session: Any) -> dict[str, str]:
        ...

    @staticmethod
    @abc.abstractmethod
    def update_headers(session: Any | None, headers: dict[str, str]) -> None:
        ...

    @abc.abstractmethod
    def update_cookies(self, session: Any | None, cookies: dict[str, str]) -> None:
        ...


# __all__ = ["BaseHttpAdapter"]
