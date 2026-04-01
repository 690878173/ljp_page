# 03-28-21-22-00
"""Xs 调试 UI。"""

from __future__ import annotations

import ast
import tkinter as tk
from tkinter import messagebox

from ljp_page.logger import Logger

from .spider import Xs


class XsUI(Xs):
    """调试 UI 版本的 Xs。"""

    class UI:
        """轻量调试界面，用于手动更新 Cookies。"""

        def __init__(self, spider: Xs):
            self.spider = spider
            self.logger = Logger()
            self.setup_ui()

        def setup_ui(self) -> None:
            self.window = tk.Tk()
            self.window.title("Spider Control")
            self.window.geometry("600x300")
            self.create_widgets()

        def create_widgets(self) -> None:
            label = tk.Label(self.window, text="Cookies (dict format):", font=("Arial", 12))
            label.pack(pady=10)

            self.cookies_entry = tk.Text(self.window, width=70, height=10, font=("Consolas", 10))
            self.cookies_entry.pack(pady=5)
            self.cookies_entry.insert("1.0", f"{self.spider.config.request_cookies}")

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

        def update_cookies_and_continue(self) -> None:
            cookies = self.get_cookies_from_entry()
            if not cookies:
                return

            if self.spider:
                self.update_spider_cookies(cookies)
                self.resume_spider()
                return
            messagebox.showwarning("Warning", "spider is not initialized")

        def update_spider_cookies(self, cookies) -> None:
            try:
                self.spider.change_session_cookies(cookies)
                self.logger.info(f"cookies updated: {cookies}")
            except Exception as exc:
                self.logger.error(f"update cookies failed: {exc}")

        def resume_spider(self) -> None:
            self.spider.resume()
            messagebox.showinfo("Success", "cookies updated")

        def test_run(self) -> None:
            self.spider.run(blocking=False)

        def run(self) -> None:
            self.window.mainloop()


Xs_UI = XsUI


__all__ = ["XsUI", "Xs_UI"]
