"""Backend-neutral contracts for browser challenge handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..model import BrowserCookie, CDPSession

__all__ = ["ChallengePage", "ChallengeTarget"]


class ChallengePage(Protocol):
    """Browser-page capabilities required by a challenge solver."""

    @property
    def frames(self) -> list[Any]: ...

    async def title(self) -> str: ...

    async def cookies(self) -> list[BrowserCookie]: ...

    async def get_cdp_session(self, target: Any = None) -> CDPSession: ...


@dataclass(frozen=True, slots=True)
class ChallengeTarget:
    """Site-specific markers used by the generic CDP challenge solver."""

    domain: str
    invalid_title_keywords: tuple[str, ...]
    checkbox_selector: str
    checkbox_class: str | None = None
    checkbox_tag: str | None = None
    checkbox_attributes: tuple[tuple[str, str], ...] = ()
    clearance_cookie: str | None = None
