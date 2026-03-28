# 03-28-15-07-30
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
import requests

from ljp_page.config.request_config import get_request_config
from ljp_page.core.adapters import (
    AdapterResponse,
    AsyncTransportAdapter,
    SyncTransportAdapter,
)
from ljp_page.modules.request import AsyncSession, SyncSession
from ljp_page.utils.logger.logger import Logger


class _RetrySyncAdapter(SyncTransportAdapter):
    """用于测试同步重试逻辑的模拟适配器。"""

    def __init__(self) -> None:
        self.count = 0

    def sync_defaults(self, headers: dict[str, str], cookies: dict[str, str]) -> None:
        return None

    def send(self, context: Any) -> AdapterResponse:
        self.count += 1
        if self.count == 1:
            raise requests.Timeout("timeout")
        return AdapterResponse(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            content=b"ok",
            encoding="utf-8",
            cookies={"a": "1"},
        )

    def close(self) -> None:
        return None


class _RetryAsyncAdapter(AsyncTransportAdapter):
    """用于测试异步重试逻辑的模拟适配器。"""

    def __init__(self) -> None:
        self.count = 0

    def sync_defaults(self, headers: dict[str, str], cookies: dict[str, str]) -> None:
        return None

    async def send(self, context: Any) -> AdapterResponse:
        self.count += 1
        if self.count == 1:
            raise asyncio.TimeoutError("timeout")
        return AdapterResponse(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            content=b"ok",
            encoding="utf-8",
            cookies={"a": "1"},
        )

    async def close(self) -> None:
        return None


def test_numeric_logger_supports_enabled_levels(tmp_path: Path) -> None:
    log_path = tmp_path / "logger.log"
    logger = Logger(
        log_file_path=str(log_path),
        enabled_levels=[5, 10],
        output_console=False,
        output_file=True,
    )
    logger.info("should_print")
    logger.error("should_not_print")
    content = log_path.read_text(encoding="utf-8")
    assert "should_print" in content
    assert "should_not_print" not in content


def test_sync_retry_middleware_works() -> None:
    config = get_request_config(
        retry={"total": 1, "backoff_factor": 0.0, "max_backoff": 0.0},
        middleware={"enable_logging_middleware": False},
    )
    session = SyncSession(
        config=config,
        adapter=_RetrySyncAdapter(),
        logger=Logger(output_console=False, output_file=False),
    )
    response = session.get("https://example.com")
    assert response.status_code == 200
    assert response.retries == 1
    assert response.text == "ok"


@pytest.mark.asyncio
async def test_async_retry_middleware_works() -> None:
    config = get_request_config(
        retry={"total": 1, "backoff_factor": 0.0, "max_backoff": 0.0},
        middleware={"enable_logging_middleware": False},
    )
    session = AsyncSession(
        config=config,
        adapter=_RetryAsyncAdapter(),
        logger=Logger(output_console=False, output_file=False),
    )
    response = await session.get("https://example.com")
    assert response.status_code == 200
    assert response.retries == 1
    assert response.text == "ok"
