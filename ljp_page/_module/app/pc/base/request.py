"""请求管理器 —— 封装 HTTP Session 与反爬检查。"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._module.request.session.pool import SessionPool as Session
from ljp_page._module.request.verification import SessionVerificationContext

from .config import Config


class BaseRequest(ABC):
    """请求管理器抽象接口 —— 业务可自定义实现（如 Playwright 请求）。"""

    @abstractmethod
    async def init(self) -> None: ...
    @abstractmethod
    async def get(self, url: str, **kwargs: Any) -> Any: ...
    @abstractmethod
    async def close(self) -> None: ...


class RequestManager(Ljp_BaseClass_Logger, BaseRequest):
    """默认请求管理器 —— SessionPool + 回调式反爬。

    反爬检测 / 处理通过回调委托给 BasePc 的 check_meet_fp / fp_do。
    """

    def __init__(
        self,
        config: Config,
        on_verify_check: Callable[[str], Awaitable[bool]],
        on_verify_handle: Callable[..., Awaitable[None]],
        logger: Any = None,
    ) -> None:
        super().__init__()
        self.set_logger(logger)
        self.config = config
        self._on_verify_check = on_verify_check
        self._on_verify_handle = on_verify_handle
        self.session: Session | None = None
        self._session_lock = asyncio.Lock()

    async def init(self) -> None:
        if self.session is not None:
            return
        async with self._session_lock:
            if self.session is not None:
                return
            self.session = Session(self.config.ljp_config)
            self.session.verification.set_verification(
                self._verify_check, self._verify_handle,
            )
            self.info("session 初始化完成")

    async def _verify_check(self, response: Any) -> bool:
        return await self._on_verify_check(response.text)

    async def _verify_handle(self, ctx: SessionVerificationContext) -> None:
        await self._on_verify_handle(ctx.owner, ctx.url, **ctx.request_kwargs)

    async def get(
        self, url: str, session: Any = None, check_fp: bool = True, **kwargs: Any,
    ) -> Any:
        self.debug(f"GET {url}")
        return await self.session.get(url, session=session, verify_response=check_fp, **kwargs)

    async def close(self) -> None:
        if self.session is not None and hasattr(self.session, "close"):
            await self.session.close()
            self.session = None
