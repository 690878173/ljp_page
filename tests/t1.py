from ljp_page.pc import Dybz,PcConfig
from ljp_page._modules.request.other.Config import LjpConfig,RequestConfig
import asyncio
cookies = {'cf_clearance': 'VmMgwC5IwMxchE_BSkrYB74cz8qu5v7vs9W9nhgNgIE-1776890756-1.2.1.1-hr1XLNhs0jbq26UIZNsq39k5DAFCLk7Snleatm3O4F6arq8oYv0GvoL9BG7JR1C1G7flSPY1g1NFu6u3SSct2fExNnG90Cj2lUdploFPw.1vFsMsyWidDpgb2aozDcv42J.5Iv5HNPr8mpdD0wH4b2CDwHsRTcgBfbMfnmrT2hFx8SCf_mCOnw7xIXS0f4Ifb53w_uiSigKsmCIP4V7udyPhDqJ.Cx0WxvRpUDLn7CnKZjbkZ1vGY8m3OSAFdHF4NgjY7V_tZ01II5okU5UwHrfJHvzWXef_q0FqWdHY88tRk4wKcBt1pGDx6bDmoRCAM20SshqKJarAoTqHnQOFZw'}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://www.bz999999999.com/24/24099/?__cf_chl_tk=Zsca6d9Ov1UI27ER7UnjCvtJYRbNzxql39r_ODm0rmI-1776888995-1.0.1.1-BJiv89Aps92wwIhP7Z6y62OqwS9yWsOOMXURgrSeiGA',
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
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
    # 'cookie': 'cf_clearance=tKBLtW75DpkcT2iPVPjLIy_zvtNyQWW6_sgG0bc8cQA-1776889003-1.2.1.1-0dvtPHMblPrwbDW6FZO_7lxAfYNUyRGTGyHbz2ZXHtnYfsrBLXRGi6wOpxJvzfehbOGAjsW4y0RgzrAn62p1ZZFcqRFRUm_pMB._giaMqprJGlK5KQI3kkPajXGHOrB5lW0NBnmuoG8LCFOgqJmTYd.hihWBjZeZtCAhfkGiGR8PgEbvyEJtzVtYoFZc67P8ciC8mK6287t491XSflBNbqv_r0vxIv.itR_WQ0cqmuwJf4_XPSOiBjf2dkufV2PSe4tFcU7oIWsAV1V6xXg6vnVmdoIzqtQnARPiDTmSUsLLgImIMDONtDvVfzPE1JD28sgcpMp19vWKFcvQHMmBVg',
}
async def main():

    from ljp_page.edge.pydoll import cf
    base_url = 'https://www.bz999999999.com/'
    ul,cookies,hd = await cf(base_url)
    headers.update(hd)
    cg = PcConfig(
        base_url="https://www.bz999999999.com/",
        save_path=r'J://xs',
        p1_url='https://www.bz999999999.com/shuku/0-size-0-{}.html',
        p2_url='https://www.bz999999999.com{}',
        mode='mode2',
        start_id=1,
        end_id=5,
        ljp_config=LjpConfig(request=RequestConfig(cookies=cookies,headers=headers)),
                                                   )

    s = Dybz(cg)
    s.run()

asyncio.run(main())



