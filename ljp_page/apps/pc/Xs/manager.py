# 04-01-20-18-00
"""Xs 章节管理器实现。"""

from __future__ import annotations

import re

from ljp_page._core.exceptions import No

from ..base import BaseManager


import re
from typing import Dict, Pattern


class XsManager(BaseManager):
    """小说章节顺序写入管理器（增强版 - 专业中文小说适配）"""

    # 🔥 核心：全覆盖章节标题正则（中英文 + 中文数字 + 符号）
    CHAPTER_PATTERNS: Dict[int, Pattern] = {
        # 0：英文特殊章节（序章/后记）
        0: re.compile(r"^(prologue|preface|epilogue|foreword|appendix)$", re.I),
        # 1：英文 Chapter + 数字
        1: re.compile(r"^(?:\[?vip\]?\s*)?chapter\s*\d+", re.I),
        # 2：中文标准章节：第1章 / 第一章 / 第1节 / 第三节 / 第1卷 / 第十篇
        2: re.compile(r"^第[一二三四五六七八九十百千0-9]+[章节篇卷集部节]\s*", re.I),
        # 3：纯数字/中文数字开头 + 符号：1. 1、 1  一、 二. 三
        3: re.compile(r"^[一二三四五六七八九十百千0-9]+[.、\s：:]+", re.I),
        # 4：括号前缀 [VIP] [免费] [完结] (上) (下)
        4: re.compile(r"^([\[\(].*?[\]\)]\s*)+", re.I),
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
        """
        智能处理章节标题：自动识别中英文、中文数字、各种符号，返回干净标题
        """
        normalized_title = (title or "").strip()
        matched_mode = None

        # 匹配优先级：序章 > 英文章节 > 中文章节 > 数字符号 > 括号前缀
        for mode, pattern in cls.CHAPTER_PATTERNS.items():
            if pattern.search(normalized_title):
                matched_mode = mode
                break

        # 模式 0/1：直接保留原文（prologue / Chapter 1）
        if matched_mode in {0, 1}:
            return normalized_title.strip()

        cleaned_title = normalized_title

        # 模式 2：清洗中文章节前缀（第1章、第一章 → 保留后面标题）
        if matched_mode == 2:
            cleaned_title = cls.CHAPTER_PATTERNS[2].sub("", cleaned_title, 1).strip()

        # 模式 3：清洗数字/中文序号（1. 一、 3  → 保留后面标题）
        if matched_mode == 3:
            cleaned_title = cls.CHAPTER_PATTERNS[3].sub("", cleaned_title, 1).strip()

        # 模式 4：清洗 [VIP] 这类括号前缀
        if matched_mode == 4:
            cleaned_title = cls.CHAPTER_PATTERNS[4].sub("", cleaned_title, 1).strip()

        # 最终兜底：空标题自动生成 Chapter {index}
        cleaned_title = cleaned_title.strip()
        if cleaned_title:
            return f"第{index}章 {cleaned_title}"
        return f"第{index}章"

    @staticmethod
    def _clean_content(content: str) -> str:
        """
        超强内容清洗：去空白、去特殊空格、去空行、去不可见字符、去NBSP
        """
        if not content:
            return ""

        # 1. 替换各种空白
        content = content.replace("\r", "")
        content = content.replace("\u3000", "  ")  # 全角空格
        content = content.replace("\u00a0", " ")  # &nbsp;
        content = content.replace("\x00", "")
        content = content.replace("NBSP", "")

        # 2. 合并多余空行（保留段落结构）
        lines = [line.strip() for line in content.split("\n")]
        content = "\n".join([line for line in lines if line])

        return content.strip()

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
