"""Synchronous and asynchronous pools built on adapter-neutral sessions."""

from __future__ import annotations

import asyncio
import queue
import threading
from copy import deepcopy
from types import TracebackType
from typing import Callable, Mapping, TypeAlias, Unpack, cast

from ljp_page._module.request.verification import AsyncVerification, SyncVerification

from .adapter import BaseAdapter
from .async_client import AsyncSession
from .base import BaseSession
from .config import SessionConfig
from .models import RequestsReponse
from .sync_client import SyncSession
from .types import (
    AsyncVerificationRunner,
    CookieMap,
    HeaderMap,
    RequestOptions,
    SyncVerificationRunner,
)

AdapterFactory: TypeAlias = Callable[[], BaseAdapter]
AdapterSource: TypeAlias = AdapterFactory | type[BaseAdapter]


class _BaseSessionPool:
    """Shared state and broadcast operations for public session pools."""

    def __init__(self, config: SessionConfig | None, adapter: AdapterSource | None) -> None:
        self.config = config or SessionConfig()
        self._adapter_source = adapter
        self._sessions: list[BaseSession] = []

    @property
    def headers(self) -> dict[str, str]:
        return deepcopy(self.config.Request.headers)

    @headers.setter
    def headers(self, values: HeaderMap) -> None:
        merged = dict(values)
        self.config.Request.headers = merged
        for session in self._sessions:
            session.headers = merged

    def update_headers(self, values: HeaderMap) -> None:
        merged = BaseSession._merge_headers(self.config.Request.headers, values)
        self.config.Request.headers = merged
        for session in self._sessions:
            session.headers = merged

    @property
    def cookies(self) -> dict[str, str]:
        if not self._sessions:
            return deepcopy(self.config.Request.cookies)
        return self._sessions[0].cookies

    @cookies.setter
    def cookies(self, values: CookieMap) -> None:
        copied = dict(values)
        self.config.Request.cookies = copied
        for session in self._sessions:
            session.cookies = copied

    def update_cookies(self, values: CookieMap) -> None:
        copied = dict(values)
        self.config.Request.cookies.update(copied)
        for session in self._sessions:
            session.update_cookies(copied)

    def clear_cookies(self) -> None:
        self.config.Request.cookies.clear()
        for session in self._sessions:
            session.clear_cookies()

    def apply_verification_result(self, result: object, context: object | None = None) -> None:
        """Apply public Cookie/Header updates returned by a verification handler."""

        del context
        if not isinstance(result, Mapping):
            return
        headers = result.get("headers")
        cookies = result.get("cookies")
        if isinstance(headers, Mapping):
            self.update_headers(cast(HeaderMap, headers))
        if isinstance(cookies, Mapping):
            self.update_cookies(cast(CookieMap, cookies))

    def _new_adapter(self) -> BaseAdapter | None:
        if self._adapter_source is None:
            return None
        return self._adapter_source()

    def _pool_size(self) -> int:
        size = int(self.config.SessionPool.max_session)
        if size < 1:
            raise ValueError("SessionPool.max_session must be at least 1")
        return size

    @staticmethod
    def _request_context(
        owner: object,
        method: str,
        url: str,
        kwargs: Mapping[str, object],
    ) -> dict[str, object]:
        return {
            "owner": owner,
            "method": method,
            "url": url,
            "request_kwargs": dict(kwargs),
        }


