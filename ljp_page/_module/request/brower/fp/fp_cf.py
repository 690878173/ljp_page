from __future__ import annotations

import asyncio
from typing import Any

from .base import FP_targe,FP_DOM, CDPBaseSession, FP_Find


class CF_str(FP_targe):  # noqa: N801
    """Cloudflare Turnstile 验证相关常量。"""

    CHALLENGE_DOMAIN = "challenges.cloudflare.com"
    IFRAME_SELECTOR = f'iframe[src*="{CHALLENGE_DOMAIN}"]'
    CHECKBOX_SELECTOR = "span.cb-i"
    CHECKBOX_CLASS = "cb-i"
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

    _DOMAIN = CF_str.CHALLENGE_DOMAIN
    _CHECKBOX_CLASS = CF_str.CHECKBOX_CLASS
    _CDPSession = CF_cdp_session

    @classmethod
    def has_cloudflare_domain(cls, node: dict[str, Any]) -> bool:
        """判断节点自身信息是否包含 Cloudflare challenge 域名。"""
        return cls.has_targe_domain(node)


class CF_Find(FP_Find):  # noqa: N801
    """Cloudflare Turnstile 查找和点击混入类。"""

    _DOM: type[CFDom] = CFDom
    _STR: type[CF_str] = CF_str

    async def check_fp(self) -> bool:
        """返回当前页面是否仍是 Cloudflare 验证页。"""
        return await self.is_challenge_page()

    async def has_cookie(self) -> bool:
        """判断当前上下文是否已有 cf_clearance。"""
        cookies = await self._get_cookies()
        return any(cookie.get("name") == "cf_clearance" for cookie in cookies)



__all__ = ["CF_Find", "CF_cdp_session", "CF_str", "CFDom"]
