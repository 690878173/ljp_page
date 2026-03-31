# 03-28-21-22-00
"""Xs 章节管理器实现。"""

from __future__ import annotations

import re

from ljp_page.applications.pc.base.base_pc import BaseManager
from ljp_page.exceptions import No


class XsManager(BaseManager):
    """小说章节顺序写入管理器。"""

    CHAPTER_PATTERNS = {
        0: r"^(prologue|preface|epilogue)$",
        1: r"^chapter\s*\d+",
        2: r"^\d+([. :])",
        3: r"^(?:\[?vip\]?\s*)?chapter\s*\d+",
        4: r"^([\[\(].*?[\]\)]\s*)",
    }

    async def target_init(self) -> None:
        if not self.file_handle:
            return

        header = (
            f"{self.data.title}\n"
            f"{self.data.author}\n"
            f"{self.data.url}\n"
            f"{self.data.description}\n"
        )
        await self.file_handle.write(header)

    async def add_p3(self, p3: BaseManager.P3Result) -> None:
        try:
            if p3.id < self.expected_id:
                return

            async with self._lock:
                self.pending[p3.id] = p3

                while self.expected_id in self.pending:
                    current = self.pending.pop(self.expected_id)
                    chapter_title = self._get_p_mode(current.title, current.id)
                    chapter_content = self._clean_content(current.content)

                    if chapter_content:
                        text = f"\n\n{chapter_title}\n{chapter_content}\n"
                        await self.file_handle.write(text)
                    else:
                        self.warning(f"empty chapter content: {chapter_title} ({current.url})")

                    self.expected_id += 1

        except Exception as exc:
            raise No("failed to write chapter", e=exc)

    @classmethod
    def _get_p_mode(cls, title: str, index: int) -> str:
        normalized_title = (title or "").strip()
        mode = 999

        for current_mode, pattern in cls.CHAPTER_PATTERNS.items():
            if re.match(pattern, normalized_title.lower()):
                mode = current_mode
                break

        if mode in {0, 1}:
            return normalized_title

        if mode == 2:
            cleaned = re.sub(cls.CHAPTER_PATTERNS[2], "", normalized_title, count=1).strip()
            return f"Chapter {index} {cleaned}" if cleaned else f"Chapter {index}"

        if mode in {3, 4}:
            cleaned = re.sub(cls.CHAPTER_PATTERNS[mode], "", normalized_title, count=1).strip()
            return cleaned or normalized_title

        if normalized_title:
            return f"Chapter {index} {normalized_title}"
        return f"Chapter {index}"

    @staticmethod
    def _clean_content(content: str) -> str:
        if not content:
            return ""
        return content.replace("\r", "").replace("\u3000", "  ").replace("\x00", "").strip()

    async def finish(self) -> None:
        if not self.file_handle:
            return

        try:
            await self.file_handle.write("\n\n[FULL_BOOK_END]\n")
            await self.file_handle.close()
            self.info(f"book completed: {self.data.title}")
        except Exception as exc:
            self.error(f"failed to close output file: {exc}")


__all__ = ["XsManager"]
