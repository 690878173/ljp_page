from ljp_page.request import Requests,create_session


url =  'https://apibi.cc/api/chapter?id=2530&chapterid=1'
session = create_session(
    "sync",
)
# req = Requests()
# res = req.get(url)
# print(res)
try:
    res = session.get(url)
    print(res.status_code)
    print(res.text)
    print(type(res.json()))
except Exception as e:
    print(e)


