import asyncio
from pathlib import Path
def ck(tx):
    for i in ['Just a moment', '请稍候']:
        if i in tx:
            return True
    return False

async def cf(url):
    from ljp_page.edge.pydoll import Edge, CookieParam, ChromiumOptions
    profile_dir = (Path.cwd() / "edge_profile").resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    options = ChromiumOptions()
    options.headless = False
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")

    async with Edge(options=options) as browser:
        tab = await browser.start()
        await tab.go_to(url)
        t = await tab.title
        while ck(t):
            await asyncio.sleep(2)
            t = await tab.title
            if ck(t):
                await tab.cf(time_to_wait_captcha=10)
        t = await tab.title
        cook = await tab.get_cookies()
        ck_ls = []
        for i in cook:
            ck_ls.append(CookieParam(**i))

        cqk = ck_ls[0]
        global cookie,bt_url
        bt_url = await tab.current_url
        cookie = {cqk.get('name'): cqk.get('value')}
        hd = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0'
        }
        print(cookie)
        return bt_url,cookie,hd
