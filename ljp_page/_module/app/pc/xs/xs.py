"""Extensible novel collector with browser-backed verification transport."""

from __future__ import annotations

import asyncio
import re
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ljp_page._core.exceptions import Notfound
from ljp_page._module.app.pc.base import (
    BasePc,
    Config,
    P1Item,
    P1Result,
    P2Item,
    P2Result,
    P3Item,
)
from ljp_page._module.file.model import ManagedAsyncFile
from ljp_page.logger import logger

from .pipeline import NovelPipeline
from .transport import BrowserHttpConfig, BrowserHttpTransport


class XsManager:
    """Crash-safe ordered chapter writer with resumable ``.downloading`` files."""

    DOWNLOAD_SUFFIX = ".downloading.txt"
    FULL_BOOK_END = "[FULL_BOOK_END]"
    CHAPTER_START_RE = re.compile(r"^\[CHAPTER_START id=(\d+)\]\s*$", re.M)
    CHAPTER_END_RE = re.compile(r"^\[CHAPTER_END id=(\d+)\]\s*$", re.M)
    CHAPTER_PATTERNS = (
        re.compile(r"^(prologue|preface|epilogue)$", re.I),
        re.compile(r"^(?:\[?vip\]?\s*)?chapter\s*\d+", re.I),
        re.compile(r"^第[一二三四五六七八九十百千0-9]+[章节篇卷集部节]\s*"),
        re.compile(r"^[一二三四五六七八九十百千0-9]+[.、\s：:]+"),
        re.compile(r"^([\[\(].*?[\]\)]\s*)"),
    )

    def __init__(self, owner: "Xs", book: P2Item, download: Path, final: Path) -> None:
        self.owner = owner
        self.book = book
        self.file = ManagedAsyncFile(download, mode="a+", encoding="utf-8")
        self.final = final
        self.expected_id = 1
        self.pending: dict[int, P3Item] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def init(self) -> bool:
        if self._initialized:
            return True
        self._initialized = True
        await self.file.open("a+", encoding="utf-8")
        content = await self._read()
        if self.FULL_BOOK_END in content:
            await self._export(content)
            await self._remove_download()
            return False
        self.expected_id = self._last_completed(content) + 1
        await self._trim_tail(content)
        if not content.strip():
            await self.file.switch_to_write(append=True)
            await self.file.write(
                f"{self.book.name}\n{self.book.author}\n{self.book.url}\n"
                f"{self.book.description or ''}\n"
            )
            await self.file.flush()
        return True

    async def add(self, chapter: P3Item) -> None:
        if chapter.id is None or chapter.id < self.expected_id:
            return
        async with self._lock:
            self.pending[chapter.id] = chapter
            while self.expected_id in self.pending:
                current = self.pending.pop(self.expected_id)
                body = self._clean_content(current.content)
                if body:
                    title = self._chapter_title(current.name, current.id)
                    await self.file.write(
                        f"\n\n[CHAPTER_START id={current.id}]\n{title}\n"
                        f"{body}\n[CHAPTER_END id={current.id}]\n"
                    )
                self.expected_id += 1
            await self.file.flush()

    async def finish(self, total: int) -> None:
        async with self._lock:
            if self.pending or self.expected_id <= total:
                await self.file.close()
                logger.warning(f"小说未完成，保留断点文件: {self.file.path}")
                return
            await self.file.write(f"\n\n{self.FULL_BOOK_END}\n")
            await self.file.flush()
            content = await self._read()
            await self._export(content)
            await self._remove_download()

    async def _read(self) -> str:
        await self.file.switch_to_read()
        return await self.file.read()

    async def _trim_tail(self, content: str) -> None:
        matches = list(self.CHAPTER_END_RE.finditer(content))
        kept = content[: matches[-1].end()].rstrip() + "\n" if matches else content
        if kept == content:
            await self.file.switch_to_write(append=True)
            return
        await self.file.switch_to_write(append=False)
        await self.file.write(kept)
        await self.file.flush()
        await self.file.switch_to_write(append=True)

    async def _export(self, content: str) -> None:
        self.final.parent.mkdir(parents=True, exist_ok=True)
        output = ManagedAsyncFile(self.final, mode="w", encoding="utf-8")
        await output.open()
        await output.write(self._clean_marks(content))
        await output.close()

    async def _remove_download(self) -> None:
        path = self.file.path
        await self.file.close()
        if path.exists():
            path.unlink()

    @classmethod
    def _last_completed(cls, content: str) -> int:
        values = cls.CHAPTER_END_RE.findall(content)
        return max((int(value) for value in values), default=0)

    @classmethod
    def _chapter_title(cls, value: str, index: int) -> str:
        title = (value or "").strip()
        for pattern in cls.CHAPTER_PATTERNS:
            title = pattern.sub("", title, count=1).strip()
        return f"第{index}章 {title}" if title else f"第{index}章"

    @staticmethod
    def _clean_content(value: str) -> str:
        value = (value or "").replace("\r", "").replace("\u3000", "  ")
        value = value.replace("\x00", "").replace("\xa0", "")
        value = value.replace("章节错误,点此报送(免注册)", "")
        value = value.replace("报送后维护人员会在两分钟内校正章节内容,请耐心等待。", "")
        return "\n".join(line.rstrip() for line in value.strip().splitlines()).strip()

    @classmethod
    def _clean_marks(cls, value: str) -> str:
        value = cls.CHAPTER_START_RE.sub("", value)
        value = cls.CHAPTER_END_RE.sub("", value)
        value = value.replace(cls.FULL_BOOK_END, "")
        return re.sub(r"\n{3,}", "\n\n", value).strip() + "\n"

    @staticmethod
    def sanitize_filename(value: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', "_", value or "未命名小说")


@dataclass(slots=True)
class _BookState:
    manager: XsManager
    total: int
    remaining: int
    lock: asyncio.Lock


class Xs(BasePc, ABC):
    """Base class for novel sites; video collectors can reuse the transport layer."""

    def __init__(self, config: Config, ui: Any = None) -> None:
        super().__init__(config, ui)
        transport_config = BrowserHttpConfig(
            browser=config.browser_config,
            session=config.session_config,
            backend=config.http_backend,
            verify_timeout=config.verify_timeout,
            verify_attempts=config.verify_attempts,
            verify_poll_interval=config.verify_poll_interval,
            image_dir=Path(config.image_dir),
        )
        self.req = BrowserHttpTransport(transport_config)
        self._book_states: dict[int, _BookState] = {}

    def get_manager(self) -> type[XsManager]:
        return XsManager

    async def check_meet_fp(self, html: str) -> bool:
        text = (html or "").casefold()
        return any(marker in text for marker in ("just a moment", "cf-chl-", "challenge-platform"))

    async def fp_do(self, session: Any, url: str, *args: Any, **kwargs: Any) -> None:
        del session, args, kwargs
        await self.req._refresh_auth(url)

    async def init_components(self) -> None:
        await self.req.init(self.config.base_url or self._input_values()[0])
        await self.file_manager.init()
        await self.parser_manager.init()

    async def collect(
        self,
        *,
        ids: Iterable[str | int] | None = None,
        url: str | None = None,
    ) -> None:
        values = [str(url)] if url else [str(item) for item in (ids or self.config.id_list or [])]
        if not values:
            raise ValueError("必须提供 ids 或 url")
        await self.init_components()
        pipeline = NovelPipeline(
            self.exc,
            book_workers=self.config.max_workers,
            chapter_workers=self.config.chapter_concurrency,
            fetch_book=self._produce_book,
            fetch_chapter=self._consume_chapter,
        )
        await pipeline.run(values)

    async def _run(self) -> None:
        await self.collect()

    def _input_values(self) -> list[str]:
        return [str(value) for value in (self.config.id_list or [])]

    async def get_p1_result(self, value: str) -> P1Result:
        page_url = self.config.format_p1_url(value)
        if not self.config.p1_url or self.config.is_absolute_url(value):
            return P1Result(items=[P1Item(name="", url=page_url)])
        response = await self.req.get(page_url)
        parsed = await self.parser_manager.parse(self.parse_p1, response.text, page_url)
        if not isinstance(parsed, P1Result):
            raise TypeError("parse_p1 必须返回 P1Result")
        return parsed

    async def _produce_book(self, value: str) -> list[tuple[P3Item, _BookState]]:
        output: list[tuple[P3Item, _BookState]] = []
        if self.config.p1_url and not self.config.is_absolute_url(value):
            current = self.config.format_p1_url(value)
            visited: set[str] = set()
            while current and current not in visited:
                visited.add(current)
                logger.info(f"正在爬取列表页: {current}")
                page = await self._get_p1_page(current)
                logger.info(f"列表页爬取完毕: {current}，发现 {len(page.items)} 本小说")
                for item in page.items:
                    state = await self._open_book(item.url)
                    if state is not None:
                        output.extend(
                            (chapter, state) for chapter in state.manager.book.p3items
                        )
                current = page.next_url
            logger.info(f"列表任务完成: {value}，共产出 {len(output)} 个章节任务")
            return output

        p1 = await self.get_p1_result(value)
        for item in p1.items:
            state = await self._open_book(item.url)
            if state is not None:
                output.extend((chapter, state) for chapter in state.manager.book.p3items)
        return output

    async def _get_p1_page(self, url: str) -> P1Result:
        response = await self.req.get(url)
        parsed = await self.parser_manager.parse(self.parse_p1, response.text, url)
        if not isinstance(parsed, P1Result):
            raise TypeError("parse_p1 必须返回 P1Result")
        return parsed

    async def get_p2_result(self, p1_item: Any) -> P2Result | None:
        """Return parsed book metadata for callers that need one-book mode."""
        state = await self._open_book(str(getattr(p1_item, "url", p1_item)))
        if state is None:
            return None
        return P2Result(items=[state.manager.book])

    async def _open_book(self, value: str) -> _BookState | None:
        current = self.config.format_p2_url(value)
        if not current:
            return None
        logger.info(f"正在爬取小说: {current}")
        first: P2Item | None = None
        chapters: list[P3Item] = []
        while current:
            response = await self.req.get(current)
            parsed = await self.parser_manager.parse(self.parse_p2, response.text, current)
            if not isinstance(parsed, P2Result) or not parsed.items:
                raise Notfound("parse_p2 未解析到小说信息", resource=current)
            page = parsed.items[0]
            first = first or page
            chapters.extend(self._normalize_p3_items(page.p3items, page.name))
            next_url = parsed.next_url or page.next_url
            current = next_url if next_url and next_url != current else None
        assert first is not None
        first.p3items = chapters
        self._reindex_p3_items(chapters, first.name)
        manager = await self._create_manager(first)
        if manager is None:
            return None
        if not chapters:
            await manager.finish(0)
            return None
        state = _BookState(manager, len(chapters), len(chapters), asyncio.Lock())
        self._book_states[id(manager)] = state
        logger.info(f"小说信息爬取完毕: {first.name}，共 {len(chapters)} 章")
        return state

    async def _consume_chapter(self, item: tuple[P3Item, _BookState]) -> None:
        chapter, state = item
        try:
            await self._fetch_chapter(chapter, state.manager)
        finally:
            async with state.lock:
                state.remaining -= 1
                if state.remaining == 0:
                    await state.manager.finish(state.total)
                    self._book_states.pop(id(state.manager), None)
                    logger.info(f"小说爬取完毕: {state.manager.book.name}，共 {state.total} 章")

    async def _fetch_chapter(self, chapter: P3Item, manager: XsManager) -> None:
        current = self.config.format_p3_url(chapter.url)
        title = chapter.name
        chunks = [chapter.content] if chapter.content else []
        logger.info(f"正在爬取章节: {manager.book.name} / {title or chapter.url}")
        while current:
            response = await self.req.get(current)
            parsed = await self.parser_manager.parse(self.parse_p3, response.text, current)
            result = self._coerce_p3_item(parsed, chapter)
            title = result.name or title
            if result.content:
                chunks.append(result.content)
            next_url = result.next_url
            current = next_url if next_url and next_url != current else None
        await manager.add(chapter.model_copy(update={"name": title, "content": "\n".join(chunks)}))
        logger.info(f"章节爬取完毕: {manager.book.name} / {title or chapter.url}")

    async def _create_manager(self, book: P2Item) -> XsManager | None:
        safe = self.check_name(XsManager.sanitize_filename(book.name))
        if not safe:
            return None
        final_name = f"{safe}.txt"
        download_name = f"{safe}{XsManager.DOWNLOAD_SUFFIX}"
        finished = self.file_manager.directory.find_file_path(final_name)
        if finished is not None:
            logger.info(f"跳过已完成小说: {finished}")
            return None
        path = self.file_manager.directory.find_file_path(download_name)
        if path is None:
            path = self.file_manager.directory.get_file_path(download_name)
        manager = XsManager(self, book, path, path.with_name(final_name))
        return manager if await manager.init() else None

    def _normalize_p3_items(self, values: list[Any], book_name: str) -> list[P3Item]:
        return [
            self._coerce_p3_item(value, None, book_name, index)
            for index, value in enumerate(values or [], 1)
        ]

    def _coerce_p3_item(
        self,
        value: Any,
        fallback: P3Item | None = None,
        book_name: str = "",
        index: int = 1,
    ) -> P3Item:
        if isinstance(value, P3Item):
            return value.model_copy(
                update={"id": value.id or index, "p2_name": value.p2_name or book_name}
            )
        if isinstance(value, (tuple, list)) and len(value) == 2:
            return P3Item(url=str(value[1]), name=str(value[0]), p2_name=book_name, id=index)
        if isinstance(value, dict):
            return P3Item(
                url=str(value.get("url", "")), name=str(value.get("name", value.get("title", ""))),
                content=str(value.get("content", "")), p2_name=str(value.get("p2_name", book_name)),
                id=int(value.get("id", index)),
                next_url=value.get("next_url"),
                other=value.get("other"),
            )
        if isinstance(value, str) and fallback is not None:
            return fallback.model_copy(update={"content": value})
        raise TypeError(f"无法转换章节数据: {value!r}")

    @staticmethod
    def _reindex_p3_items(items: list[P3Item], book_name: str) -> None:
        for index, item in enumerate(items, 1):
            item.id = index
            item.p2_name = item.p2_name or book_name

    def check_name(self, name: str) -> str | None:
        return name

    def parse_p1(self, response: str, url: str) -> P1Result:
        raise NotImplementedError

    def parse_p2(self, response: str, url: str) -> P2Result:
        raise NotImplementedError

    def parse_p3(self, response: str, url: str) -> P3Item:
        raise NotImplementedError


__all__ = ["Xs", "XsManager"]
