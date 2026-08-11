import time

from ljp_page.request.session import __all__,AsyncSession,CurlCffiAdapter
from ljp_page.exc import LJPExc,BindTask

from curl_cffi import requests as curl_req


exc = LJPExc()
session = AsyncSession(adapter=CurlCffiAdapter())
async def ts1():
    res = await session.get('https://baidu.com')
    print(res)
    s = exc.submit_inside(xc)
    await s
    # print(s.result())

def xc():
    time.sleep(2)
    print('执行完毕')
    return 4


ts_ls = [BindTask(ts1) for i in range(100)]



def run():
    sem = exc.create_semaphore(100)


    el = exc.submit_many_inside(ts_ls,semaphore=sem)
    for i in el:
        i.result()


def call_b(self):
    print('执行回调')
    print(self)

s = exc.submit(run,callback=call_b)
s.result()
exc.wait_all_tasks()
s = exc.submit(session.close)
s.result()


print(7777)
exc.shutdown()
print(6666)
