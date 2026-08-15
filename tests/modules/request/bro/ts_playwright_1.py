import asyncio

from ljp_page.request.edge.playwright import Playwright,BrowserLaunchConfig
from ljp_page._module.request.brower.base.ljp_fp.mouse import MouseAPI


edge = Playwright(
    BrowserLaunchConfig(headless=False)
)

async def run():
    await edge.start()
    page = await edge.new_page()

    url = 'https://www.chewy.com/'

    await page.goto(url)



    s = await page.title
    print(s)
    await asyncio.sleep(5)
    s = await page.cookies

    print(s)
    dic = {}
    for k in s:
        dic[k['name']] = k['value']



    print(dic)


    s = await page.goto('https://www.chewy.com/dreambone-collayums-twists-plus/dp/3254342')
    s = await page.content

    print(s)

    s = page.url

    print(s)

    s = await page.content


    s = await page.is_cf_challenge()

    print(s)

    # if s:
    #     await page.cf()

    s = await page.title
    print(s)



    fs = page.frames

    for f in fs:
        print(f)

    # mouse = MouseAPI(page,debug=True)

    print(666)
    # import random
    # x = 200
    # y = 200
    # for i in range(100):
    #     x += random.randint(-100,100)
    #     y += random.randint(-100,100)
    #     await mouse.move(x,y,humanize=True)


    from ljp_page._module.request.brower.base.commands.dom_commands import DomCommands

    session = await page.get_cdp_session()
    res = await session.send(**DomCommands.get_document(depth=-1, pierce=True))






    print(777)
    #
    #
    #
    #
    # def _1(res):
    #     print('需要验证')
    #     return True
    #
    # def _2(ctx):
    #     print(f'执行验证')
    #     return ctx
    #
    # page.verify_gate.configure(checker=_1,handler=_2)
    #
    # print(page.fetch.verify_gate._checker)
    #
    # s = await page.fetch.get(url)
    # for k, v in s.items():
    #     print(k)
    #
    # page.fetch.verify_gate._checker(s)


    await edge.close()


if __name__ == '__main__':
    asyncio.run(run())










