from __future__ import annotations

from typing import TYPE_CHECKING, Optional
__all__ = ['EmulationCommands']
from ljp_page._module.request.brower.base.protocol.base import Command
from ljp_page._module.request.brower.base.protocol.emulation.methods import (



    EmulationMethod,
    SetUserAgentOverrideParams,
)

if TYPE_CHECKING:
    from ljp_page._module.request.brower.base.protocol.emulation.methods import SetUserAgentOverrideCommand
    from ljp_page._module.request.brower.base.protocol.emulation.types import UserAgentMetadata


class EmulationCommands:
    """针对模拟域实施 Chrome DevTools 协议。

    此类提供用于模拟不同环境的命令，
    包括用户代理覆盖、设备指标和其他浏览器
    对于测试和自动化有用的特性。

    请参阅 https://chromedevtools.github.io/devtools-protocol/tot/Emulation/"""

    @staticmethod
    def set_user_agent_override(
        user_agent: str,
        accept_language: Optional[str] = None,
        platform: Optional[str] = None,
        user_agent_metadata: Optional[UserAgentMetadata] = None,
    ) -> SetUserAgentOverrideCommand:
        """通过仿真域覆盖浏览器的用户代理字符串。

        这是用户代理覆盖的规范 CDP 方法。它修改
        HTTP 标头和导航器 JavaScript 属性，确保
        所有层之间的一致性。

        当提供 userAgentMetadata 时，客户端提示标头 (Sec-CH-UA-*)
        也将与被覆盖的用户代理一致地发送。

        参数：
            user_agent：要使用的完整用户代理字符串。
            Accept_language：浏览器语言首选项（例如“en-US,en;q=0.9”）。
            platform：navigator.platform 的值（例如“Win32”、“MacIntel”）。
            user_agent_metadata：Sec-CH-UA-* 标头的客户端提示元数据
                和 navigator.userAgentData。

        返回：
            SetUserAgentOverrideCommand：覆盖用户代理的 CDP 命令。"""
        params = SetUserAgentOverrideParams(userAgent=user_agent)
        if accept_language is not None:
            params['acceptLanguage'] = accept_language
        if platform is not None:
            params['platform'] = platform
        if user_agent_metadata is not None:
            params['userAgentMetadata'] = user_agent_metadata
        return Command(method=EmulationMethod.SET_USER_AGENT_OVERRIDE, params=params)
