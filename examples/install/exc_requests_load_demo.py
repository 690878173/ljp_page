import asyncio

from ljp_page.runtime.ljp_exc import LJPExc
from ljp_page.request import Requests

exc = LJPExc()
req = Requests()


async def get_url(url, session):
    async with session.get(url) as response:
        return await response.text()


async def main():
    session = await req.async_create_session()
    try:
        handles = exc.submit_many_inside(
            [exc.bind(get_url, "https://www.baidu.com", session) for _ in range(200)],
            mode="async",
        )
        return [await handle for handle in handles]
    finally:
        await session.close()


handle = exc.submit(main, mode="async")
results = handle.result()
for result in results:
    print(result)
print(len(results))
exc.shutdown()
