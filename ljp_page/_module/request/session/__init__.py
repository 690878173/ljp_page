import re
from typing import TYPE_CHECKING

from ljp_page._core.utils.lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    # from .base import *  # noqa: F403
    from .session import ASession
    from .sync_session import SyncSession
    from .config import *


def curl_to_requests(curl_str: str) -> tuple[str, dict, dict]:
    """解析 curl 命令，提取 url、headers 与 cookies。"""

    # 统一清理换行与多余空白，兼容浏览器复制的多行 curl。
    curl_str = re.sub(r"\s+", " ", curl_str.strip())

    url_pattern = re.compile(r"curl\s+(?:[\'\"]?)(.*?)(?:[\'\"]?)(?:\s|$)", re.I)
    url_match = url_pattern.search(curl_str)
    url = url_match.group(1).strip() if url_match else ""

    headers = {}
    header_pattern = re.compile(r"-(?:H|header)\s*[\'\"](.*?)[\'\"]", re.I)
    header_items = header_pattern.findall(curl_str)
    for item in header_items:
        if ": " in item:
            key, value = item.split(": ", 1)
            headers[key.strip()] = value.strip()

    cookies = {}
    cookie_pattern = re.compile(r"-(?:b|cookie)\s*[\'\"](.*?)[\'\"]", re.I)
    cookie_match = cookie_pattern.search(curl_str)
    if cookie_match:
        cookie_str = cookie_match.group(1).strip()
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" in pair:
                ck, cv = pair.split("=", 1)
                cookies[ck.strip()] = cv.strip()

    if "Cookie" in headers and not cookies:
        cookie_str = headers.pop("Cookie")
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" in pair:
                ck, cv = pair.split("=", 1)
                cookies[ck.strip()] = cv.strip()

    return url, headers, cookies


_lazy_getattr, __all__ = bind_lazy_exports(__name__, __file__)
__all__.append("curl_to_requests")


def __getattr__(name: str) -> object:
    if name == "curl_to_requests":
        return curl_to_requests
    return _lazy_getattr(name)
