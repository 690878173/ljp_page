"""Playwright binding for backend-neutral browser challenge capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base.fingerprint import CloudflareChallenge

if TYPE_CHECKING:
    from .page import Ljp_Page

__all__ = ["PlaywrightFingerprint"]


class PlaywrightFingerprint:
    """Challenge capabilities available on a Playwright page wrapper."""

    def __init__(self, page: "Ljp_Page") -> None:
        self.source = page
        self.cloudflare = CloudflareChallenge(page)
