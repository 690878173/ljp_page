from __future__ import annotations

import asyncio
from typing import Any

from .base import FP_DOM, CDPBaseSession, FP_Find


class CF_str:  # noqa: N801
    """Cloudflare Turnstile 验证相关常量。"""

    CLOUDFLARE_CHALLENGE_DOMAIN = "challenges.cloudflare.com"
    CLOUDFLARE_IFRAME_SELECTOR = f'iframe[src*="{CLOUDFLARE_CHALLENGE_DOMAIN}"]'
    CLOUDFLARE_CHECKBOX_SELECTOR = "span.cb-i"
    CLOUDFLARE_CHECKBOX_CLASS = "cb-i"
    INVALID_TITLE_KEYWORDS = (
        "Just a moment",
        "www.cloudflare.com",
        "challenge-platform",
        "Verify you are human",
        "请稍候",
    )


class CF_cdp_session(CDPBaseSession):  # noqa: N801
    """Cloudflare CDP 会话适配器。"""


class CFDom(FP_DOM):
    """Cloudflare 专用 DOM 配置，行为复用通用 FP_DOM。"""

    _DOMAIN = CF_str.CLOUDFLARE_CHALLENGE_DOMAIN
    _CHECKBOX_CLASS = CF_str.CLOUDFLARE_CHECKBOX_CLASS
    _CDPSession = CF_cdp_session

    @classmethod
    def has_cloudflare_domain(cls, node: dict[str, Any]) -> bool:
        """判断节点自身信息是否包含 Cloudflare challenge 域名。"""
        return cls.has_targe_domain(node)


class CF_Find(FP_Find):  # noqa: N801
    """Cloudflare Turnstile 查找和点击混入类。"""

    _DOM: type[CFDom] = CFDom

    async def check_fp(self) -> bool:
        """返回当前页面是否仍是 Cloudflare 验证页。"""
        return await self.is_challenge_page()

    async def has_cookie(self) -> bool:
        """判断当前上下文是否已有 cf_clearance。"""
        cookies = await self._get_cookies()
        return any(cookie.get("name") == "cf_clearance" for cookie in cookies)

    async def is_challenge_page(self) -> bool:
        """通过标题和 iframe 判断当前页面是否仍像 Cloudflare 验证页。"""
        title = await self._get_title()
        if any(keyword in title for keyword in CF_str.INVALID_TITLE_KEYWORDS):
            return True
        return await self.has_frame()

    async def has_frame(self) -> bool:
        """判断当前页面是否仍存在 Cloudflare challenge iframe。"""
        frames = await self._get_frames()
        return any(CF_str.CLOUDFLARE_CHALLENGE_DOMAIN in item.url for item in frames)

    async def find_frame(self, timeout: float = 10):
        """等待并返回 Cloudflare challenge iframe 对应的 Frame。"""
        start = asyncio.get_event_loop().time()
        while True:
            frames = await self._get_frames()
            frame = next(
                (
                    item
                    for item in frames
                    if CF_str.CLOUDFLARE_CHALLENGE_DOMAIN in item.url
                ),
                None,
            )
            if frame is not None:
                return frame
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError("找不到 Cloudflare iframe")
            await asyncio.sleep(0.3)


__all__ = ["CF_Find", "CF_cdp_session", "CF_str", "CFDom"]
