"""Cloudflare profile built on the generic browser-challenge primitives."""

from __future__ import annotations

from .challenge import ChallengeSolver
from .model import ChallengePage, ChallengeTarget

__all__ = ["CLOUDFLARE_TARGET", "CloudflareChallenge"]

CLOUDFLARE_TARGET = ChallengeTarget(
    domain="challenges.cloudflare.com",
    invalid_title_keywords=(
        "Just a moment",
        "www.cloudflare.com",
        "challenge-platform",
        "Verify you are human",
        "请稍候",
    ),
    checkbox_selector='input[type="checkbox"]',
    checkbox_tag="input",
    checkbox_attributes=(("type", "checkbox"),),
    clearance_cookie="cf_clearance",
)


class CloudflareChallenge(ChallengeSolver):
    """Cloudflare challenge behavior independent of a browser backend."""

    def __init__(self, page: ChallengePage) -> None:
        super().__init__(page, CLOUDFLARE_TARGET)
