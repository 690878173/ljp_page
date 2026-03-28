from __future__ import annotations

import ast
import re
import tkinter as tk
from tkinter import messagebox
from urllib.parse import urljoin

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None

from ljp_page.applications.pc.base.base_pc import BaseManager, Pc
from ljp_page.exceptions import No
from ljp_page.logger import Logger
from ljp_page.request import Html


class Xs(Pc):
    # 小说爬虫：实现章节清洗与顺序落盘
    class Manager(BaseManager):
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
                raise No("failed to write chapter", f=self.add_p3, e=exc)

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

    def get_manager(self):
        self.manager = self.Manager
        return self.manager


class XsUI(Xs):
    class UI:
        # 轻量调试界面：用于手动更新 Cookies
        def __init__(self, spider: Xs):
            self.spider = spider
            self.logger = Logger()
            self.setup_ui()

        def setup_ui(self):
            self.window = tk.Tk()
            self.window.title("Spider Control")
            self.window.geometry("600x300")
            self.create_widgets()

        def create_widgets(self):
            label = tk.Label(self.window, text="Cookies (dict format):", font=("Arial", 12))
            label.pack(pady=10)

            self.cookies_entry = tk.Text(self.window, width=70, height=10, font=("Consolas", 10))
            self.cookies_entry.pack(pady=5)
            self.cookies_entry.insert("1.0", f"{self.spider.config.cookies}")

            button_frame = tk.Frame(self.window)
            button_frame.pack(pady=20)

            update_btn = tk.Button(
                button_frame,
                text="Update Cookies",
                command=self.update_cookies_and_continue,
                font=("Arial", 12),
                bg="#4CAF50",
                fg="white",
                padx=20,
                pady=5,
            )
            update_btn.pack(side=tk.LEFT, padx=10)

            test_btn = tk.Button(
                button_frame,
                text="Test Run",
                command=self.test_run,
                font=("Arial", 12),
                bg="#2196F3",
                fg="white",
                padx=20,
                pady=5,
            )
            test_btn.pack(side=tk.LEFT, padx=10)

        def get_cookies_from_entry(self):
            cookies_str = self.cookies_entry.get("1.0", tk.END).strip()
            try:
                cookies = ast.literal_eval(cookies_str)
                if not isinstance(cookies, dict):
                    raise ValueError("cookies must be dict")
                return cookies
            except (SyntaxError, ValueError) as exc:
                messagebox.showerror("Error", f"invalid cookies: {exc}")
                return None

        def update_cookies_and_continue(self):
            cookies = self.get_cookies_from_entry()
            if not cookies:
                return

            if self.spider:
                self.update_spider_cookies(cookies)
                self.resume_spider()
            else:
                messagebox.showwarning("Warning", "spider is not initialized")

        def update_spider_cookies(self, cookies):
            try:
                self.spider.change_session_cookies(cookies)
                self.logger.info(f"cookies updated: {cookies}")
            except Exception as exc:
                self.logger.error(f"update cookies failed: {exc}")

        def resume_spider(self):
            self.spider.resume()
            messagebox.showinfo("Success", "cookies updated")

        def test_run(self):
            self.spider.run(blocking=False)

        def run(self):
            self.window.mainloop()


Xs_UI = XsUI


class Dybz(XsUI):
    # 示例站点解析实现
    @staticmethod
    def _clean_text(text: str) -> str:
        return (
            (text or "")
            .replace("\r", "")
            .replace("\xa0", "")
            .replace("\t", "")
            .replace("\u3000", "")
            .strip()
        )

    @staticmethod
    def _to_absolute(base: str, link: str) -> str:
        return urljoin(base, link)

    def parse_p1(self, res_html: str, url: str) -> Pc.P1Result:
        try:
            html = Html.drop_xml(res_html)
            links = html.xpath("/html/body/div[3]/div[1]/div[2]/ul/li/div/a/@href")
            items = [link for link in links if link]

            next_url = None
            next_btn = html.xpath("/html/body/div[3]/div[3]/div/a[5]/@href")
            if next_btn:
                next_url = self._to_absolute(url, next_btn[0])

            return self.P1Result(items=items, next_url=next_url)
        except Exception:
            return self.P1Result(items=[], next_url=None)

    def parse_p2(self, res_html: str, url: str) -> Pc.P2ParseResult:
        html = Html.drop_xml(res_html)

        title_tag = html.xpath("/html/head/title/text()")
        if title_tag and "not found" in title_tag[0].lower():
            raise ValueError(f"resource not found: {url}")

        title = self._clean_text(html.xpath("/html/body/div[3]/div[2]/div[1]/div[2]/h1/text()")[0])
        author = "unknown"
        description = self._clean_text("".join(html.xpath("/html/body/div[3]/div[3]/div/text()")))

        chapters: list[tuple[str, str]] = []
        nodes = html.xpath("/html/body/div[3]/div[7]/div[2]/ul/li/a")
        for node in nodes:
            href = node.get("href")
            if not href:
                continue
            chapter_title = self._clean_text("".join(node.xpath(".//text()")))
            chapters.append((chapter_title, self._to_absolute(url, href)))

        next_rel = html.xpath("/html/body/div[3]/div[7]/div[3]/a[last()]/@href")
        next_url = self._to_absolute(url, next_rel[0]) if next_rel else None
        if next_url == url:
            next_url = None

        return self.P2ParseResult(
            title=title,
            author=author,
            description=description,
            p3s=chapters,
            next_url=next_url,
        )

    def parse_p3(self, res_html: str, url: str) -> Pc.P3ParseResult:
        if "Just a moment" in res_html:
            self.pause()
            self.warning("anti crawler page detected")
            if winsound is not None:
                winsound.Beep(1500, 100)

        html = Html.drop_xml(res_html)

        title = ""
        title_nodes = html.xpath("//h1/text()")
        if title_nodes:
            title = self._clean_text(title_nodes[0])

        content_nodes = html.xpath('//*[@id="nr1"]//text()')
        content = "".join(self._clean_text(i) for i in content_nodes if i)

        next_rel = html.xpath(
            '//*[@id="nr1"]/center/span[@class="curr"]/following-sibling::a[1]/@href'
        )
        next_url = self._to_absolute(url, next_rel[0]) if next_rel else None

        return self.P3ParseResult(title=title, content=content, next_url=next_url)


if __name__ == "__main__":
    pass
