import base64
import json
import re

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ljp_page._module.request.session import SyncSession as Requests
from ljp_page._module.ocr.ocr import Ocr

class JW:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82"
            ),
            "Accept-Encoding": "gzip, deflate",
        }
        self.login_is = False
        self.init_session()

    def out_init(self):
        self.req = Requests()
        self.session = self.req.ensure_session()
        self.ocr = Ocr()

    def init_session(self):
        self.out_init()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def url_get_host(self, url):
        if not url:
            return None
        return url.split("/")[2]

    def get_next_url(self, url, refer):
        self.headers["Host"] = self.url_get_host(url)
        self.headers["Referer"] = refer
        response = self.session.get(url, headers=self.headers, allow_redirects=False)
        return response.headers["Location"], url

    def init_login(self):
        print("初始化登录")
        url = "https://jw.v.hbfu.edu.cn/jsxsd/"
        next_url, refer = self.get_next_url(url, "")
        next_url, refer = self.get_next_url(next_url, refer)
        next_url, refer = self.get_next_url(next_url, refer)
        next_url, refer = self.get_next_url(next_url, refer)

        self.headers["Host"] = self.url_get_host(next_url)
        response = self.session.get(next_url, headers=self.headers, allow_redirects=False)
        pattern = r"var bridgeData = {.*?flowExecutionKey:(.*?),.*?errors"
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            self.execution = json.loads(match.group(1))
        return next_url

    def login(self):
        refer = self.init_login()
        print("登录")
        url = 'https://oa-443.v.hbfu.edu.cn/backstage/cas/captcha.jpg'
        res = self.session.get(url, headers=self.headers, allow_redirects=False)
        captcha = self.ocr.classification(res.content)

        def get_password(password):
            def qk(t: str, n: str, iv_value: str) -> str:
                plaintext = t.encode("utf-8")
                key = n.encode("utf-8")
                iv = iv_value.encode("utf-8")
                cipher = AES.new(key, AES.MODE_CBC, iv)
                padded_data = pad(plaintext, AES.block_size)
                ciphertext = cipher.encrypt(padded_data)
                return base64.b64encode(ciphertext).decode("ascii")

            if (password.startswith("phone_msg") and "###" in password) or password.startswith(
                "qrcode"
            ):
                return password
            return qk(password, "UH1eN7apoK9lY5VB", "VkRu0s6hLfFriZDW")

        url = "https://oa-443.v.hbfu.edu.cn/backstage/cas/login"
        data = {
            "username": self.username,
            "password": get_password(self.password),
            "execution": self.execution,
            "_eventId": "submit",
            "geolocation": "",
            "captcha": captcha,
            "rememberMe": "false",
            "domain": self.url_get_host(url),
            "tenantId": "",
        }

        self.headers["Host"] = self.url_get_host(url)
        self.headers["Referer"] = refer

        response = self.session.post(url, data=data, headers=self.headers, allow_redirects=False)
        next_url = response.headers.get("Location",'')

        self.headers["Host"] = self.url_get_host(next_url)
        self.headers["Referer"] = next_url
        response = self.session.get(next_url, headers=self.headers, allow_redirects=False)
        url = response.headers["Location"]
        next_url, refer = self.get_next_url(url, next_url)

        self.headers["Host"] = self.url_get_host(next_url)
        self.headers["Referer"] = refer
        self.session.get(next_url, headers=self.headers, allow_redirects=False)

        url = "https://jw.v.hbfu.edu.cn/jsxsd/xk/LoginToXk"
        self.headers["Host"] = self.url_get_host(url)
        self.headers["Origin"] = "https://jw.v.hbfu.edu.cn"
        self.headers["Referer"] = next_url
        data = {
            "encoded": self.encode_inp(self.username) + "%%%" + self.encode_inp(self.password)
        }
        response = self.session.post(url, data=data, headers=self.headers, allow_redirects=False)
        nt_url = response.headers["Location"]
        self.headers["Referer"] = url
        self.session.get(nt_url, headers=self.headers, allow_redirects=False)
        self.login_is = True
        print("登录成功")

    def get_course_grades(self, time):
        if not self.login_is:
            self.login()
        url = "https://jw.v.hbfu.edu.cn/jsxsd/kscj/cjcx_list"
        self.headers["Host"] = self.url_get_host(url)
        self.headers["Origin"] = "https://jw.v.hbfu.edu.cn"
        data = {
            "kksj": time,
            "kcxz": "",
            "kcmc": "",
            "xsfs": "all",
        }
        response = self.session.post(url, data=data, headers=self.headers, allow_redirects=False)
        html = etree.HTML(response.text)
        rows = html.xpath('//table[@id="dataList"]/tr')[1:]
        grades = {}
        for row in rows:
            name = row.xpath("./td[4]/text()")[0]
            score = row.xpath("./td[5]/text()")[0]
            grades[name] = score
        return grades

    def encode_inp(self, value):
        return base64.b64encode(value.encode("utf-8")).decode("utf-8")

    def get_cookies(self):
        if not self.login_is:
            self.login()
        return self.session.cookies.get_dict()

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv("env/jw.env")
    jw = JW(username=os.getenv('jw_username'),password=os.getenv('jw_password'))
    jw.login()


