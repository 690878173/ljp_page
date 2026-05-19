import asyncio
from pathlib import Path
from time import time
from urllib.parse import urlencode, urlsplit, urlunsplit


def _no_cache_url(url: str) -> str:
    parts = urlsplit(url)
    query = parts.query
    extra = urlencode({"_cf_refresh": str(int(time() * 1000))})
    query = f"{query}&{extra}" if query else extra
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", query, parts.fragment))


def ck(tx):
    for i in ['Just a moment', '请稍候']:
        if i in tx:
            return True
    return False

async def cf(url):
    from ljp_page.pc.edge.pydoll import Edge, ChromiumOptions
    profile_dir = (Path.cwd() / "edge_profile").resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    options = ChromiumOptions()
    options.headless = False
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")

    async with Edge(options=options) as browser:
        tab = await browser.start()
        await tab.delete_all_cookies()
        await tab.go_to(_no_cache_url(url))
        t = await tab.title
        while ck(t):
            await asyncio.sleep(2)
            t = await tab.title
            if ck(t):
                await tab.cf(time_to_wait_captcha=10)
        t = await tab.title
        cook = await tab.get_cookies()
        global cookie,bt_url
        bt_url = await tab.current_url
        cookie = {
            item.get('name'): item.get('value')
            for item in cook
            if item.get('name') and item.get('value') is not None
        }
        hd = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0'
        }
        print(cookie)
        await browser.close()
        return bt_url,cookie,hd
