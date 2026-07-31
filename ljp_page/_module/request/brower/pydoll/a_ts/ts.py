import asyncio
from pathlib import Path




def ck(tx):
    for i in ['Just a moment', '请稍候']:
        if i in tx:
            return True
    return False
cookie = {}
bt_url = ''

async def cf(url):
    from ljp_page.request.edge.pydoll import Edge, CookieParam, ChromiumOptions
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
        print(t)
        cook = await tab.get_cookies()
        print(cook)
        ck_ls = []
        for i in cook:
            ck_ls.append(CookieParam(**i))

        print(ck_ls)
        cqk = ck_ls[0]
        global cookie,bt_url
        bt_url = await tab.current_url
        cookie = {cqk.get('name'): cqk.get('value')}
        return bt_url,cookie

url = "https://www.bz11111111.com/shuku/0-size-0-45.html"
if __name__ == '__main__':
    asyncio.run(cf(url))
    from ljp_page.request.request import Requests

    session = Requests().create_session()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"147.0.3912.72"',
        'sec-ch-ua-full-version-list': '"Microsoft Edge";v="147.0.3912.72", "Not.A/Brand";v="8.0.0.0", "Chromium";v="147.0.7727.102"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        # 'cookie': 'cf_clearance=xUD8xD15fj.hY83YcoY_mc16N2uB6kCYdNi_t6wyNqM-1776884568-1.2.1.1-1mu3m3QR3O7v7WVuvdSfvJYNa1JhoEkn.wzzZgeNrSAEKMfUC8Qqcewl2rJlGE7VU8tGG5Pl9HkXPzkO4u9GxRqHVd8_FBi4PBhDFwBJG3pVhQfUAAtbOieDaY4pki2kAuzH21shxA66FtFAPQ8YDSLod.UxdZ4lzeynZgee7AzeI52kSc5FOV6FpdfuIG8bg5gm2.awf3n8Z7pBPZ.rKoFTcibc45JFXtdUdtTA4_yNaxEkIUBNFR750QFQvrx0Gk.NiMdg7HbVlM3.czHm2ihS1mlqbTV81zplF3BKCP0vdddTx3s2rSQIyl8R2QTRyRbwfHMzBq64aIQlLm.WEA',
    }
    headers.update({
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0'
    })
    session.headers = headers
    data = {
        'a2b1f9db4e9e6c6c798f9ded57ebfe58ec3465312bf1f304c85616991bf1040d': 'EyPq0qnpUmcSMlI7cI_ReRimC6b4IVVbyHMhwIU0fn8-1776884780-1.2.1.1-X8ePi.VuSaTyCz__sr7iaxjJPUBt6SpHhjl01QanJR9H5gBf8Pa7Dktb1MmiWk7bAE4spFUP0RvD.XaofYnodu2Y5jcLDxeTRGDFZW1umQU7VZkSHyAmY0YbxGJL_voDVynfwD7943fgFIu.4tEVjtxRGddiRWhulHcaKU9L_SJmnhvwua3Hnxm_wtJISx73tTCVkZxTbX0wp9ZPHt.dHbBT2GYySz5kF1VDw8h9kqREpmo2N3qjJRfqJKvxcgqUDeacQdmzZx2qJBygq2rC1vy2yGEuRY.ThNerNpk32f7S2hxXhcdHTrGtgodiIDj8aAukIDWHLPi3_Jic17zIsjE7O_XlY01ctTXFss4YeMij2b5Z3DCTr_63QQQnUCnhKugKEdbdANXhsdTTGN9sxR_qLMhnyY1xw5pULvLTFad1xEDRX5uZxALLBQ4Qz7uVhRuI6Pzl84E..0OytkjOXdNVcqfyukSsAILfJO44itcsyf7K0aeEU1Tl53670nWeEL9AzRj4.sW7m9cA0EdjOnLlxWNGvH0pmljzzVJ1HIv6T2xvJJkX5mDRmMbuY3gFhfe5KxyJr9G0UXSs1LX3kd4XI_w7MV.ww7dL5.ZX2oIj82flMuO2CliJuTHcuJb5RHWymqd39072a40XZuipEnPVoJrDBuGLU0N3T.mi7Y1Gm3prTyxqGgC_lOjDkis29MoR86oZIgQA0zdNO2VMPAq6kmphU97pJlNnfmrS6IL3MBmTpSm_h3uIAELUIrJWxvaQKZqiuYMmuhFIhPW1D1NP0CT.exDqlPnd23wNH3kj2HYbRMNXnJ4OjQu1YIPKbEVYfCkQ8Mwg1Av.4sRGF3NpZfcKPyBi1NjIMs9FUfcRZylnkmiTlwuoxcojn4HHfkunC0XsZarbsSv8I1rOjjHcq6ZRTmQNmlnb37IwMZfEsZqEEc4y0iTGAVQPnkq.H95WPT50_z.p_RdFuHYNb8sLyA83wzS6FycZrrsrJNlo26jPhmOCcrAioUdDOe4uxqGdFfx1GyETPAu068Pqgxn3wwnl4telbr8BIvKrvrvSIT2gzNkpfCJwRi5z3hyz',
        'bd68ad7e64e782c64df794b8af83443dc7097354607136ff4d7cd8aa9320a228': 'H035VspAW29PzlWd.qNr3JkKoU1MZbKke669qsrg1Wg-1776884780-1.2.1.1-vBLPJSLm.6bzF7EZjO5iG7uXBTqrdE_9hWs8L0ls6N8RhE4CJ4XCPOlP6SZwPqdI.Ux.eZXZ5.eEEs0mcJ5cT1PpMpl.SljBYeW1i2bgOrWvwwx0S9irU5513Vs010AUUHVK4sKc01eIclNADfEmopP1e_zxyBP8ay8_d7hqbbm36cvD6cX7DlYJk1QCXWYw8zMIOVm9i.MAq.WvU7_OkukpuHMB.MkDyiO38ptEQRm6fJ.7ovzXZc1lztXeRCycl1OFlNrLs78yTcl8lnCLDicSyf.aCV2wFNdXpZxcJ.bOS1z.vXU7qAvWCJjgIm6HCeweZWB7sPpja4pT4crne5IOL25OvvOnPZhI_0eX4Q8CwBNZJD3w4cPU6AqMVjCl51uVXwbLv5lREZJ.EVL18IaKa8RG_WAxI5o784Dav2qPC2gugw8apse5hHn9M2xf.p9mIuvUxIrSzNwbHdrXHxPdwq2JLSewtA4UmsXKLGWbOPsXqgjdXhJddHAzVz1P2zTZG5a5Yk19C5lfS5XPbGx6y2cIqgjSIfAcefdN8jviSMksOfySqBJctFDWNbOUv5R6erdaQsnv0hRsLxC5qdGKCLu_rjdbUhLIoAzBZmmXQ.uTBT2n0ZJZimxRSzzzAfxF5_SDzZWMWvcsLn9apcPpwZRrxNT9scYm.Lsr6cxuTG0unQnZUD.AcVYHnhJg3L3kDEi_o_stUX_MKaH4YYI1kHNf30Pja5av1aYL9.fZMxm3GN7LmlxQYHZ5EY1_4MTjMCoZCTqTmwjakn7Y8gK.iM5AOIs8lA61_rwseTmlZkzmtlFtYY2XpbNFBRBJ.deHkKmDRgRjWkxIdHieKQ2cC67Wa7gnahcggt9SQBXFzjmBtrKS42fC2_g_Rk3xza6KVqyTxv7sQeetFT3YF6ifQdDqY9riBTj1dlfHhZY',
        '5a578e71d532602516c848d95487004f53908cfd9c60af49b4e9ede86246cd7b': 'KvId20FAJ6PGsyQaLZJnUxLFbd9KVwqEpR5xa7SXhAA-1776884785-1.0.1.1-7hrSl5cL41GUDXOPW3XTqZO4Arg5KpsRRGnvgw0ltqz636oVhvDS_8EMlbdpF73fOoVsWj3Kh0jpNWxh0IvmG5w6AoVaL02BQP5l1kfc8HBDhNksU2zJtVtsYn1UVmLa1DdbdErKNJYPm6TMkrCAT_9OxxtB0M93vAo1uBvvLHSxhhWImCTGuE_81Cfl0AaG',
    }
    print(session.headers)
    print(cookie)
    print(url)
    res = session.get(bt_url, cookies=cookie)
    print(res)
    print(res.text)
    print(666)



