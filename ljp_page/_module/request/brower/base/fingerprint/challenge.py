"""Generic browser-challenge detection and CDP interaction."""

from __future__ import annotations

import asyncio
from typing import Any

from .dom import CDPDOM, _debug
from .model import ChallengePage, ChallengeTarget

__all__ = ["ChallengeSolver"]


class ChallengeSolver:
    """Solve one site profile using only the shared page and CDP contracts."""

    def __init__(self, page: ChallengePage, target: ChallengeTarget) -> None:
        self.source = page
        self.target = target

    async def is_challenge_page(self) -> bool:
        title = await self.source.title()
        if any(
            keyword.casefold() in title.casefold()
            for keyword in self.target.invalid_title_keywords
        ):
            return True
        return any(
            self.target.domain in str(getattr(frame, "url", ""))
            for frame in self.source.frames
        )

    async def has_clearance(self) -> bool:
        if self.target.clearance_cookie is None:
            return False
        cookies = await self.source.cookies()
        return any(cookie.name == self.target.clearance_cookie for cookie in cookies)

    async def solve(
        self,
        *,
        timeout: float = 30.0,
        poll_interval: float = 0.3,
        max_attempts: int = 3,
    ) -> bool:
        """Solve a challenge within one total timeout and bounded retries.

        ``timeout`` is the budget for the whole operation, including
        replacement widgets after a click. This prevents a stale iframe from
        adding another full timeout for every retry.
        """
        if not await self.is_challenge_page():
            return True

        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(0.0, timeout)
        attempts = min(3, max(1, int(max_attempts)))
        for attempt in range(1, attempts + 1):
            if loop.time() > deadline:
                break
            _debug(f"challenge attempt {attempt}/{attempts} started")
            try:
                challenge = await self.is_challenge_page()
            except Exception:
                challenge = True
            if not challenge:
                return True
            # The first widget may be injected slowly. Replacement widgets
            # after a successful click should converge quickly and must not
            # consume the entire remaining solve budget.
            wait_deadline = deadline
            if attempt > 1:
                wait_deadline = min(deadline, loop.time() + 5.0)
            clicked = await self._wait_and_click_checkbox(wait_deadline, poll_interval)
            _debug(f"challenge attempt {attempt}/{attempts} click result={clicked}")
            if clicked and await self._wait_for_resolution(deadline, poll_interval):
                _debug(f"challenge attempt {attempt}/{attempts} resolved")
                return True
            _debug(f"challenge attempt {attempt}/{attempts} still unresolved")
        try:
            challenge = await self.is_challenge_page()
            clearance = await self.has_clearance()
            return not challenge and (
                self.target.clearance_cookie is None or clearance
            )
        except Exception:
            return False

    async def _wait_and_click_checkbox(self, deadline: float, poll_interval: float) -> bool:
        """Poll the main target CDP tree until the nested checkbox is available."""
        session = await self.source.get_cdp_session()
        reported_widget = False
        while asyncio.get_running_loop().time() <= deadline:
            try:
                iframe = self._find_challenge_iframe(
                    (await CDPDOM.document(session)).get("root", {})
                )
                if iframe is not None:
                    if not reported_widget:
                        _debug("cloudflare shadow/iframe found")
                        reported_widget = True
                    target_click = getattr(
                        self.source, "_click_cloudflare_checkbox_cdp", None
                    )
                    if callable(target_click) and await target_click(
                        str(iframe.get("frameId", ""))
                    ):
                        return True
                if iframe is not None and await CDPDOM.click_cloudflare_checkbox(
                    session, iframe
                ):
                    return True
            except Exception as exc:
                # Challenge iframes are frequently replaced while loading.
                _debug(f"checkbox lookup/click failed ({type(exc).__name__})")
                pass
            await asyncio.sleep(poll_interval)
        return False

    async def _find_checkbox(self, session: Any) -> dict[str, Any] | None:
        document = await CDPDOM.document(session)
        root = document.get("root", {})
        iframe = self._find_challenge_iframe(root)
        if iframe is not None:
            return CDPDOM.find_node(iframe, self._is_checkbox)
        if self.target.checkbox_class:
            return CDPDOM.find_node(
                root,
                lambda item: self.target.checkbox_class
                in CDPDOM.attributes(item).get("class", "").split(),
            )
        if not root.get("nodeId"):
            return None
        return await CDPDOM.query_selector(
            session, int(root["nodeId"]), self.target.checkbox_selector
        )

    def _find_challenge_iframe(self, root: dict[str, Any]) -> dict[str, Any] | None:
        """Find the iframe in a possibly closed Shadow DOM through CDP."""
        return CDPDOM.find_node(
            root,
            lambda item: item.get("nodeName", "").casefold() == "iframe"
            and self.target.domain
            in CDPDOM.attributes(item).get("src", "").casefold(),
        )

    def _is_checkbox(self, node: dict[str, Any]) -> bool:
        if self.target.checkbox_tag is not None:
            if node.get("nodeName", "").casefold() != self.target.checkbox_tag.casefold():
                return False
            attributes = CDPDOM.attributes(node)
            return all(
                attributes.get(name.casefold(), "").casefold() == value.casefold()
                for name, value in self.target.checkbox_attributes
            )
        if self.target.checkbox_class is not None:
            return self.target.checkbox_class in CDPDOM.attributes(node).get(
                "class", ""
            ).split()
        return False

    async def _wait_for_resolution(self, deadline: float, poll_interval: float) -> bool:
        """Wait for redirect/cookie settlement after a trusted click.

        A successful mouse click is not completion. Cloudflare may redirect,
        replace the iframe, and set ``cf_clearance`` asynchronously. Require
        two consecutive settled observations before returning to the caller.
        """
        loop = asyncio.get_running_loop()
        settle_deadline = min(deadline, loop.time() + 5.0)
        session = await self.source.get_cdp_session()
        settled_checks = 0
        reported_wait = False
        while loop.time() <= settle_deadline:
            try:
                challenge = await self.is_challenge_page()
                clearance = await self.has_clearance()
            except Exception:
                challenge = True
                clearance = False

            if challenge:
                if clearance:
                    try:
                        document = await CDPDOM.document(session)
                        iframe = self._find_challenge_iframe(document.get("root", {}))
                    except Exception:
                        iframe = True
                    if iframe is None:
                        _debug("clearance cookie found and challenge iframe gone")
                        return True
                # The next solve attempt owns a replacement checkbox. Keep
                # this observation bounded so stale title/frame state cannot
                # consume the full outer timeout.
                await asyncio.sleep(poll_interval)
                continue

            if self.target.clearance_cookie is not None and not clearance:
                if not reported_wait:
                    _debug("challenge cleared; waiting for clearance cookie")
                    reported_wait = True
                settled_checks = 0
                await asyncio.sleep(poll_interval)
                continue

            settled_checks += 1
            if settled_checks >= 2:
                return True
            await asyncio.sleep(poll_interval)
        return False
