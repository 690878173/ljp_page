# 03-29-00-27-00
"""樱花动漫站点示例。"""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urljoin

from lxml import etree

from .models import PageParseResult, VideoEpisode, VideoInfo
from .spider import Ys


class YhdmSpider(Ys):
    """樱花动漫解析实现。"""

    @staticmethod
    def _clean_text(value: str) -> str:
        return (
            (value or "")
            .replace("\r", "")
            .replace("\n", "")
            .replace("\t", "")
            .replace("\xa0", "")
            .replace("\u3000", "")
            .strip()
        )

    @staticmethod
    def parse_video_info(html_str: str, video_id: Any, url: str) -> VideoInfo:
        html = etree.HTML(html_str)
        if html is None:
            raise ValueError("invalid html")

        title = YhdmSpider._clean_text("".join(html.xpath('//div[@class="info"]/h1/text()')))
        if not title:
            title = f"video_{video_id}"

        description = YhdmSpider._clean_text("".join(html.xpath('//div[@class="info"]/p/text()')))
        episode_nodes = html.xpath('//div[contains(@class,"play")]//a')

        episodes: list[VideoEpisode] = []
        for index, node in enumerate(episode_nodes, start=1):
            href = (node.get("href") or "").strip()
            if not href:
                continue
            episode_url = urljoin(url, href)
            episode_title = YhdmSpider._clean_text("".join(node.xpath(".//text()"))) or f"episode_{index}"
            episodes.append(
                VideoEpisode(
                    index=index,
                    title=episode_title,
                    page_url=episode_url,
                )
            )

        return VideoInfo(
            id=video_id,
            title=title,
            url=url,
            description=description,
            episodes=episodes,
        )

    @staticmethod
    def parse_page_videos(html_str: str, page_url: str) -> PageParseResult | list[Any]:
        html = etree.HTML(html_str)
        if html is None:
            return []

        result: list[Any] = []
        links = html.xpath('//*[@id="app"]//div[@data-href]/@data-href')
        for link in links:
            match = re.search(r"/id/(\d+)", link)
            if match:
                result.append(int(match.group(1)))
        return PageParseResult(items=result, next_url=None)

    async def get_real_m3u8_url(self, episode_page_url: str) -> Optional[str]:
        html = await self.req.async_get(self.session, episode_page_url, return_type="text")
        if not html:
            return None
        match = re.search(r"""["'](https?://[^"' ]+\.m3u8[^"']*)["']""", html)
        if match:
            return match.group(1)
        return None


__all__ = ["YhdmSpider"]
