
from __future__ import annotations

from typing import Any

from ljp_page._core._exceptions import HtmlParseError, MeetCheckError, No, Notfound

from ljp_page._module.app.pc.base import P2Item, P3Item, P1Result, P2Result

from ljp_page._apps.new_pc.pydoll_pc.request_manager import PydollResponse, PcRequest,XsTabPool
from ljp_page._module.app.pc.xs import XsManager,Xs



class Xs_(Xs):
    def __init__(self, config, ui=None):
        super().__init__(config, ui)
        self._xs_tab_pool: XsTabPool | None = None
        self.req = PcRequest(self, self.config, self.logger)
    def _get_xs_tab_count(self) -> int:
        configured = getattr(self.config, "xs_tab_count", None)
        if configured is None:
            configured = getattr(self.config, "pydoll_tab_count", None)
        if configured is not None:
            return max(1, int(configured))

        chapter_concurrency = max(1, int(getattr(self.config, "chapter_concurrency", 1)))
        return min(chapter_concurrency, 4)

    async def _get_xs_tab_pool(self) -> XsTabPool:
        if self._xs_tab_pool is None:
            self._xs_tab_pool = XsTabPool(self, self._get_xs_tab_count())
        await self._xs_tab_pool.start()
        return self._xs_tab_pool

    async def _xs_get(self, url: str, *, check_fp: bool = True) -> PydollResponse:
        pool = await self._get_xs_tab_pool()
        seen_version = await self.req.fp_guard.before_request() if check_fp else None

        async with pool.lease() as tab:
            response = await self._xs_tab_get(tab, url)
            if check_fp and await self.check_meet_fp(response.text):
                await self.req.fp_guard.handle_blocked(
                    seen_version,
                    self.fp_do,
                    tab,
                    url,
                )
        return response

    async def _xs_tab_get(self, tab: Any, url: str) -> PydollResponse:
        await tab.get(url)
        await tab.cf()
        html_text = await tab.text()
        current_url = await self.req._get_current_url(tab, url)
        headers = self.req.browser.hd if self.req.browser is not None else {}
        return PydollResponse(text=html_text, url=current_url, headers=headers)

    async def _p1_work(self, p1_id: Any) -> list[Any]:
        if not self.config.p1_url:
            return [p1_id]

        page_url = self.config.format_p1_url(p1_id)

        response = await self._xs_get(page_url)
        if not response:
            return []

        parsed = await self.parser_manager.parse_html(self.parse_p1, response, page_url)
        if not isinstance(parsed, P1Result):
            raise TypeError("parse_p1 需要返回 P1Result")
        return parsed.items


    async def _fetch_p2(self, p2_items: Any) -> P2Result:
        if not self.config.p2_url:
            raise ValueError("config.p2_url 参数未设置")
        p2_id = getattr(p2_items, "url", p2_items)
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
                response = await self._xs_get(current_url)
                html_str = response.text
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
                raise No(f"获取 p2 出错: id={p2_id}, url={current_url}", e=exc)

        self._reindex_p3_items(all_p3s, title)
        return P2Result(
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

    async def _parse_p3_info(
        self,
        p3_id: int,
        p3: P3Item,
        p2_name: str,
        manager: XsManager,
    ) -> None:
        p3.url = self.config.format_p3_url(p3.url)
        current_url = p3.url
        chapter_title = p3.name
        chunks: list[str] = [p3.content] if p3.content else []

        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            try:
                response = await self._xs_get(current_url)
                html_str = response.text
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

Xs = Xs_

__all__ = ["Xs", "XsManager"]
