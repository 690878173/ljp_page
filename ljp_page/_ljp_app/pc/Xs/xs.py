import asyncio
import re

import winsound
import tkinter as tk
from tkinter import messagebox
import ast
from ljp_page._ljp_app.pc.base.base_pc import Pc,BaseManager
from ljp_page.logger import Logger
from ljp_page.request import Html
from ljp_page.exceptions import No


class Xs(Pc):
    """
    需要继承重写 parse_p1，parse_p2，parse_p3
    """
    class Manager(BaseManager):
        CHAPTER_PATTERNS = {
            0: r'^(序章|前言|引子|楔子|后记|番外|终章)',
            1: r'^第[零一二三四五六七八九十百千万\d]',
            2: r'^[\d零一二三四五六七八九十百千万]+([、. ])',
            3: r'^(【VIP】)第[零一二三四五六七八九十百千万\d]',
            4: r'^([\[【].*?[\]】])',
        }

        def __init__(self, pc, data: BaseManager.p2_return, file_handle, log):
            super().__init__(pc, data=data, file_handle=file_handle, log=log)

        async def target_init(self) -> None:
            try:
                if self.file_handle:
                    header = f"{self.data.title}\n{self.data.author}\n{self.data.url}\n{self.data.description}\n"
                    await self.file_handle.write(header)
            except Exception as e:
                raise e

        async def add_p3(self, p3: BaseManager.p3_return):
            try:
                if p3.id < self.expected_id:
                    return
                self.pending[p3.id] = p3
                title = p3.title

                async with self._lock:
                    while self.expected_id in self.pending:
                        curr_p = self.pending.pop(self.expected_id)
                        self.expected_id += 1
                        await self.file_handle.write(curr_p.content)

                        title = self._get_p_mode(title, curr_p.id)

                        content = self._clean_content(curr_p.content)
                        try:
                            if content:
                                await self.file_handle.write(f"\n\n{title}\n{content}\n")
                            else:
                                self.warning(f"章节内容为空: {title} ({curr_p.url})")

                            self.expected_id += 1
                        except Exception as e:
                            self.error(f"写入章节失败 {title}: {e}")

            except Exception as e:
                raise No(f=self.add_p3,e=e)

        @classmethod
        def _get_p_mode(cls, title: str, index: int) -> str:
            title = title.strip()
            md = 999
            for mode, pattern in cls.CHAPTER_PATTERNS.items():
                if re.match(pattern, title):
                    md = mode
                    break

            if md == 1:
                return title
            elif md == 2:
                match = re.match(cls.CHAPTER_PATTERNS[md], title)
                if match:
                    return '第' + title.replace(match.group(1), '章')
            elif md in [3, 4]:
                match = re.match(cls.CHAPTER_PATTERNS[md], title)
                if match:
                    return title.replace(match.group(1), ' ')

            elif md in [0, 999]:
                return title
            return f'第{index}章:{title}'

        @staticmethod
        def _clean_content(content: str) -> str:
            if not content:
                return ""
            return content.replace('\r', '').replace('\u3000', '  ').replace('\x00', '').strip()

        async def finish(self):
            if self.file_handle:
                try:
                    await self.file_handle.write("\n\n[全书完]\n")
                    await self.file_handle.close()
                    self.info(f'书籍下载完成：{self.data.title}')
                except Exception as e:
                    self.error(f'结束书籍写入失败：{e}')

    def __init__(self, config: Pc.Config, log: Logger = None, MainWindows_ui=None, stop_flag: bool = False,
                 pause_flag: bool = False):
        super().__init__(config=config, log=log, MainWindows_ui=MainWindows_ui, stop_flag=stop_flag,
                         pause_flag=pause_flag)

    def get_manager(self):
        self.manager = self.Manager
        return self.manager

class Xs_UI(Xs):

    class UI:
        def __init__(self, spider):
            self.spider = spider
            self.logger = Logger()
            self.setup_ui()

        def setup_ui(self):
            self.window = tk.Tk()
            self.window.title("爬虫控制界面")
            self.window.geometry("600x300")

            self.create_widgets()

        def create_widgets(self):
            label = tk.Label(self.window, text="Cookies (字典格式):", font=("Arial", 12))
            label.pack(pady=10)

            self.cookies_entry = tk.Text(self.window, width=70, height=10, font=("Consolas", 10))
            self.cookies_entry.pack(pady=5)

            self.cookies_entry.insert("1.0", f"{self.spider.config.cookies}")

            button_frame = tk.Frame(self.window)
            button_frame.pack(pady=20)

            update_btn = tk.Button(button_frame, text="更新Cookies并继续", command=self.update_cookies_and_continue,
                                   font=("Arial", 12), bg="#4CAF50", fg="white", padx=20, pady=5)
            update_btn.pack(side=tk.LEFT, padx=10)

            test_btn = tk.Button(button_frame, text="测试运行", command=self.test_run,
                                 font=("Arial", 12), bg="#2196F3", fg="white", padx=20, pady=5)
            test_btn.pack(side=tk.LEFT, padx=10)

        def get_cookies_from_entry(self):
            cookies_str = self.cookies_entry.get("1.0", tk.END).strip()
            try:
                cookies = ast.literal_eval(cookies_str)
                if not isinstance(cookies, dict):
                    raise ValueError("Cookies必须是字典格式")
                return cookies
            except (SyntaxError, ValueError) as e:
                messagebox.showerror("错误", f"Cookies格式错误: {e}\n请确保输入的是有效的字典格式")
                return None

        def update_cookies_and_continue(self):
            cookies = self.get_cookies_from_entry()
            if not cookies:
                return

            if self.spider:
                self.update_spider_cookies(cookies)
                self.resume_spider()
            else:
                messagebox.showwarning("提示", "爬虫未启动，请先初始化爬虫")

        def update_spider_cookies(self, cookies):
            if self.spider.session:
                loop = self.spider.asy.loop
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self._update_session_cookies(cookies), loop)
            else:
                self.spider.config.cookies = cookies

            if self.logger:
                self.logger.info(f"Cookies已更新: {cookies}")

        async def _update_session_cookies(self, cookies):
            if self.spider.session and hasattr(self.spider.session, 'cookie_jar'):
                for key, value in cookies.items():
                    self.spider.session.cookie_jar.update_cookies({key: value})

        def resume_spider(self):
            if self.spider:
                self.spider.resume()
                messagebox.showinfo("成功", "Cookies已更新")

        def test_run(self):
            self.spider.run(blocking=False)

        def run(self):
            self.window.mainloop()

