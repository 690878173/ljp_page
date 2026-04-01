# 03-28-23-55-00
"""PC 文本站点业务基类。"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, List, Tuple

from ....exceptions import MeetCheckError, No, Notfound
from ....logger import Logger

from .manager_base import BaseManager
from .runtime_base import BasePc


class Pc(BasePc):
    """文本站点业务基类：实现 p1/p2/p3 主流程。"""

    def __init__(
        self,
        config: BasePc.Config,
        log: Logger = None,
        MainWindows_ui: Any = None,
        stop_flag: bool = False,
        pause_flag: bool = False,
    ) -> None:
        super().__init__(
            config=config,
            log=log,
            MainWindows_ui=MainWindows_ui,
            stop_flag=stop_flag,
            pause_flag=pause_flag,
        )
        self.manager = self.get_manager()
        if self.manager is None:
            raise NotImplementedError("get_manager must return manager class")

    async def get(self, session: Any, url: str, *args: Any, **kwargs: Any) -> Any:
        self.debug(f"request url: {url}", self.get.__name__)
        kwargs.setdefault("return_type", "text")
        return await self.req.async_get(session=session, url=url, *args, **kwargs)

    def parse_p1(self, res_html: str, url: str) -> BasePc.P1Result:
        raise NotImplementedError("parse_p1 is required")

    def parse_p2(self, res_html: str, url: str) -> BasePc.P2ParseResult:
        raise NotImplementedError("parse_p2 is required")

    def parse_p3(self, res_html: str, url: str) -> BasePc.P3ParseResult:
        raise NotImplementedError("parse_p3 is required")

    @staticmethod
    def _normalize_p3s(raw_p3s: list[Any]) -> list[tuple[str, str]]:
        normalized: list[tuple[str, str]] = []
        for index, item in enumerate(raw_p3s, start=1):
            if isinstance(item, tuple) and len(item) == 2:
                chapter_title, chapter_url = item
            elif isinstance(item, list) and len(item) == 2:
                chapter_title, chapter_url = item[0], item[1]
            else:
                raise TypeError(
                    f"parse_p2.p3s[{index}] must be (title, url), got {item!r}"
                )
            normalized.append((str(chapter_title or ""), str(chapter_url)))
        return normalized

    async def _process_page(self, page_id: Any) -> List[Any]:
        if not self.config.p1_url:
            raise ValueError("mode2 requires p1_url")

        page_url = self.config.p1_url.format(page_id)
        html_str = await self.get(session=self.session, url=page_url)
        if not html_str:
            return []

        result = await self.parse_html(self.parse_p1, html_str, page_url)
        if not isinstance(result, self.P1Result):
            raise TypeError("parse_p1 must return P1Result")
        return result.items

    async def _fetch_p2(self, p2_id: Any) -> BasePc.P2Result:
        if not self.config.p2_url:
            raise ValueError("config p2_url is required for Pc spider")

        base_url = self.config.p2_url.format(p2_id)
        current_url = base_url

        all_p3s: List[Tuple[str, str]] = []
        title = ""
        author = ""
        description = ""

        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            try:
                html_str = await self.get(session=self.session, url=current_url)
                if not html_str:
                    raise No(f"empty p2 response: id={p2_id}, url={current_url}")

                parsed = await self.parse_html(self.parse_p2, html_str, current_url)
                if not isinstance(parsed, self.P2ParseResult):
                    raise TypeError("parse_p2 must return P2ParseResult")

                if not title:
                    title = parsed.title
                if not author:
                    author = parsed.author
                if not description:
                    description = parsed.description

                if parsed.p3s:
                    all_p3s.extend(self._normalize_p3s(parsed.p3s))

                if not parsed.next_url or parsed.next_url == current_url:
                    break
                current_url = parsed.next_url

            except MeetCheckError:
                continue
            except Exception as exc:
                self.error(f"fetch p2 failed: id={p2_id}, url={current_url}, error={exc}")
                raise No(f"fetch p2 failed: id={p2_id}, url={current_url}", e=exc)

        return self.P2Result(
            id=p2_id,
            url=base_url,
            title=title or str(p2_id),
            author=author,
            description=description,
            p3s=all_p3s,
            total_p3=len(all_p3s),
        )

    async def _parse_p3_info(
        self,
        p3_id: int,
        p3: Tuple[str, str],
        p2_title: str,
        manager: BaseManager,
    ) -> None:
        chapter_title, chapter_url = p3
        current_url = chapter_url
        chunks: List[str] = []

        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            try:
                html_str = await self.get(session=self.session, url=current_url)
                if not html_str:
                    self.warning(f"empty p3 response: id={p3_id}, url={current_url}")
                    break

                parsed = await self.parse_html(self.parse_p3, html_str, current_url)
                if not isinstance(parsed, self.P3ParseResult):
                    raise TypeError("parse_p3 must return P3ParseResult")

                if not chapter_title:
                    chapter_title = parsed.title
                if parsed.content and parsed.content.strip():
                    chunks.append(parsed.content)

                if not parsed.next_url or parsed.next_url == current_url:
                    break
                current_url = parsed.next_url

            except MeetCheckError:
                continue
            except Exception as exc:
                self.error(f"fetch p3 failed: id={p3_id}, url={current_url}, error={exc}")
                break

        p3_result = self.P3Result(
            p2_title=p2_title,
            id=p3_id,
            title=chapter_title,
            url=chapter_url,
            content="\n".join(chunks),
        )
        await manager.add_p3(p3_result)

    async def download(self, p2_result: BasePc.P2Result) -> None:
        try:
            safe_title = self.manager.sanitize_filename(p2_result.title)
            path = self.manager.get_file_path(safe_title)
            file_path = self.directory.get_file_path(path)
            file_handle = await self._get_file_handle(file_path)
            if file_handle is None:
                raise No(f"get file handle failed: {file_path}")

            manager = self.manager(self, p2_result, file_handle, self.log)
            if not await manager.init():
                return

            # 中文注释：章节抓取可能很多，用信号量控制内层并发，避免一次性压垮目标站点。
            semaphore = asyncio.Semaphore(max(1, self.config.chapter_concurrency))

            async def _chapter_task(chapter_id: int, chapter: Tuple[str, str]) -> None:
                async with semaphore:
                    await self._parse_p3_info(chapter_id, chapter, p2_result.title, manager)

            tasks = [
                _chapter_task(chapter_id, chapter)
                for chapter_id, chapter in enumerate(p2_result.p3s, start=1)
            ]
            results = await self.runtime.gather_inside(tasks, return_exceptions=True)
            for item in results:
                if isinstance(item, Exception):
                    self.error(f"chapter task error: {item}")

            await manager.finish()
        except Exception as exc:
            self.error(f"download flow failed: {exc}")
            raise No("download flow failed", e=exc)

    async def work(self, work_id: Any) -> None:
        try:
            p2_result = await self._fetch_p2(work_id)
            if self.ui and hasattr(self.ui, "add_p2"):
                ui_result = self.ui.add_p2(p2_result)
                if inspect.isawaitable(ui_result):
                    await ui_result
                return
            await self.download(p2_result)
        except Notfound as exc:
            self.warning(f"resource not found id={work_id}: {exc}")
        except Exception as exc:
            self.error(f"work failed id={work_id}: {exc}")

    def get_manager(self) -> Any:
        raise NotImplementedError("get_manager is required")

    async def _get_file_handle(self, file_path: str) -> Any:
        return await self.file_handle.get(file_path)


class Ys(Pc):
    class Manager(BaseManager):
        pass

    def get_manager(self) -> Any:
        self.manager = self.Manager
        return self.manager


__all__ = ["Pc", "Ys"]
