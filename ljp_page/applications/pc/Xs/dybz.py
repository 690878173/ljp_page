# 03-28-21-22-00
"""Dybz 站点示例解析实现。"""

from __future__ import annotations

from urllib.parse import urljoin

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None

from ljp_page.applications.pc.base.base_pc import Pc
from ljp_page.request import Html

from .ui import XsUI


class Dybz(XsUI):
    """示例站点解析实现。"""

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

        next_rel = html.xpath('//*[@id="nr1"]/center/span[@class="curr"]/following-sibling::a[1]/@href')
        next_url = self._to_absolute(url, next_rel[0]) if next_rel else None

        return self.P3ParseResult(title=title, content=content, next_url=next_url)


__all__ = ["Dybz"]