class Dybz(Xs_UI):


    def parse_p1(self,res_html,url):
        """
        解析第一站的分页列表
        """
        try:
            html = Html.drop_xml(res_html)

            links = html.xpath('/html/body/div[3]/div[1]/div[2]/ul/li/div/a/@href')
            ids = []
            for link in links:

                ids.append(link)

            # 下一页
            next_url = None
            next_btn = html.xpath('/html/body/div[3]/div[3]/div/a[5]/@href')
            if next_btn:
                next_url = next_btn[0]
                print(next_url)

            return ids, next_url
        except Exception as e:
            print(e)
            return [], None


    def parse_p3(self,res_html,url) ->tuple[str,str,str|None]:
        next_url = None
        if 'Just a moment' in res_html:
            self.pause()
            self.warning('页面被反爬')
            winsound.Beep(1500, 100)
        try:
            html = Html.drop_xml(res_html)
            title = ''
            content = ''
            ls = html.xpath('//*[@id="nr1"]//text()')
            for i in ls:
                content += str(i.replace('\r', '').replace('\xa0', '').replace('\t', '').replace('\u3000', ''))
            if_ne = html.xpath('//*[@id="nr1"]/center/span[@class="curr"]/following-sibling::a[1]/@href')
            if if_ne:
                if type(if_ne) == list:
                    if_ne = if_ne[0]
                next_url = 'https://m.diyibanzhu.me' + if_ne

            return title,content,next_url
        except Exception as e:
            self.error(f'解析章节出错:{e}')
            return '','获取失败',None


    def parse_p2(self,res_html,url) ->tuple[str,str,str,str,int,list[tuple[str,str]]]:
        html = Html.drop_xml(res_html)
        try:
            if '不存在' in html.xpath('/html/head/title/text()')[0]:
                raise ValueError(f'资源不存在,url:{url}')
            title = html.xpath('/html/body/div[3]/div[2]/div[1]/div[2]/h1/text()')[0]
            author = '未知'
            description = html.xpath('/html/body/div[3]/div[3]/div/text()')[0].replace('\r', '').replace('\xa0','').replace('\t','')
            li = html.xpath('/html/body/div[3]/div[7]/div[2]/ul/li/a/@href')
            # ls = sorted([i.split('/')[-1].split('.html')[0] for i in li])
            ls = [self.config.base_url+i for i in li]

            return title,url,author,description,len(ls),ls
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Parse failed: {e}")


if __name__ == '__main__':
    config = Dybz.Config(
        base_url='https://m.diyibanzhu.me/wap.php',
        start_id=1,
        end_id=1,
        mode='mode2',
        save_path='E:/爬虫/第一版主test',
        proxy_list=['http://127.0.0.1:7890'],
        max_retries=5,
        max_workers=2,
        timeout=5,
        p2_url='https://m.diyibanzhu.me{}',
        p1_url='https://m.diyibanzhu.me/wap.php?action=shuku&tid=&over=&order=4&uid=&totalresult=15565&pageno={}',
        headers={
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'priority': 'u=0, i',
            'referer': 'https://m.diyibanzhu.me/wap.php?action=top',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version': '"144.0.3719.82"',
            'sec-ch-ua-full-version-list': '"Not(A:Brand";v="8.0.0.0", "Chromium";v="144.0.7559.60", "Microsoft Edge";v="144.0.3719.82"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"15.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0',
        },
        cookies={
            'content_id': 'a%3A6%3A%7Bi%3A0%3Bs%3A13%3A%22%7C19009-786819%22%3Bi%3A1%3Bs%3A13%3A%22%7C18410-761847%22%3Bi%3A2%3Bs%3A13%3A%22%7C23640-783443%22%3Bi%3A3%3Bs%3A13%3A%22%7C16749-754624%22%3Bi%3A4%3Bs%3A9%3A%22%7C646-3363%22%3Bi%3A5%3Bs%3A11%3A%22%7C5277-37062%22%3B%7D',
            'cf_clearance': 'J7GJm0Y9F8N8NYHVN4LaKFvyPBSVJ0r54Dx.5rKmUm0-1768674122-1.2.1.1-CfwsDCI7CjHZQwRiAQHZ_oars0iyHGbIvcmimyA4t46vhPt3zZQwRrbHYX1v.yyEutM7eEMXJk2Sw_O40VklKtz8p0td3gBMw47g7wam4MtUeMhA42EvTybzSAGtJfwpqAkNSmapyrRub9fVkop7hFcJbwDwlO2rPO7ZntsMzwW4TyPkU9VbL6C.QSao2nizXOR_0Ee4cwfIhqWhJDYwdoSJodoBudnheSkBMLwvtsM',
        }

    )
    xs = Dybz(config=config)
    ui = Dybz.UI(xs)
    ui.run()
