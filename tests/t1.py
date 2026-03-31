from ljp_page.request import Requests,create_session


url =  'https://www.baidu.com'
session = create_session(
    "sync",
    log={
        "enabled_levels": [10, 15, 19,5],  # 只输出 warrior/error/critical
        "default_level": 10,
    },
)
# req = Requests()
# res = req.get(url)
try:
    res = session.get(url)
    print(res.status_code)
except Exception as e:
    print(e)


