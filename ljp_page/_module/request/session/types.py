"""Type contracts shared by public sessions and backend adapters."""

from __future__ import annotations

from typing import (
    IO,
    TYPE_CHECKING,
    Awaitable,
    Callable,
    Mapping,
    Protocol,
    Sequence,
    TypeAlias,
    TypedDict,
)

if TYPE_CHECKING:
    from .models import RequestsReponse

HeaderMap: TypeAlias = Mapping[str, str]
CookieMap: TypeAlias = Mapping[str, str]
QueryValue: TypeAlias = str | int | float | bool | None
QueryParams: TypeAlias = (
    Mapping[str, QueryValue | Sequence[QueryValue]] | Sequence[tuple[str, QueryValue]]
)
RequestData: TypeAlias = (
    str | bytes | Mapping[str, str] | Sequence[tuple[str, str]] | IO[str] | IO[bytes]
)
JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
BackendOptions: TypeAlias = Mapping[str, object]
AdapterCloseResult: TypeAlias = None | Awaitable[None]
AdapterSendResult: TypeAlias = "RequestsReponse | Awaitable[RequestsReponse]"


class RequestOptions(TypedDict, total=False):
    """Keyword arguments accepted by public session request methods."""

    headers: HeaderMap
    cookies: CookieMap
    timeout: float | tuple[float, float]
    proxy: str
    proxies: Mapping[str, str]
    params: QueryParams
    data: RequestData
    json: JsonValue
    json_data: JsonValue
    allow_redirects: bool
    stream: bool
    verify_ssl: bool
    impersonate: str
    ja3: str
    akamai: str
    extra_fp: object
    http_version: str
    default_headers: bool


class AsyncVerificationRunner(Protocol):
    """Verification middleware contract for :class:`AsyncSessionPool`."""

    async def run(
        self,
        send: Callable[[], Awaitable["RequestsReponse"]],
        *,
        context: Mapping[str, object] | None,
        verify_response: bool,
        max_retries: int | None,
    ) -> "RequestsReponse": ...

    def set_verification(
        self,
        checker: Callable[["RequestsReponse"], object],
        handler: Callable[[object], object],
        *,
        max_retries: int = 1,
        result_applier: Callable[[object, object], object] | None = None,
    ) -> None: ...

    def clear_verification(self) -> None: ...


class SyncVerificationRunner(Protocol):
    """Verification middleware contract for :class:`SyncSessionPool`."""

    def run(
        self,
        send: Callable[[], "RequestsReponse"],
        *,
        context: Mapping[str, object] | None,
        verify_response: bool,
        max_retries: int | None,
    ) -> "RequestsReponse": ...

    def set_verification(
        self,
        checker: Callable[["RequestsReponse"], object],
        handler: Callable[[object], object],
        *,
        max_retries: int = 1,
        result_applier: Callable[[object, object], object] | None = None,
    ) -> None: ...

    def clear_verification(self) -> None: ...


__all__ = [
    "AdapterCloseResult",
    "AdapterSendResult",
    "BackendOptions",
    "CookieMap",
    "HeaderMap",
    "JsonValue",
    "QueryParams",
    "RequestData",
    "RequestOptions",
    "QueryValue",
    "AsyncVerificationRunner",
    "SyncVerificationRunner",
]
