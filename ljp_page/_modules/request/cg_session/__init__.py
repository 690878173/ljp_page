
from .session import AsyncSession
from .sync_session import SyncSession
from .config import LjpConfig,LjpResponse,RequestContext,AdapterResponse,SessionPoolConfig,RetryConfig,RequestContext
from .fp import FP
from .html import Html

import re
def curl_to_requests(curl_str: str) -> tuple[str, dict, dict]:
    """
    解析curl命令，提取 url、headers、cookies
    兼容：浏览器复制的 curl、单引号/双引号、--header / -H、--cookie / -b、多行curl
    :param curl_str: 完整curl字符串
    :return: (url, headers_dict, cookies_dict)
    """
    # 统一清理换行、多余空格，避免多行curl出错
    curl_str = re.sub(r'\s+', ' ', curl_str.strip())

    # 1. 提取 URL（兼容单引号/双引号/无引号）
    url_pattern = re.compile(r'curl\s+(?:[\'"]?)(.*?)(?:[\'"]?)(?:\s|$)', re.I)
    url_match = url_pattern.search(curl_str)
    url = url_match.group(1).strip() if url_match else ""

    # 2. 提取 Headers（支持 -H / --header）
    headers = {}
    header_pattern = re.compile(r'-(?:H|header)\s*[\'\"](.*?)[\'\"]', re.I)
    header_items = header_pattern.findall(curl_str)

    for item in header_items:
        if ": " in item:
            key, value = item.split(": ", 1)
            headers[key.strip()] = value.strip()

    # 3. 提取 Cookies（支持 -b / --cookie，同时支持从 header 里的 Cookie 字段提取）
    cookies = {}
    # 优先从 -b 参数提取
    cookie_pattern = re.compile(r'-(?:b|cookie)\s*[\'\"](.*?)[\'\"]', re.I)
    cookie_match = cookie_pattern.search(curl_str)

    if cookie_match:
        cookie_str = cookie_match.group(1).strip()
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" in pair:
                ck, cv = pair.split("=", 1)
                cookies[ck.strip()] = cv.strip()

    # 兼容：很多 curl 把 Cookie 放在 -H 里，这里自动补抓
    if "Cookie" in headers and not cookies:
        cookie_str = headers.pop("Cookie")
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" in pair:
                ck, cv = pair.split("=", 1)
                cookies[ck.strip()] = cv.strip()

    return url, headers, cookies



__all__ = [
    "AsyncSession",
    'SyncSession',
    'LjpConfig',
    'LjpResponse',
    "RequestContext",
    'RetryConfig',
    'AdapterResponse',
    'SessionPoolConfig',
    'Html',
    'FP',
    'curl_to_requests'
]