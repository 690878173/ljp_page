"""The backend boundary for HTTP sessions."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, ClassVar, Mapping

from ..types import AdapterCloseResult, AdapterSendResult

if TYPE_CHECKING:
    from ..config import SessionConfig
    from ..models import RequestArgs, RequestsReponse


class BaseAdapter(abc.ABC):
    """Owns a native HTTP session and translates only neutral request models."""

    is_async: ClassVar[bool] = False

    @abc.abstractmethod
    def open(self, config: "SessionConfig", cookies: Mapping[str, str]) -> None:
        """Create and retain the native session if it is not already open."""

    @abc.abstractmethod
    def close(self) -> AdapterCloseResult:
        """Release the native session. Async adapters return an awaitable."""

    @abc.abstractmethod
    def send(self, request: "RequestArgs") -> AdapterSendResult:
        """Perform I/O and return a unified response or awaitable response."""

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        """Whether the adapter currently has no usable native session."""

    @abc.abstractmethod
    def get_cookies(self) -> dict[str, str]:
        """Return a snapshot of the native cookie jar."""

    @abc.abstractmethod
    def set_cookies(self, cookies: Mapping[str, str]) -> None:
        """Replace the native cookie jar contents."""

    @abc.abstractmethod
    def update_cookies(self, cookies: Mapping[str, str]) -> None:
        """Merge cookies into the native cookie jar."""

    @abc.abstractmethod
    def clear_cookies(self) -> None:
        """Clear the native cookie jar."""

    @abc.abstractmethod
    def map_exception(self, exc: Exception, request: "RequestArgs") -> Exception:
        """Map a backend exception to the project's public exception hierarchy."""


__all__ = ["BaseAdapter"]
