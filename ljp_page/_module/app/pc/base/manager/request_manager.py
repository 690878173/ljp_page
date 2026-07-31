# 05-24-20-15-13
from __future__ import annotations

import asyncio
from abc import ABC,abstractmethod
from typing import TYPE_CHECKING, Any

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._module.request.verification import SessionVerificationContext
from ljp_page._module.request.session.session import ASession as Session

if TYPE_CHECKING:
    from ljp_page._module.app.pc.base.model import Config
    from ljp_page._module.app.pc.base.pc import BasePc

class PC_Base_Request(ABC):

    @abstractmethod
    async def init(self):
        pass

    @abstractmethod
    async def get(self,url,**kwargs: Any):
        pass

    @abstractmethod
    async def close(self):
        pass



class Pc_Request(Ljp_BaseClass_Logger, PC_Base_Request):
    """封装 session、请求与反爬检查。"""

    async def init(self):
        await self.init_session()

    def __init__(self, owner: BasePc, config: Config, logger: Any = None) -> None:
        super().__init__()
        self.set_logger(logger)
        self.owner = owner
        self.config = config
        self.session: Session | None = None
        self._session_lock = asyncio.Lock()

    async def init_session(self) -> None:
        if self.session is not None:
            return
        async with self._session_lock:
            if self.session is not None:
                return
            self.session = Session(self.config.ljp_config)
            self.session.verification.set_verification(
                self._check_response_verification,
                self._handle_response_verification,
            )
            self.owner.session = self.session
            self.info("session 初始化")

    async def do_get(self,url: str, *args: Any,session: Any = None, **kwargs: Any) -> Any:
        self.debug(f"get url:{url}")
        return await self.session.get(url, *args, session=session, **kwargs)

    async def _check_response_verification(self, response: Any) -> bool:
        """判断响应内容是否触发验证，由业务类保留具体识别规则。"""

        return await self.owner.check_meet_fp(response.text)

    async def _handle_response_verification(self, context: SessionVerificationContext) -> None:
        """执行外部验证，并允许业务代码通过 ASession 更新 cookies、headers 等状态。"""

        await self.owner.fp_do(
            context.owner,
            context.url,
            **context.request_kwargs,
        )

    async def get(self,url: str,session: Any = None,check_fp: bool = True,**kwargs: Any,) -> Any:
        return await self.do_get(
            url,
            session=session,
            verify_response=check_fp,
            **kwargs,
        )

    async def close(self) -> None:
        if self.session is not None and hasattr(self.session, "close"):
            await self.session.close()
            self.session = None
            self.owner.session = None



__all__ = ["Pc_Request", "Pc_Request"]
