from enum import Enum

from typing_extensions import NotRequired, TypedDict

from base import Command, EmptyResponse, Response
from emulation.types import UserAgentMetadata


class EmulationMethod(str, Enum):
    SET_USER_AGENT_OVERRIDE = 'Emulation.setUserAgentOverride'


class SetUserAgentOverrideParams(TypedDict):
    """用于覆盖用户代理字符串的参数。

    请参阅 https://chromedevtools.github.io/devtools-protocol/tot/Emulation/#method-setUserAgentOverride"""

    userAgent: str
    acceptLanguage: NotRequired[str]
    platform: NotRequired[str]
    userAgentMetadata: NotRequired[UserAgentMetadata]


SetUserAgentOverrideCommand = Command[SetUserAgentOverrideParams, Response[EmptyResponse]]
