# 04-01-20-58-00
import json

from ljp_page.out.pc import Mode, PcConfig
from ljp_page._core.config import RetryConfig
from ljp_page._core.config import TimeoutConfig
from ljp_page.out.pc import Xs
from ljp_page.out.request import RequestConfig,LjpConfig
from ljp_page.out.logger import LogConfig


class Ts(Xs):
    def parse_p2(self, res_html: str, url: str):
        s = json.loads(res_html)
        title = s.get("title")
        author = s.get("author")
        intro = s.get("intro")
        lastchapterid = s.get("lastchapterid")

        b_id = url.split("id=")[-1]
        s = f"https://apibi.cc/api/chapter?id={b_id}&chapterid="
        return self.P2ParseResult(
            title=title,
            author=author,
            description=intro,
            p3s=[("", s + str(i)) for i in range(1, int(lastchapterid) + 1)],
            next_url=None,
        )

    def parse_p3(self, res_html: str, url: str):
        res_dict = json.loads(res_html)
        title = res_dict["chaptername"]
        content = res_dict["txt"]

        return self.P3ParseResult(title=title, content=content, next_url=None)


def _build_pc_config() -> PcConfig:
    req_cfg = LjpConfig(
        request=RequestConfig(base_url="https://www.bqg291.cc/"),
        timeout=TimeoutConfig(connect=10, read=10),
        retry=RetryConfig(total=3),
        log=LogConfig(enabled_levels=[i for i in range(2, 20)]),
    )
    return PcConfig(
        base_url="https://www.bqg291.cc/",
        save_path=r"J:\pppppppppppppppppc\books",
        p2_url="https://apibi.cc/api/book?id={}",
        mode=Mode.MODE1,
        id_ls=[i for i in range(1010, 1011)],
        ljp_config=req_cfg,
    )


def main() -> None:
    cfg = _build_pc_config()
    print(cfg)
    spider = Ts(cfg)
    spider.run(blocking=True)


if __name__ == "__main__":
    main()
