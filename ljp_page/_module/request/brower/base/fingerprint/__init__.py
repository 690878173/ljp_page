"""Backend-independent browser challenge and CDP DOM primitives."""

from .challenge import ChallengeSolver
from .cloudflare import CLOUDFLARE_TARGET, CloudflareChallenge
from .dom import CDPDOM
from .model import ChallengePage, ChallengeTarget

__all__ = [
    "CDPDOM",
    "CLOUDFLARE_TARGET",
    "ChallengePage",
    "ChallengeSolver",
    "ChallengeTarget",
    "CloudflareChallenge",
]
