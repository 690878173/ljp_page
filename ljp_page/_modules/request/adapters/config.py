from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterResponse:
    """适配器统一响应结构。"""

    status_code: int
    headers: dict[str, str]
    content: bytes
    encoding: str | None
    cookies: dict[str, str]