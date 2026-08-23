"""Producer/consumer orchestration for novel collection."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from ljp_page._module.runtime import LJPExc
from ljp_page.logger import logger

_STOP = object()


class NovelPipeline:
    """Run book discovery and chapter fetching with explicit sentinels."""

    def __init__(
        self,
        exc: LJPExc,
        *,
        book_workers: int,
        chapter_workers: int,
        fetch_book: Callable[[str], Awaitable[Any]],
        fetch_chapter: Callable[[Any], Awaitable[None]],
    ) -> None:
        self.exc = exc
        self.book_workers = max(1, book_workers)
        self.chapter_workers = max(1, chapter_workers)
        self.fetch_book = fetch_book
        self.fetch_chapter = fetch_chapter
        self.books: asyncio.Queue[str | object] = asyncio.Queue()
        self.chapters: asyncio.Queue[Any] = asyncio.Queue()

    async def run(self, inputs: Iterable[str]) -> None:
        for value in inputs:
            await self.books.put(value)
        for _ in range(self.book_workers):
            await self.books.put(_STOP)

        # ``LJPExc`` owns the outer collector coroutine. Queue workers must be
        # created on that same event loop; submitting them again to its
        # background async loop would bind asyncio.Queue to the wrong loop.
        producers = [
            asyncio.create_task(self._book_worker())
            for _ in range(self.book_workers)
        ]
        consumers = [
            asyncio.create_task(self._chapter_worker())
            for _ in range(self.chapter_workers)
        ]
        await asyncio.gather(*producers)
        for _ in range(self.chapter_workers):
            await self.chapters.put(_STOP)
        await asyncio.gather(*consumers)
        await self.books.join()
        await self.chapters.join()

    async def _book_worker(self) -> None:
        while True:
            item = await self.books.get()
            try:
                if item is _STOP:
                    return
                if not isinstance(item, str):
                    continue
                result = await self.fetch_book(item)
                if result is not None:
                    for chapter in result:
                        await self.chapters.put(chapter)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(f"小说元数据任务失败: {item}")
            finally:
                self.books.task_done()

    async def _chapter_worker(self) -> None:
        while True:
            item = await self.chapters.get()
            try:
                if item is _STOP:
                    return
                await self.fetch_chapter(item)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("章节任务失败")
            finally:
                self.chapters.task_done()


__all__ = ["NovelPipeline"]
