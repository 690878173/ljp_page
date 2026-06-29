from __future__ import annotations

import asyncio
import inspect
import re
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Any

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._core.exceptions import HtmlParseError, MeetCheckError, No, Notfound
from ljp_page._module.file import ManagedAsyncFile
from ljp_page._module.request.session import LjpResponse

from ljp_page._module.app.pc.base import P1Result, P2Item, P2Result, P3Item
from ljp_page._module.app.pc.base import BasePc
from ljp_page._core.utils.other import f_mark


class XsManager(Ljp_BaseClass_Logger):
    DOWNLOAD_SUFFIX = ".downloading.txt"
    FULL_BOOK_END = "[FULL_BOOK_END]"
    CHAPTER_START_RE = re.compile(r"^\[CHAPTER_START id=(\d+)\]\s*$", re.M)
    CHAPTER_END_RE = re.compile(r"^\[CHAPTER_END id=(\d+)\]\s*$", re.M)

    clean_patterns = [
        r"^(prologue|preface|epilogue)",
        r"^(?:\[?vip\]?\s*)?chapter\s*\d+",
        r"^第[一二三四五六七八九十0-9]+[章节篇卷集部节]\s*",
        r"^[一二三四五六七八九十0-9]+[.、\s：:]+",
        r"^([\[\(].*?[\]\)]\s*)",
    ]

    # 全覆盖中文章节格式（第1章、第一章、1.、1、、一、、[VIP]）
    CHAPTER_PATTERNS = [
        re.compile(r"^(prologue|preface|epilogue)$", re.I),
        re.compile(r"^(?:\[?vip\]?\s*)?chapter\s*\d+", re.I),
        re.compile(r"^第[一二三四五六七八九十百千0-9]+[章节篇卷集部节]\s*"),
        re.compile(r"^[一二三四五六七八九十百千0-9]+[.、\s：:]+"),
        re.compile(r"^([\[\(].*?[\]\)]\s*)"),
    ]

    def __init__(
            self,
            pc: Any,
            data: P2Item,
            file_handle: ManagedAsyncFile,
            final_file_path: str | Path,
            logger: Any,
    ) -> None:
        super().__init__()
        self.set_logger(logger)
        self.pc = pc
        self.data = data
        self.file_handle = file_handle
        self.final_file_path = Path(final_file_path).expanduser().resolve()
        self.expected_id = 1
        self.pending: dict[int, P3Item] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        self._already_finished = False

    async def init(self) -> bool:
        if self._initialized:
            return not self._already_finished
        self._initialized = True

        await self.file_handle.open("a+", encoding="utf-8")
        content = await self._read_download_content()
        if self.FULL_BOOK_END in content:
            await self._export_readable_file(content)
            await self._remove_download_file()
            self._already_finished = True
            return False

        self.expected_id = self._get_last_completed_chapter_id(content) + 1
        await self._trim_incomplete_tail(content)
        self.info(f"章节管理器初始化: {self.data.name}-->{self.data.url}")
        if self.expected_id > 1:
            self.info(f"检测到断点文件，将从第 {self.expected_id} 章继续写入")

        await self.target_init(content)
        return True

    async def _read_download_content(self) -> str:
        await self.file_handle.switch_to_read()
        return await self.file_handle.read()

    async def target_init(self, existing_content: str = "") -> None:
        if not self.file_handle:
            return

        await self.file_handle.switch_to_write(append=True)
        if existing_content.strip():
            return

        header = (
            f"{self.data.name}\n"
            f"{self.data.author}\n"
            f"{self.data.url}\n"
            f"{self.data.description or ''}\n"
        )
        await self.file_handle.write(header)
        await self.file_handle.flush()

    async def add_p3(self, p3: P3Item) -> None:
        try:
            if p3.id < self.expected_id:
                return

            async with self._lock:
                self.pending[p3.id] = p3

                while self.expected_id in self.pending:
                    current = self.pending.pop(self.expected_id)
                    chapter_title = self._get_p_mode(current.name, current.id)
                    chapter_title = chapter_title.replace(self.data.name, "")
                    chapter_content = self._clean_content(current.content)

                    if chapter_content:
                        chapter_text = (
                            f"\n\n[CHAPTER_START id={current.id}]\n"
                            f"{chapter_title}\n{chapter_content}\n"
                            f"[CHAPTER_END id={current.id}]\n"
                        )
                        await self.file_handle.write(chapter_text)
                    else:
                        self.warning(f"写入章节内容为空: {chapter_title} ({current.url})")

                    self.expected_id += 1
                await self.file_handle.flush()

        except Exception as exc:
            raise No("写入章节失败", e=exc)

    async def finish(self, total_chapters: int) -> None:
        if not self.file_handle:
            return

        try:
            if self.expected_id <= total_chapters or self.pending:
                await self.file_handle.close()
                self.warning(f"章节未全部写完，保留断点文件: {self.file_handle.path}")
                return

            await self.file_handle.switch_to_write(append=True)
            await self.file_handle.write(f"\n\n{self.FULL_BOOK_END}\n")
            await self.file_handle.flush()
            content = await self._read_download_content()
            await self._export_readable_file(content)
            await self.file_handle.close()
            await self._remove_download_file()
            self.info(f"下载完成: {self.data.name}")
        except Exception as exc:
            self.error(f"关闭文件失败: {exc}")

    @classmethod
    def _get_last_completed_chapter_id(cls, content: str) -> int:
        matches = cls.CHAPTER_END_RE.findall(content)
        if not matches:
            return 0
        return max(int(item) for item in matches)

    async def _trim_incomplete_tail(self, content: str) -> None:
        """中断时可能留下半章内容，续写前只保留最后一个完整章节。"""
        end_matches = list(self.CHAPTER_END_RE.finditer(content))
        if end_matches:
            resume_content = content[: end_matches[-1].end()].rstrip() + "\n"
        else:
            start_match = self.CHAPTER_START_RE.search(content)
            if start_match:
                resume_content = content[: start_match.start()].rstrip() + "\n"
            else:
                resume_content = content

        if resume_content == content:
            await self.file_handle.switch_to_write(append=True)
            return

        await self.file_handle.switch_to_write(append=False)
        await self.file_handle.write(resume_content)
        await self.file_handle.flush()
        await self.file_handle.switch_to_write(append=True)

    async def _export_readable_file(self, content: str) -> None:
        clean_content = self._clean_download_marks(content)
        self.final_file_path.parent.mkdir(parents=True, exist_ok=True)
        final_file = ManagedAsyncFile(self.final_file_path, mode="w", encoding="utf-8")
        await final_file.open()
        await final_file.write(clean_content)
        await final_file.close()

    async def _remove_download_file(self) -> None:
        download_path = self.file_handle.path
        await self.file_handle.close()
        if download_path.exists():
            download_path.unlink()

    @classmethod
    def _clean_download_marks(cls, content: str) -> str:
        content = cls.CHAPTER_START_RE.sub("", content)
        content = cls.CHAPTER_END_RE.sub("", content)
        # 是否去除最后结束标签
        # content = content.replace(cls.FULL_BOOK_END, "")
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip() + "\n"

    @classmethod
    def _get_p_mode(cls, title: str, index: int, rt: bool = False) -> str:
        normalized_title = (title or "").strip()

        # 清洗干净
        cleaned = normalized_title
        for pat in XsManager.clean_patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.I).strip()

        if rt:
            return cleaned

        if cleaned:
            return f"第{index}章 {cleaned}"
        return f"第{index}章"

    @staticmethod
    def _clean_content(content: str) -> str:
        if not content:
            return ""
        cleaned = (
            content.replace("\r", "")
            .replace("\u3000", "  ")
            .replace("\x00", "")
            .replace("\u00A0", "")
            .replace("章节错误,点此报送(免注册)", "")
            .replace("报送后维护人员会在两分钟内校正章节内容,请耐心等待。", "")
        )
        lines = cleaned.strip().splitlines()

        for i in range(min(2, len(lines))):
            for p in XsManager.clean_patterns:
                lines[i] = re.sub(p, "", lines[i], flags=re.I)
            lines[i] = lines[i].strip()

        return "\n".join(lines)

    @staticmethod
    def sanitize_filename(title: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', "_", title or "未命名小说")

    @staticmethod
    def get_file_path(title: str) -> str:
        return f"{title}.txt"

    @classmethod
    def get_download_file_path(cls, title: str) -> str:
        return f"{title}{cls.DOWNLOAD_SUFFIX}"


class Xs(BasePc,ABC):

    @abstractmethod
    async def fp_do(self, session, url, *args, **kwargs):
        pass

    @abstractmethod
    async def check_meet_fp(self, res) -> bool:
        return False

    def __init__(self, config, ui=None):
        super().__init__(config, ui)

    def get_manager(self) -> type[XsManager]:
        self.manager = XsManager
        return XsManager

    def parse_p1(self, response: LjpResponse, url: str) -> P1Result:
        raise NotImplementedError("需要继承实现 parse_p1")

    def parse_p2(self, res_html: str, url: str) -> P2Result:
        raise NotImplementedError("需要继承实现 parse_p2")

    def parse_p3(self, res_html: str, url: str) -> P3Item:
        raise NotImplementedError("需要继承实现 parse_p3")

    @f_mark('format_p1,请求和解析，返回P1res，在p1_work_loop中被调用')
    async def get_p1_result(self, p1_id: str) -> P1Result:
        if not self.config.p1_url:
            return P1Result(items=[Xs.P1Item(url=p1_id, name='')])

        page_url = self.config.format_p1_url(p1_id)

        response = await self.req.get(url=page_url)
        if not response:
            return P1Result()

        parsed = await self.parser_manager.parse_html(self.parse_p1, response, page_url)
        if not isinstance(parsed, P1Result):
            raise TypeError("parse_p1 需要返回 P1Result")
        return parsed

    @f_mark('转发p3到download')
    async def _p3_work(self, p2_result):
        try:
            if self.ui and hasattr(self.ui, "add_p2"):
                ui_result = self.ui.add_p2(p2_result)
                if inspect.isawaitable(ui_result):
                    await ui_result
                return
            await self.download(p2_result)
        except Exception as exc:
            self.error(f"p2_work 任务出错:: {exc}")

    @f_mark('format_p2,请求和解析，返回P2res')
    async def get_p2_result(self,p1_item) -> P2Result | None:
        try:
            if not self.config.p2_url:
                raise ValueError("config.p2_url 参数未设置")

            p2_id = getattr(p1_item, "url", p1_item)
            base_url = self.config.format_p2_url(p2_id)
            current_url = base_url

            all_p3s: list[P3Item] = []
            title = ""
            author = ""
            description = ""

            while current_url:
                if self.stop_flag:
                    break
                await self.pause_event.wait()

                try:
                    response = await self.req.get(url=current_url)
                    html_str = response
                    if not html_str:
                        raise No(f"p2 响应为空: id={p2_id}, url={current_url}")

                    parsed = await self.parser_manager.parse_html(self.parse_p2, html_str, current_url)
                    if not isinstance(parsed, P2Result):
                        raise TypeError("parse_p2 需要返回 P2Result")
                    if not parsed.items:
                        raise Notfound("parse_p2 未解析到信息", resource=str(p2_id))

                    page_item = parsed.items[0]
                    if not title:
                        title = page_item.name
                    if not author:
                        author = page_item.author
                    if not description:
                        description = page_item.description or ""

                    all_p3s.extend(self._normalize_p3_items(page_item.p3items, title))

                    next_url = parsed.next_url or page_item.next_url
                    if not next_url or next_url == current_url:
                        break
                    current_url = next_url

                except MeetCheckError:
                    continue
                except Exception as exc:
                    raise No(f"获取 p2 出错: id={p2_id}, url={current_url}") from exc

            self._reindex_p3_items(all_p3s, title)  # 重置索引名称
            res = P2Result(
                items=[
                    P2Item(
                        name=title or str(p2_id),
                        author=author,
                        description=description,
                        url=base_url,
                        p3items=all_p3s,
                    )
                ]
            )
            await self._p3_work(res)
            return res

        except Notfound as exc:
            self.warning(f"资源不存在 id={p1_item}: {exc}")
        except Exception as exc:
            self.error(f"p2 任务出错: id={p1_item}: {exc}")

    @f_mark('整体章节调度，初始化管理器')
    async def download(self, p2_result: P2Result) -> None:
        try:
            for p2_item in p2_result.items:
                safe_title = self.manager.sanitize_filename(p2_item.name)
                safe_title = self.check_name(safe_title)
                if not safe_title:
                    continue
                final_name = self.manager.get_file_path(safe_title)
                download_name = self.manager.get_download_file_path(safe_title)
                finished_path = self.file_manager.directory.find_file_path(final_name)
                if finished_path is not None:
                    self.info(f"检测到完整文件，跳过下载: {finished_path}")
                    continue

                download_path = self.file_manager.directory.find_file_path(download_name)
                if download_path is None:
                    download_path = self.file_manager.directory.get_file_path(download_name)
                final_path = download_path.with_name(final_name)
                file_handle = ManagedAsyncFile(
                    download_path,
                    mode="a+",
                    encoding="utf-8",
                )

                manager = self.manager(self, p2_item, file_handle, final_path, self.logger)
                if not await manager.init():
                    continue

                resume_start_id = manager.expected_id

                async def _chapter_task(chapter_id: int, chapter: P3Item) -> None:
                    await self._parse_p3_info(chapter_id, chapter, p2_item.name, manager)

                tasks = [
                    _chapter_task(chapter_id, chapter)
                    for chapter_id, chapter in enumerate(p2_item.p3items, start=1)
                    if chapter_id >= resume_start_id
                ]
                handles = self.exc.submit_many_inside(
                    tasks,
                    mode="async",
                )
                for handle in handles:
                    try:
                        await handle
                    except Exception as exc:
                        self.error(f"章节任务出错: {exc}")

                await manager.finish(total_chapters=len(p2_item.p3items))

        except Exception as exc:
            self.error(f"下载流程失败: {exc}")
            raise No("下载流程失败") from exc

    @f_mark('章节下载，添加到管理器')
    async def _parse_p3_info(self,p3_id: int,p3: P3Item,p2_name: str,manager: XsManager,) -> None:
        p3.url = self.config.format_p3_url(p3.url)
        current_url = p3.url
        chapter_title = p3.name
        chunks: list[str] = [p3.content] if p3.content else []

        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            try:
                response = await self.req.get(url=current_url)
                html_str = response
                if not html_str:
                    self.warning(f"p3 响应为空: id={p3_id}, url={current_url}")
                    break

                parsed = await self.parser_manager.parse_html(self.parse_p3, html_str, current_url)
                parsed_p3 = self._coerce_p3_item(parsed, fallback=p3, p2_name=p2_name, p3_id=p3_id)
                if parsed_p3.name:
                    chapter_title = parsed_p3.name
                if parsed_p3.content and parsed_p3.content.strip():
                    chunks.append(parsed_p3.content)

                if not parsed_p3.next_url or parsed_p3.next_url == current_url:
                    break
                current_url = parsed_p3.next_url

            except MeetCheckError:
                continue
            except HtmlParseError as e:
                self.html_parse_error(html_str)
                self.error(e)
                raise Notfound(e=e)
            except Exception as exc:
                self.error(f"获取 p3 出错: id={p3_id}, url={current_url}, error={exc}")
                break

        await manager.add_p3(
            P3Item(
                url=p3.url,
                name=chapter_title,
                p2_name=p2_name,
                content="\n".join(chunks),
                id=p3_id,
                description=p3.description,
                other=p3.other,
            )
        )

    def check_name(self, name: str) -> str:
        return name

    @f_mark('将输入转化为标准的P3items')
    def _normalize_p3_items(self, raw_p3s: list[Any], p2_name: str) -> list[P3Item]:
        p3_items: list[P3Item] = []
        for index, item in enumerate(raw_p3s or [], start=1):
            p3_items.append(self._coerce_p3_item(item, fallback=None, p2_name=p2_name, p3_id=index))
        return p3_items

    @f_mark('将输入转化为标准的P3item')
    def _coerce_p3_item(self, item: Any, *, fallback: P3Item | None, p2_name: str, p3_id: int, ) -> P3Item:
        if isinstance(item, P3Item):
            if not item.id:
                item.id = p3_id
            if not item.p2_name:
                item.p2_name = p2_name
            return item

        if isinstance(item, (tuple, list)) and len(item) == 2:
            return P3Item(
                url=str(item[1]),
                name=str(item[0] or ""),
                p2_name=p2_name,
                id=p3_id,
            )

        if isinstance(item, dict):
            return P3Item(
                url=str(item.get("url") or ""),
                name=str(item.get("name") or item.get("title") or ""),
                p2_name=str(item.get("p2_name") or p2_name),
                content=str(item.get("content") or ""),
                id=int(item.get("id") or p3_id),
                description=item.get("description"),
                next_url=item.get("next_url"),
                other=item.get("other"),
            )

        if isinstance(item, str) and fallback is not None:
            return P3Item(
                url=fallback.url,
                name=fallback.name,
                p2_name=p2_name,
                content=item,
                id=p3_id,
                description=fallback.description,
                other=fallback.other,
            )

        raise TypeError(f"无法转换章节数据: {item!r}")

    @staticmethod
    def _reindex_p3_items(p3_items: list[P3Item], p2_name: str) -> None:
        for index, item in enumerate(p3_items, start=1):
            item.id = index
            if not item.p2_name:
                item.p2_name = p2_name


__all__ = ["Xs", "XsManager"]
