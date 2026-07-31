import asyncio

from ljp_page._module.request.brower.pydoll import Edge
from ljp_page.request.request import AsyncSession
edge = Edge()
async def main():
    session = AsyncSession()

    tab = await edge.start()
    hd = await edge.edge.get_version()
    print(hd)
    url = "https://www.bz888888888.com/"
    await tab.go_to(url)
    await tab.refresh()
    await tab.cf()
    cookies = await tab.cookies
    hd = edge.hd
    session.headers = hd
    session.cookies = cookies
    print(session.cookies)
    print(session.headers)
    tab = await edge.new_tab()
    await tab.go_to(url)
    await tab.cf()

    cookies = await tab.cookies
    hd = edge.hd
    session.headers = hd
    session.cookies = cookies
    print(session.cookies)
    print(session.headers)

    res = await session.get(url)
    print(res)
    print(res.text)

    await asyncio.sleep(5)
    await asyncio.sleep(5)
    await asyncio.sleep(5)
    await asyncio.sleep(5)
    await asyncio.sleep(5)




    await edge.close()


if __name__ == '__main__':
    asyncio.run(main())