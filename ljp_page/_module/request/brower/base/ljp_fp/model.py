
from typing import Any, Awaitable, Callable, Iterator, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CDPBaseSession



class FP_targe:  # noqa: N801
    """常用反爬目标域名配置。"""

    CHALLENGE_DOMAIN = "challenges.cloudflare.com"
    INVALID_TITLE_KEYWORDS = (
        "Just a moment",
        "www.cloudflare.com",
        "challenge-platform",
        "Verify you are human",
        "请稍候",
    )
    DOMAIN = 'challenges.cloudflare.com'



class PageHost(Protocol):
    """FP_Find 需要的宿主能力"""

    @property
    async def title(self) -> Union[str, Awaitable[str]]: ...

    @property
    def frames(self) -> Union[list, Awaitable[list]]: ...

    @property
    async def cookies(self) -> Union[list, Awaitable[list]]: ...

    async def get_cdp_session(self, own=None) -> Any: ...
