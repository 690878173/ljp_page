"""工具函数。"""

from __future__ import annotations

import re


def _parse_cookie_string(s: str) -> dict[str, str]:
    """解析 'k1=v1; k2=v2' 格式的 cookie 字符串。"""
    cookies: dict[str, str] = {}
    for pair in s.split(";"):
        pair = pair.strip()
        if "=" in pair:
            k, v = pair.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def curl_to_requests(curl_str: str) -> tuple[str, dict[str, str], dict[str, str]]:
    """解析 curl 命令，提取 url、headers 与 cookies。"""
    curl_str = re.sub(r"\s+", " ", curl_str.strip())

    url_match = re.search(r"curl\s+(?:['\"]?)(.*?)(?:['\"]?)(?:\s|$)", curl_str, re.I)
    url = url_match.group(1).strip() if url_match else ""

    headers: dict[str, str] = {}
    for item in re.findall(r"-(?:H|header)\s*['\"](.*?)['\"]", curl_str, re.I):
        if ": " in item:
            k, v = item.split(": ", 1)
            headers[k.strip()] = v.strip()

    cookies: dict[str, str] = {}
    cookie_match = re.search(r"-(?:b|cookie)\s*['\"](.*?)['\"]", curl_str, re.I)
    if cookie_match:
        cookies = _parse_cookie_string(cookie_match.group(1))

    if "Cookie" in headers and not cookies:
        cookies = _parse_cookie_string(headers.pop("Cookie"))

    return url, headers, cookies


__all__ = ["curl_to_requests"]
