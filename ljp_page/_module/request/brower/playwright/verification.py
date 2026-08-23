"""自包含的异步验证门闸 —— 消除对 ..verification 的反向依赖。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping, TypeVar

from ljp_page._core.utils.async_tool import resolve_value

from ..base.fingerprint import CLOUDFLARE_TARGET
from ..base.model import FetchResult

_T = TypeVar("_T")

# ── 数据模型 ──

@dataclass(slots=True)
class VerifyContext:
    """验证上下文快照。"""
    response: Any
    verify_attempt: int = 0
    version: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        if key in {"response", "verify_attempt", "version", "extra"}:
            return getattr(self, key)
        return self.extra[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key in {"response", "verify_attempt", "version", "extra"}:
            return getattr(self, key)
        return self.extra.get(key, default)

    def __getattr__(self, key: str) -> Any:
        try:
            return self.extra[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


# ── 验证门闸 ──

class VerificationGate:
    """异步验证门闸。

    多个并发请求共享同一个 gate：
    1. 第一个命中验证的请求暂停后续请求（door_ev.clear）
    2. 等待所有已进入 send() 的请求结束（no_active_ev.wait）
    3. 执行 handler 完成验证
    4. 恢复后续请求（door_ev.set）
    """

    def __init__(self, checker: Callable[[Any], Awaitable[bool] | bool] | None = None,
                 handler: Callable[[VerifyContext], Awaitable[Any] | Any] | None = None,
                 *, max_retries: int = 1) -> None:
        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))

        self._lock = asyncio.Lock()
        self._door_ev = asyncio.Event()
        self._door_ev.set()
        self._active_count = 0
        self._no_active_ev = asyncio.Event()
        self._no_active_ev.set()
        self._version = 0

    # ── 配置 ──

    def configure(self, checker: Any, handler: Any, *, max_retries: int = 1) -> None:
        self._checker = checker
        self._handler = handler
        self._max_retries = max(0, int(max_retries))

    def clear(self) -> None:
        self._checker = None
        self._handler = None

    # ── 内部 ──

    async def _need_verify(self, response: Any) -> bool:
        if self._checker is None:
            return False
        return bool(await resolve_value(self._checker(response)))

    async def _enter_send(self) -> int:
        await self._door_ev.wait()
        self._active_count += 1
        self._no_active_ev.clear()
        return self._version

    def _exit_send(self) -> None:
        self._active_count -= 1
        if self._active_count <= 0:
            self._active_count = 0
            self._no_active_ev.set()

    async def _handle(self, context: VerifyContext, version: int) -> bool:
        if self._handler is None:
            return False
        await self._door_ev.wait()
        if self._version != version:
            return False
        async with self._lock:
            if self._version != version:
                return False
            self._door_ev.clear()
            try:
                await self._no_active_ev.wait()
                await resolve_value(self._handler(context))
                self._version += 1
                return True
            finally:
                self._door_ev.set()

    # ── 运行 ──

    async def run(self, send: Callable[[], Awaitable[_T] | _T], *,
                  context: Mapping[str, Any] | None = None,
                  verify_response: bool = True, max_retries: int | None = None,
                  ) -> _T:
        retry_limit = max(0, int(max_retries)) if max_retries is not None else self._max_retries
        attempt = 0
        while True:
            version = await self._enter_send()
            try:
                response = await resolve_value(send())
            finally:
                self._exit_send()

            if self._version != version:
                continue
            if not verify_response or not await self._need_verify(response):
                return response
            if attempt >= retry_limit:
                return response

            ctx = VerifyContext(response=response, verify_attempt=attempt,
                                version=version, extra=dict(context or {}))
            if await self._handle(ctx, version):
                attempt += 1
                continue
            return response


# ── CF 响应检测 (从 Ljp_Context 提取) ──

class CfResponseChecker:
    """Cloudflare 响应检测 —— 判断 CDP/fetch 返回是否命中验证页。"""

    @staticmethod
    def _response_text(response: Any) -> str:
        if isinstance(response, FetchResult):
            return response.text
        if not isinstance(response, dict):
            return ""
        parts: list[str] = []
        text = response.get("text")
        if isinstance(text, str):
            parts.append(text)
        content = response.get("content")
        if isinstance(content, list):
            content = bytes(content)
        if isinstance(content, bytes):
            parts.append(content.decode("utf-8", errors="replace"))
            parts.append(content.decode("gbk", errors="replace"))
        return "\n".join(dict.fromkeys(parts))

    @staticmethod
    def _response_headers(response: Any) -> dict[str, str]:
        if isinstance(response, FetchResult):
            return {str(key).lower(): str(value) for key, value in response.headers.items()}
        if not isinstance(response, dict):
            return {}
        headers = response.get("headers") or {}
        return {str(k).lower(): str(v) for k, v in headers.items()}

    async def is_cf_challenge(self, response: Any) -> bool:
        text = self._response_text(response)
        text_lower = text.lower()
        if any(kw.lower() in text_lower for kw in CLOUDFLARE_TARGET.invalid_title_keywords):
            return True
        if "cf-chl" in text_lower or "challenges.cloudflare.com" in text_lower:
            return True
        if isinstance(response, FetchResult):
            status = response.status
        else:
            status = int(response.get("status") or 0) if isinstance(response, dict) else 0
        headers = self._response_headers(response)
        return status in {403, 503} and "cloudflare" in headers.get("server", "").lower()


__all__ = ["VerificationGate", "VerifyContext", "CfResponseChecker"]
