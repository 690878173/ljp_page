# 该文件为测试文件，请忽略

from urllib.parse import urljoin

from ljp_page._core._exceptions import LjpBaseException,HtmlParseError
from ljp_page._modules.request.cg_session.html import Html
from ljp_page.apps.new_pc.base.model import P1Result
from ljp_page.apps.new_pc.xs.xs import Xs
from ljp_page.logger import logger
from ljp_page.edge.pydoll import cf


class Md(Xs):

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

    async def fp(self,res):
        l = ['Just a moment...','请稍候…']
        for i in l:
            if i in res:
                return True
        return False

    async def fp_do(self,session,url,*args,**kwargs):
        r_url, cookies, hd = await cf(url)
        session.update_cookies(cookies)
        session.headers.update(hd)


    def parse_p1(self, res_html: str, url: str) -> P1Result:
        try:
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
            raise LjpBaseException(message=f'出错', e=e)

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
            raise LjpBaseException(message=f'出错',e=e)

    def parse_p3(self, res_html: str, url: str):
        try:
            html = Html.drop_xml(res_html)

            title = ""
            title_nodes = html.xpath("//h1[@class='page-title']/text()")
            if title_nodes:
                title = self._clean_text(title_nodes[0])

            content_nodes = html.xpath('//div[@class="page-content font-large"]/p//text()')
            content = "\n".join(self._clean_text(i) for i in content_nodes if i)

            next_rel = html.xpath('//center[@class="chapterPages"]/a[@class="curr"]/following-sibling::a[1]/@href')
            next_url = self._to_absolute(url, next_rel[0]) if next_rel else None

            return self.P3Item(url=url,name=title,content=content,next_url=next_url)
        except Exception as e:
            self.error(e)
            raise LjpBaseException(message=f'出错', e=e)

if __name__ == '__main__':
    md = Md(config=Md.Config(mode='mode2',
                             p1_url='https://www.bz888888888.com/shuku/0-size-0-{}.html',
                             p2_url='https://www.bz888888888.com{}',
                             p3_url='https://www.bz888888888.com{}',
                             start_id=120,
                             end_id=125,
                             ))
    md.logger = logger
    md.run()