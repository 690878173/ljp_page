import asyncio
import json
from pathlib import Path
from urllib.parse import urljoin

from ljp_page._core.exceptions import LjpBaseException
from ljp_page._module.app.pc.base import Config
from ljp_page._module.request.html import Html
from ljp_page._module.app.pc.base.model import P1Result
from ljp_page._module.app.pc.xs.xs import Xs
from ljp_page.logger import logger

from ljp_page._module.ocr import Ocr

ocr = Ocr()

from ljp_page._module.request.brower.playwright import Playwright

from ljp_page._module.app.pc.base.manager.request_manager import PC_Base_Request


class Pc_Ocr:
    def __init__(self,pc):
        self.pc = pc
        self.ocr_cache_path = Path("res/res_data/ocr_cache.json")
        self.ocr_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.ocr_img_dic_count = 0
        if self.ocr_cache_path.exists():
            self.ocr_cache = json.loads(self.ocr_cache_path.read_text(encoding="utf-8"))
        else:
            self.ocr_cache = {}

        self.ocr_cache_lock = asyncio.Lock()

    def check_img(self,url):
        if url in self.ocr_cache:
            return self.ocr_cache[url]
        else:
            return False

    def ocr_img(self, img_by):

        word = ocr.classification(img_by, png_fix=True).strip()[0]
        confuse_list = {"j", "l", "J", "L", "|", "I", "i"}

        if word in confuse_list:
            word = "丁"
        return word


    async def get_content_by_br(self, node):
        parts = []
        line = []

        for child in node.xpath("./*|./text()"):
            if isinstance(child, str):
                txt = child.strip()
                if txt:
                    line.append(txt)

            elif child.tag == "br":
                if line:
                    parts.append(line)
                    line = []
                parts.append("\n")

            elif child.tag in {"img", "a"}:
                img_url = child.get("src", "").strip() if child.tag == "img" else child.get("href", "").strip()

                if img_url:
                    if self.check_img(img_url):
                        line.append(self.check_img(img_url))
                    else:
                        im_url = self.pc.config.base_url + img_url

                        handle = asyncio.create_task(self.pc.req.get_png(im_url))

                        line.append([handle,img_url])

        if line:
            parts.append(line)

        result_lines = []
        current_line = []

        for part in parts:
            if part == "\n":
                if current_line:
                    result_lines.append("".join(current_line).strip())
                    current_line = []
                result_lines.append("")
                continue

            for item in part:
                if isinstance(item, str):
                    current_line.append(item)
                else:
                    try:
                        res = await item[0]
                        text = self.ocr_img(res)
                        self.ocr_cache[item[1]] = text
                        print(f'添加：{item[1]}:{text}')
                        self.ocr_img_dic_count += 1
                        if self.ocr_img_dic_count % 10 == 0:
                            self.ocr_cache_path.write_text(
                                json.dumps(self.ocr_cache, ensure_ascii=False, indent=2),
                                encoding="utf-8",
                            )

                    except Exception as e:
                        print(f"OCR 识别失败: {e}")
                        text = "[图片]"

                    current_line.append(text)

        if current_line:
            result_lines.append("".join(current_line).strip())

        return "\n".join(line for line in result_lines if line is not None).replace('\n\n','\n')


class Request(PC_Base_Request):

    async def close(self):
        while not self.page_queue.empty():
            try:
                page = await self.page_queue.get()
                await page.close()
            except Exception as e:
                print(e)
                continue
        await self.edge.close()

    def __init__(self,own,config,logger=None):
        self.edge = Playwright()
        self.own = own

        self.page_queue = asyncio.Queue()

    async def init(self):
        await self.edge.start()
        page_ls = await self.edge.new_pages(4)
        for page in page_ls:
            await page.goto(self.own.config.base_url)
            await page.cf()
            self.page_queue.put_nowait(page)

    async def get_page(self):
        """轮询取得页面；普通 CDP 请求允许并发，验证刷新由门闸统一协调。"""

        page = await self.page_queue.get()
        await self.page_queue.put(page)
        return page

    async def get(self,url,**kwargs):
        while True:
            page = await self.get_page()
            try:
                res = await page.cdp_request.get(
                    url,
                    verify_max_retries=3,
                    cf_time_to_wait_captcha=10,
                )
                content_bytes = bytes(res["content"])
                return content_bytes.decode("gbk", errors="replace")
            except Exception as e:
                if "Execution context was destroyed" in str(e):
                    print("✅ 捕获到页面跳转错误，已处理")
                print(f"请求失败，等待后重试: {e}")
            await asyncio.sleep(10)

    async def get_png(self,url):
        page = await self.get_page()
        res = await page.cdp_request.get(
            url,
            verify_max_retries=3,
            cf_time_to_wait_captcha=10,
        )
        return bytes(res["content"])

