import asyncio

from .session import CDPBaseSession
from .model import PageHost,FP_targe

from ljp_page._core.utils.async_tool import resolve_value

class FP:
    _fp_targe = FP_targe
    def __init__(self,host:PageHost):
        self.host = host
        self.session = None

    @property
    async def title(self):
        return await resolve_value(self.host.title)
    @property
    async def frames(self):
        return await resolve_value(self.host.frames)
    @property
    async def cookies(self):
        return await resolve_value(self.host.cookies)

    async def get_session(self,owm=None):
        self.session = await self.host.get_cdp_session(owm)
        return CDPBaseSession(self.session)

    async def find_checkbox(self,check_class,timeout=10):
        session = await self.get_session()
        checkbox =  await session.find_checkbox(check_class,timeout)
        if checkbox is None:
            raise TimeoutError("在目标 iframe 内找不到复选框")
        return  checkbox

    async def check_fp(self):
        title = await self.title
        if any(keyword in title for keyword in self._fp_targe.INVALID_TITLE_KEYWORDS):
            return True
        frames = await self.frames
        return any(self._fp_targe.CHALLENGE_DOMAIN in item.url for item in frames)

    async def find_frame(self,timeout=10):
        """通用的 frame 查找器，匹配不同域名。"""
        start = asyncio.get_event_loop().time()
        while True:
            frames = await self.frames
            frame = next((item for item in frames if self._fp_targe.DOMAIN in item.url), None)
            if frame is not None:
                return frame
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError("找不到符合条件的 iframe")
            await asyncio.sleep(0.3)




