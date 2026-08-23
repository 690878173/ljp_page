"""Novel transport: browser verification plus one IP-bound HTTP pool."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from ljp_page._module.request.brower.playwright import BrowserLaunchConfig, Playwright
from ljp_page._module.request.session import (
    AsyncSessionPool,
    RequestsReponse,
    SessionConfig,
)
from ljp_page._module.request.session.models import RequestArgs
from ljp_page.logger import logger

HttpBackend = Literal["aiohttp", "curl_cffi"]


@dataclass(slots=True)
class BrowserHttpConfig:
    """Settings shared by the verification browser and HTTP consumers."""

    browser: BrowserLaunchConfig
    session: SessionConfig
    backend: HttpBackend = "aiohttp"
    verify_timeout: float = 30.0
    verify_attempts: int = 3
    verify_poll_interval: float = 0.5
    image_dir: Path = Path("res/images")


class ImageStore:
    """Content-addressed image storage used by chapter parsers."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self._lock = asyncio.Lock()

    async def save(self, url: str, content: bytes, *, content_type: str = "") -> Path:
        suffix = _suffix(url, content_type)
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        path = self.root / f"{digest}{suffix}"
        async with self._lock:
            self.root.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(content)
        return path


class BrowserHttpTransport:
    """Keep browser verification and HTTP requests on the same network path."""

    challenge_markers = (
        "just a moment",
        "cf-chl-",
        "challenge-platform",
        "verify you are human",
        "请稍候",
    )

    def __init__(self, config: BrowserHttpConfig) -> None:
        self.config = config
        self._inherit_browser_proxy()
        if config.backend == "curl_cffi":
            config.session.Request.extra.setdefault("impersonate", "chrome")
        self.browser = Playwright(config.browser)
        self.page: Any = None
        adapter = None
        if config.backend == "curl_cffi":
            from ljp_page._module.request.session.adapter.curl_cffi_adapter import (
                CurlCffiAdapter,
            )

            adapter = CurlCffiAdapter
        self.http = AsyncSessionPool(
            config.session,
            adapter=adapter,
        )
        self.images = ImageStore(config.image_dir)
        self._refresh_lock = asyncio.Lock()
        self._initialized = False

    def _inherit_browser_proxy(self) -> None:
        """Use the browser proxy for HTTP when SessionConfig has none."""
        if self.config.session.Proxy.http or self.config.session.Proxy.https:
            return
        proxy = self.config.browser.proxy
        server = proxy.get("server") if isinstance(proxy, dict) else proxy
        if server:
            self.config.session.Proxy.http = str(server)
            self.config.session.Proxy.https = str(server)

    @property
    def headers(self) -> dict[str, str]:
        return self.http.headers

    @property
    def cookies(self) -> dict[str, str]:
        return self.http.cookies

    async def init(self, bootstrap_url: str) -> None:
        if self._initialized:
            return
        await self.browser.start()
        self.page = await self.browser.new_page()
        await self.http.open()
        await self._refresh_auth(bootstrap_url)
        self._initialized = True

    async def close(self) -> None:
        if not self._initialized and self.page is None:
            return
        with contextlib.suppress(Exception):
            await self.http.close()
        with contextlib.suppress(Exception):
            await self.browser.close()
        self.page = None
        self._initialized = False

    async def get(self, url: str, **kwargs: Any) -> RequestsReponse:
        return await self._request("GET", url, **kwargs)

    async def get_image(self, url: str, **kwargs: Any) -> bytes:
        response = await self._request("GET", url, **kwargs)
        response.raise_for_status()
        content = response.content
        await self.images.save(url, content, content_type=response.headers.get("content-type", ""))
        return content

    async def _request(self, method: str, url: str, **kwargs: Any) -> RequestsReponse:
        # Pass the synchronized browser state explicitly.  The session layer
        # also keeps these values as defaults, but explicit request arguments
        # make the state visible in the request object and prevent stale
        # caller-provided snapshots from surviving a re-verification.
        caller_headers = dict(kwargs.get("headers") or {})
        kwargs["headers"] = {**self.headers, **caller_headers}
        kwargs["cookies"] = self.cookies
        response = await self.http.request(method, url, verify_response=False, **kwargs)
        logger.debug(
            f"HTTP 请求完成: {method.upper()} {url} status={response.status_code} "
            f"headers={len(response.request_args.headers)} cookies="
            f"{len(response.request_args.cookies or {})}"
        )
        if self._is_challenge(response):
            logger.warning(f"检测到验证页面，开始浏览器验证: {url}")
            await self._refresh_auth(url)
            kwargs["headers"] = {**self.headers, **caller_headers}
            kwargs["cookies"] = self.cookies
            response = await self.http.request(method, url, verify_response=False, **kwargs)
            logger.debug(
                f"重新验证后请求完成: {method.upper()} {url} status={response.status_code} "
                f"headers={len(response.request_args.headers)} cookies="
                f"{len(response.request_args.cookies or {})}"
            )
            if self._is_challenge(response) and method.upper() == "GET":
                logger.warning(f"验证后 HTTP 仍被拦截，回退浏览器 Fetch: {url}")
                return await self._browser_fallback(url)
        return response

    async def _browser_fallback(self, url: str) -> RequestsReponse:
        result = await self.page.fetch.get(url, timeout=30, check_fp=False)
        timeout = self.config.session.Timeout.resolve(None)
        request = RequestArgs(
            method="GET",
            url=url,
            headers=self.headers,
            timeout=timeout,
            allow_redirects=True,
            stream=False,
            verify_ssl=True,
            cookies=self.cookies,
        )
        return RequestsReponse(
            request_args=request,
            status_code=result.status,
            url=result.url,
            headers=result.headers,
            content=result.content,
            encoding=result.encoding,
            cookies=self.cookies,
            raw=result.source,
        )

    async def _refresh_auth(self, url: str) -> None:
        async with self._refresh_lock:
            logger.info(f"正在验证浏览器访问权限: {url}")
            captured: dict[str, str] = {}
            request_ids: set[str] = set()

            def capture(event: dict[str, Any]) -> None:
                request = event.get("request", event)
                request_url = str(request.get("url", ""))
                request_id = str(event.get("requestId", ""))
                is_extra = "url" not in request
                matches = (
                    request_id in request_ids
                    if is_extra
                    else request_url == url or request_url.rstrip("/") == url.rstrip("/")
                )
                if matches:
                    if request_id:
                        request_ids.add(request_id)
                    captured.update(
                        {
                            str(name): str(value)
                            for name, value in request.get("headers", {}).items()
                        }
                    )

            await self.page.cdp.enable(network=True)
            unsubscribe_request = await self.page.cdp.subscribe(
                "Network.requestWillBeSent", capture
            )
            unsubscribe_extra = await self.page.cdp.subscribe(
                "Network.requestWillBeSentExtraInfo", capture
            )
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                solved = await self.page.solve_cloudflare(
                    timeout=self.config.verify_timeout,
                    poll_interval=self.config.verify_poll_interval,
                    max_attempts=self.config.verify_attempts,
                )
                if solved:
                    # Navigation headers and Fetch headers differ. Generate a
                    # same-origin browser Fetch so CDP captures the exact
                    # header family used by the HTTP consumer.
                    with contextlib.suppress(Exception):
                        await self.page.fetch.get(url, timeout=30, check_fp=False)
            finally:
                unsubscribe_request()
                unsubscribe_extra()
            if not solved:
                logger.error(f"浏览器验证失败: {url}")
                raise RuntimeError(f"Cloudflare verification failed: {url}")
            cookies = await self.page.cookies()
            self.http.cookies = {cookie.name: cookie.value for cookie in cookies}
            headers = {
                name: value
                for name, value in captured.items()
                if name.casefold()
                not in {"host", "content-length", "cookie", "accept-encoding"}
            }
            headers.update(self.page.headers)
            if "User-Agent" not in {name.title() for name in headers}:
                headers["User-Agent"] = await self.browser.ua()
            self.http.headers = headers
            logger.info(
                f"浏览器验证完成，HTTP 会话已同步 cookies/headers "
                f"(cookies={len(self.http.cookies)}, headers={len(self.http.headers)})"
            )

    def _is_challenge(self, response: RequestsReponse) -> bool:
        if response.status_code in {403, 429, 503}:
            text = response.text[:200_000].casefold()
            return any(marker in text for marker in self.challenge_markers)
        return False


def _suffix(url: str, content_type: str) -> str:
    path_suffix = Path(urlparse(url).path).suffix.lower()
    if path_suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}:
        return path_suffix
    value = content_type.casefold()
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }.get(value.split(";", 1)[0], ".bin")


__all__ = ["BrowserHttpConfig", "BrowserHttpTransport", "ImageStore"]