class Md(Xs):
    _Request_Manager = Request


    def __init__(self,config,ui=None):
        super().__init__(config,ui)
        self.ocr = Pc_Ocr(self)

    def check_name(self,name):
        no_in_ls = ['绿', '近代现代', 'GL百合','[穿越重生]','[BL同人]','[古代架空]']
        for no in no_in_ls:
            if no in name:
                self.warning(f'跳过->{name}')
                return None
        return name

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

    async def check_meet_fp(self, res):
        l = ['Just a moment...','请稍候…']
        for i in l:
            if i in res:
                return True
        return False

    async def fp_do(self,session,url,*args,**kwargs):
        pass

    def parse_p1(self, res, url: str) -> P1Result:
        try:
            res_html = res
            # print(res)
            # print(res.text)
            html = Html.drop_xml(res_html)
            links = html.xpath("//a[@class='name']")
            ls = [
                (
                    ''.join(link.xpath('.//text()')).strip(),  # 文本转字符串
                    link.xpath('./@href')[0].strip() if link.xpath('./@href') else ''  # 链接取第一个
                )
                for link in links if link is not None
            ]
            items = [self.P1Item(name=item[0],url=item[1]) for item in ls]

            next_url = None
            next_btn = html.xpath("/html/body/div[3]/div[3]/div/a[5]/@href")
            if next_btn:
                next_url = self._to_absolute(url, next_btn[0])
            return self.P1Result(
                items=items
            )
        except Exception as e:
            raise LjpBaseException(message=f'出错') from e

    def parse_p2(self, res_html: str, url: str):
        try:
            html = Html.drop_xml(res_html)

            # title_tag = html.xpath("/html/head/title/text()")
            # if title_tag and "not found" in title_tag[0].lower():
            #     raise ValueError(f"resource not found: {url}")
            title = self._clean_text(html.xpath("/html/body/div[3]/div[2]/div[1]/div[2]/h1/text()")[0])

            author = "unknown"
            description = self._clean_text("".join(html.xpath("/html/body/div[3]/div[3]/div/text()")))

            items = []
            p3items = []
            nodes = html.xpath("/html/body/div[3]/div[7]/div[2]/ul//li//a")
            for node in nodes:
                href = node.get("href")
                if not href:
                    continue
                chapter_title = self._clean_text("".join(node.xpath(".//text()")))

                p3items.append(
                    self.P3Item(url=self._to_absolute(url, href),
                                name=chapter_title,
                                )
                )
            items.append(self.P2Item(
                url = url,
                name = title,
                author = author,
                description = description,
                p3items=p3items,
            ))
            # next_rel = html.xpath("/html/body/div[3]/div[7]/div[3]/a[last()]/@href")
            next_rel = html.xpath('/html/body/div[3]/div[9]/div/div/a[3]/@href')
            next_url = self._to_absolute(url, next_rel[0]) if next_rel else None
            if next_url == url:
                next_url = None

            return self.P2Result(
                items=items,
                next_url=next_url
            )
        except Exception as e:
            raise LjpBaseException(message=f'出错') from e

    async def parse_p3(self, res_html: str, url: str):
        try:
            html = Html.drop_xml(res_html)

            title = ""
            title_nodes = html.xpath("//h1[@class='page-title']/text()")
            if title_nodes:
                title = self._clean_text(title_nodes[0])

            content_nodes = html.xpath('//div[@class="page-content font-large"]/p')[0]
            content = await self.ocr.get_content_by_br(content_nodes)
            # content = "\n".join(self._clean_text(i) for i in content_nodes if i)
    
            next_rel = html.xpath('//center[@class="chapterPages"]/a[@class="curr"]/following-sibling::a[1]/@href')
            next_url = self._to_absolute(url, next_rel[0]) if next_rel else None

            return self.P3Item(url=url,name=title,content=content,next_url=next_url)
        except Exception as e:
            self.error(e)
            raise LjpBaseException(message=f'出错') from e

if __name__ == '__main__':
     md = Md(config=Md.Config(mode='mode2',
                              save_path='./res',
                             base_url='https://www.bz777777777.com',
                             p1_url='https://www.bz777777777.com/shuku/0-size-0-{}.html',
                             p2_url='https://www.bz777777777.com{}',
                             p3_url='https://www.bz777777777.com{}',
                             start_id=236,
                             end_id=270
                             ))
                                # 已完成一半270
     md.logger = logger
     md.run()