class SyncSessionPool(_BaseSessionPool):
    """Blocking pool that leases :class:`SyncSession` instances per request."""

    def __init__(
        self,
        config: SessionConfig | None = None,
        *,
        verification: SyncVerificationRunner | None = None,
        adapter: AdapterSource | None = None,
    ) -> None:
        super().__init__(config, adapter)
        self.verification = verification or SyncVerification(
            checker=None,
            handler=None,
            result_applier=self.apply_verification_result,
        )
        self._queue: queue.Queue[SyncSession] = queue.Queue()
        self._init_lock = threading.RLock()
        self._initialized = False

    @property
    def closed(self) -> bool:
        return not self._initialized

    def open(self) -> "SyncSessionPool":
        self._ensure_initialized()
        return self

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            try:
                for _ in range(self._pool_size()):
                    session = SyncSession(config=self.config, adapter=self._new_adapter())
                    self._sessions.append(session)
                    session.open()
                    self._queue.put_nowait(session)
            except BaseException:
                self._close_initialized_sessions()
                raise
            self._initialized = True

    def _close_initialized_sessions(self) -> None:
        sessions = tuple(self._sessions)
        self._sessions.clear()
        self._drain_queue()
        for session in sessions:
            session.close()
        self._initialized = False

    def _drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def request(
        self,
        method: str,
        url: str,
        *,
        session: SyncSession | None = None,
        verify_response: bool = True,
        verify_max_retries: int | None = None,
        **kwargs: Unpack[RequestOptions],
    ) -> RequestsReponse:
        self.open()

        def send() -> RequestsReponse:
            leased_session = session or self._queue.get()
            try:
                return leased_session.request(method, url, **kwargs)
            finally:
                if session is None and not leased_session.closed:
                    self._queue.put(leased_session)

        return self.verification.run(
            send,
            context=self._request_context(self, method, url, kwargs),
            verify_response=verify_response,
            max_retries=verify_max_retries,
        )

    def get(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("GET", url, session=session, **kwargs)

    def post(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("POST", url, session=session, **kwargs)

    def put(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("PUT", url, session=session, **kwargs)

    def patch(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("PATCH", url, session=session, **kwargs)

    def delete(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("DELETE", url, session=session, **kwargs)

    def head(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("HEAD", url, session=session, **kwargs)

    def options(
        self, url: str, *, session: SyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return self.request("OPTIONS", url, session=session, **kwargs)

    def close(self) -> None:
        with self._init_lock:
            self._close_initialized_sessions()

    def __enter__(self) -> "SyncSessionPool":
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class AsyncSessionPool(_BaseSessionPool):
    """Async pool that leases :class:`AsyncSession` instances per request."""

    def __init__(
        self,
        config: SessionConfig | None = None,
        *,
        verification: AsyncVerificationRunner | None = None,
        adapter: AdapterSource | None = None,
    ) -> None:
        super().__init__(config, adapter)
        self.verification = verification or AsyncVerification(
            checker=None,
            handler=None,
            result_applier=self.apply_verification_result,
        )
        self._queue: asyncio.Queue[AsyncSession] = asyncio.Queue()
        self._init_lock = asyncio.Lock()
        self._initialized = False

    @property
    def closed(self) -> bool:
        return not self._initialized

    async def open(self) -> "AsyncSessionPool":
        await self._ensure_initialized()
        return self

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            try:
                for _ in range(self._pool_size()):
                    session = AsyncSession(config=self.config, adapter=self._new_adapter())
                    self._sessions.append(session)
                    await session.open()
                    self._queue.put_nowait(session)
            except BaseException:
                await self._close_initialized_sessions()
                raise
            self._initialized = True

    async def _close_initialized_sessions(self) -> None:
        sessions = tuple(self._sessions)
        self._sessions.clear()
        self._drain_queue()
        self._initialized = False
        for session in sessions:
            await cast(AsyncSession, session).close()

    def _drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                return

    async def request(
        self,
        method: str,
        url: str,
        *,
        session: AsyncSession | None = None,
        verify_response: bool = True,
        verify_max_retries: int | None = None,
        **kwargs: Unpack[RequestOptions],
    ) -> RequestsReponse:
        await self.open()

        async def send() -> RequestsReponse:
            leased_session = session or await self._queue.get()
            try:
                return await leased_session.request(method, url, **kwargs)
            finally:
                if session is None and not leased_session.closed:
                    await self._queue.put(leased_session)

        return await self.verification.run(
            send,
            context=self._request_context(self, method, url, kwargs),
            verify_response=verify_response,
            max_retries=verify_max_retries,
        )

    async def get(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("GET", url, session=session, **kwargs)

    async def post(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("POST", url, session=session, **kwargs)

    async def put(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("PUT", url, session=session, **kwargs)

    async def patch(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("PATCH", url, session=session, **kwargs)

    async def delete(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("DELETE", url, session=session, **kwargs)

    async def head(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("HEAD", url, session=session, **kwargs)

    async def options(
        self, url: str, *, session: AsyncSession | None = None, **kwargs: Unpack[RequestOptions]
    ) -> RequestsReponse:
        return await self.request("OPTIONS", url, session=session, **kwargs)

    async def close(self) -> None:
        async with self._init_lock:
            await self._close_initialized_sessions()

    async def __aenter__(self) -> "AsyncSessionPool":
        return await self.open()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()


SessionPool = AsyncSessionPool

__all__ = ["AsyncSessionPool", "SyncSessionPool", "SessionPool"]
