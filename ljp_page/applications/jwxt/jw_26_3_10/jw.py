from ljp_page.request import Requests
# 什么都还未开始



class JW:
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82',
            "Accept-Encoding": "gzip, deflate",
            }
        self.login_is = False
        self.init_session()

    def out_init(self):
        self.req = Requests()
        self.session = self.req.create_session()

    def init_session(self):
        # self.session = requests.session()
        # 配置重试策略
        retries = Retry(
            total=3,  # 总共重试3次
            backoff_factor=1,  # 每次重试的退避因子（等待时间）：1→2→4秒
            status_forcelist=[500, 502, 503, 504],  # 遇到这些状态码时重试
            allowed_methods=["GET", "POST"]  # 允许重试的请求方法
        )

        # 将重试策略应用到所有 HTTP 和 HTTPS 请求
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def url_get_host(self,url):
        return url.split('/')[2]

    def get_next_url(self,url,refer):
        self.headers['Host'] = self.url_get_host(url)
        self.headers['Referer'] = refer
        response = self.session.get(url, headers=self.headers, allow_redirects=False)
        return response.headers['Location'],url
    def init_login(self):
        print('初始化登录')
        url = 'https://jw.v.hbfu.edu.cn/jsxsd/'
        next_url,refer = self.get_next_url(url,'') # https://v.hbfu.edu.cn:443/vpn_key/update?origin=https%3A%2F%2Fjw.v.hbfu.edu.cn%2Fjsxsd%2F&reason=site+jw.v.hbfu.edu.cn+not+found

        next_url,refer = self.get_next_url(next_url,refer) # https://v.hbfu.edu.cn/users/sign_in

        next_url,refer =self.get_next_url(next_url,refer) # https://v.hbfu.edu.cn/users/auth/cas

        next_url,refer = self.get_next_url(next_url,refer) # https://oa-443.v.hbfu.edu.cn/backstage/cas/login?service=https%3A%2F%2Fv.hbfu.edu.cn%2Fusers%2Fauth%2Fcas%2Fcallback%3Furl

        self.headers['Host'] = self.url_get_host(next_url)
        response = self.session.get(next_url, headers=self.headers, allow_redirects=False)
        pattern = r'var bridgeData = {.*?flowExecutionKey:(.*?),.*?errors'
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            self.execution = json.loads(match.group(1))
        return next_url

    def login(self):
        refer = self.init_login()
        print('登录')
        def get_password(password):
            def qk(t: str, n: str, l: str) -> str:
                """
                等效于 JavaScript 中的 qk 函数
                使用固定 IV 进行 AES-CBC 加密，返回 Base64 编码的密文
                """
                # 将输入转换为 bytes
                plaintext = t.encode('utf-8')
                key = n.encode('utf-8')
                iv = l.encode('utf-8')

                # 创建 AES-CBC 加密器
                cipher = AES.new(key, AES.MODE_CBC, iv)

                # 对明文进行 PKCS7 填充并加密
                padded_data = pad(plaintext, AES.block_size)
                ciphertext = cipher.encrypt(padded_data)

                # 返回 Base64 编码的密文
                return base64.b64encode(ciphertext).decode('ascii')

            if (password.startswith('phone_msg') and '###' in password) or (password.startswith('qrcode')):
                return password
            return qk(password, 'UH1eN7apoK9lY5VB', 'VkRu0s6hLfFriZDW')
        url = 'https://oa-443.v.hbfu.edu.cn/backstage/cas/login'
        data = {
            'username': self.username,  # 原始
            'password': get_password(self.password),  # 加密
            'execution': self.execution,  # 未知
            '_eventId': 'submit',
            'geolocation': '',  # 空
            'captcha': '',  # 空
            'rememberMe': 'false',
            'domain': self.url_get_host(url),
            'tenantId': ''
        }

        self.headers['Host'] = self.url_get_host(url)
        self.headers['Referer'] = refer

        response = self.session.post(url, data=data, headers=self.headers, allow_redirects=False)
        next_url = response.headers['Location'] # https://v.hbfu.edu.cn/users/auth/cas/callback?url&ticket=ST-79197-GDSWyKZF2myjXm0aSFrCLXzpRBYcas-v401052-6b5dc95f88-pdxcw

        self.headers['Host'] = self.url_get_host(next_url)
        self.headers['Referer'] = next_url
        response = self.session.get(next_url, headers=self.headers, allow_redirects=False)
        url = response.headers['Location'] # https://v.hbfu.edu.cn/vpn_key/update
        next_url,refer = self.get_next_url(url,next_url) # https://jw.v.hbfu.edu.cn/jsxsd/

        self.headers['Host'] = self.url_get_host(next_url)
        self.headers['Referer'] = refer
        response = self.session.get(next_url, headers=self.headers, allow_redirects=False)

        url = 'https://jw.v.hbfu.edu.cn/jsxsd/xk/LoginToXk'
        self.headers['Host'] = self.url_get_host(url)
        self.headers['Origin'] = 'https://jw.v.hbfu.edu.cn'
        self.headers['Referer'] = next_url
        data = {
            'encoded': self.encode_inp(username)+ "%%%"+ self.encode_inp(password)
        }
        response = self.session.post(url, data=data, headers=self.headers, allow_redirects=False)
        nt_url = response.headers['Location'] # https://jw.v.hbfu.edu.cn/jsxsd/framework/xsMain.jsp
        self.headers['Referer'] = url
        response = self.session.get(nt_url, headers=self.headers, allow_redirects=False)
        self.login_is = True
        print('登录成功')

    def get_course_grades(self,time):
        if not self.login_is:
            self.login()
        url = 'https://jw.v.hbfu.edu.cn/jsxsd/kscj/cjcx_list'
        self.headers['Host'] = self.url_get_host(url)
        self.headers['Origin'] = 'https://jw.v.hbfu.edu.cn'
        data = {
            'kksj': time,
            'kcxz': '',
            'kcmc': '',
            'xsfs': 'all'
        }
        response = self.session.post(url, data=data, headers=self.headers, allow_redirects=False)
        html = etree.HTML(response.text)
        ls=  html.xpath('//table[@id="dataList"]/tr')[1:]
        s = {}
        for i in ls:
            name = i.xpath('./td[4]/text()')[0]
            cj = i.xpath('./td[5]/text()')[0]
            s[name] = cj
        return s

    def encode_inp(self,s):
        return base64.b64encode(s.encode("utf-8")).decode("utf-8")

    def get_cookies(self):
        if not self.login_is:
            self.login()
        return self.session.cookies.get_dict()