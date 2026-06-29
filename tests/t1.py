import asyncio

from ljp_page._module.request.session import ASession
from ljp_page._module.runtime.exc import LJPExc

session = ASession()

exc = LJPExc()
async def checker(res):
    # print(f'checker: {res}')
    return True

async def handler(res):
    print(f'handler:{res}')
    await asyncio.sleep(1)
    print(f'handler:验证完成')
    return True

session.verification_gate.set_verification(checker=checker,handler=handler)

async def t_test(i):
    url = 'https://www.baidu.com'

    await asyncio.sleep(0.0000000001)
    res = await session.get(url)
    print(f'第{i}哥响应:{res}')
    return res


async def main():
    ls = [t_test(i) for i in range(100)]
    rs = exc.submit_many(ls)
    mask = True
    tas = []
    for r in rs:
        if mask:
            tas = exc.submit_many([t_test(i) for i in range(10)])
            mask = False
        res = await r
        # print(f'res:{res}')

    for r in tas:
        res = await r
        # print(f'res:{res}')



    await exc.submit(session.close())
    exc.shutdown()


if __name__ == '__main__':
    asyncio.run(main())


