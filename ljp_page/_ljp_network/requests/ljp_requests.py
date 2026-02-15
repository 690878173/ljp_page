import inspect
import time
from dataclasses import dataclass
import aiohttp
import asyncio
import random
import requests
from lxml import etree
from typing import Optional, Dict, Any, Callable, Union

from ..._ljp_coro.base_class import Ljp_BaseClass
from ..._ljp_coro.exceptions import (
    CaptchaException,
    NetworkException,
    TimeoutException,
    ProxyException,
    HTTPStatusException,
    EncodingException,
    SSLException,
    ResponseParseException,
    MaxRetriesException, No, MeetCheckError
)




class BaseRequests(Ljp_BaseClass):
    """HTTP请求基类，提供公共功能"""
    
    @dataclass
    class Config:
        """
        HTTP 请求配置类
        包含代理列表、最大重试次数、超时时间、Cookies、请求头等配置项，并提供合法性校验
        """
        proxy_list: list[str] | None = None
        max_retries: int = 3
        timeout: float = 10.0
        cookies: dict | None = None
        headers: dict | None = None
        delay: float = 0.0

        def __post_init__(self) -> None:
            if self.headers is None:
                self.headers = {}
            if self.cookies is None:
                self.cookies = {}

            if self.proxy_list:
                if not isinstance(self.proxy_list, list):
                    raise TypeError("proxy_list 必须是列表类型")
                for idx, proxy in enumerate(self.proxy_list):
                    if not isinstance(proxy, str):
                        raise TypeError(f"proxy_list 第 {idx + 1} 个元素 {proxy} 必须是字符串类型")
                    if not proxy.startswith(('http://', 'https://')):
                        raise ValueError(f"proxy_list 第 {idx + 1} 个代理 {proxy} 必须以 http:// 或 https:// 开头")

            if not isinstance(self.max_retries, int) or self.max_retries < 0:
                raise ValueError(
                    f"max_retries 必须为非负整数，当前传入：{self.max_retries}（类型：{type(self.max_retries).__name__}）")

            if not (isinstance(self.timeout, (int, float)) and self.timeout > 0):
                raise ValueError(
                    f"timeout 必须为大于 0 的数字，当前传入：{self.timeout}（类型：{type(self.timeout).__name__}）")

    def __init__(self, config: Config, logger=None):
        super().__init__(logger=logger)
        self.config = config or self.Config()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.73',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0'
        ]
        self.default_headers = {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = None
        self.encoding = 'utf-8'
        self._init()
    
    def _init(self):
        """初始化headers"""
        self.headers = self.default_headers.copy()
        self.headers.update(self.config.headers)

    def get_cookies(self, session):
        """获取会话的cookies（支持同步/异步会话）"""
        res = {}
        if isinstance(session, aiohttp.ClientSession):
            try:
                for cookie in session.cookie_jar:
                    res[cookie.key] = cookie.value
            except Exception as e:
                self.error(f'获取aiohttp会话cookies失败: {e}', self.get_cookies.__name__)
        elif isinstance(session, requests.Session):
            return session.cookies.get_dict()
        else:
            self.error(f'{self.name(self.get_cookies)}不支持的会话类型，无法获取cookies', self.get_cookies.__name__)
        return res

    def update_cookies(self, session, cookies):
        """更新会话的cookies（支持同步/异步会话）"""
        if isinstance(session, aiohttp.ClientSession):
            session.cookie_jar.update_cookies(cookies)
        elif isinstance(session, requests.Session):
            session.cookies.update(cookies)
        else:
            self.error(f'{self.name(self.update_cookies)}:不支持的会话类型，无法更新cookies', self.update_cookies.__name__)

    def get_headers(self, session):
        """获取会话的headers（支持同步/异步会话）"""
        if isinstance(session, aiohttp.ClientSession):
            return dict(session.headers) if session.headers else {}
        elif isinstance(session, requests.Session):
            return dict(session.headers) if session.headers else {}
        else:
            self.error(f'不支持的会话类型，无法获取headers,实际类型:{type(session).__name__}', self.get_headers.__name__)
            return {}

    @staticmethod
    def meet_yzm(html_str: str) -> bool:
        """检测是否遇到验证码页面"""
        if '<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>' in html_str:
            return True
        return False

    def _decode_response_text(self, content: bytes, url: str, res_encoding: Optional[str] = None, charset: Optional[str] = None) -> str:
        """解码响应文本"""
        encodings_to_try = [res_encoding] if res_encoding else []
        encodings_to_try.extend(['utf-8', 'gbk', 'gb18030'])

        # 尝试从Content-Type头获取编码
        if charset and charset not in encodings_to_try:
            encodings_to_try.insert(0, charset)

        text = None
        for enc in encodings_to_try:
            if not enc:
                continue
            try:
                text = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            text = content.decode('utf-8', errors='replace')
            self.error(f'解码失败，已使用replace模式，url：{url}', self._decode_response_text.__name__)

        if not text and len(content) > 0:
            self.error(f'解码后内容为空但原始内容不为空，url：{url}', self._decode_response_text.__name__)

        return text

    def _init_request_decorator(self, func: Callable) -> Callable:
        """请求装饰器工厂：处理请求前的参数预处理"""
        def wrapper(*args, **kwargs):
            if len(args) >= 2 and isinstance(args[0], str) and args[0].upper() in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
                method, url = args[0], args[1]
                remaining_args = args[2:]
            else:
                method, url = None, (args[0] if len(args) > 0 else kwargs.pop('url', ''))
                remaining_args = args[1:]
            session = kwargs.pop('session', None)
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                self.error(f'{self.name(func)}:url参数必须是有效的URL字符串,实际url:{url}', func.__name__)
                raise ValueError(f'{self.name(func)}:url参数必须是有效的URL字符串,实际url:{url}')
            headers = {**self.headers, **self.get_headers(session)}
            headers = {**headers, **kwargs.pop('headers', {})}
            timeout = kwargs.pop('timeout', self.config.timeout)
            delay = kwargs.pop('delay', self.config.delay)
            retries = kwargs.pop('retries', self.config.max_retries)
            cookies = kwargs.pop('cookies', self.get_cookies(session))
            if method:
                return func(method, url, headers=headers, cookies=cookies, session=session,
                           timeout=timeout, delay=delay, retries=retries, *remaining_args, **kwargs)
            else:
                return func(url, headers=headers, cookies=cookies, session=session,
                           timeout=timeout, delay=delay, retries=retries, *remaining_args, **kwargs)

        async def async_wrapper(*args, **kwargs):
            if len(args) >= 2 and isinstance(args[0], str) and args[0].upper() in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
                method, url = args[0], args[1]
                remaining_args = args[2:]
            else:
                method, url = None, (args[0] if len(args) > 0 else kwargs.pop('url', ''))
                remaining_args = args[1:]
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                self.error(f'{self.name(func)}:url参数必须是有效的URL字符串,实际url:{url}', func.__name__)
                raise ValueError(f'{self.name(func)}:url参数必须是有效的URL字符串,实际url:{url}')
            headers = {**self.headers, **kwargs.pop('headers', {})}
            session = kwargs.pop('session', None)
            headers = {**self.get_headers(session), **headers}
            timeout = kwargs.pop('timeout', self.config.timeout)
            delay = kwargs.pop('delay', self.config.delay)
            retries = kwargs.pop('retries', self.config.max_retries)
            if delay > 0:
                await asyncio.sleep(delay)
            proxy = random.choice(self.config.proxy_list) if self.config.proxy_list else None
            if method:
                return await func(method, url, headers=headers, session=session, timeout=timeout,
                                delay=delay, retries=retries, proxy=proxy, *remaining_args, **kwargs)
            else:
                return await func(url, headers=headers, session=session, timeout=timeout,
                                delay=delay, retries=retries, proxy=proxy, *remaining_args, **kwargs)
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    def _init_session_decorator(self, func: Callable) -> Callable:
        """会话创建装饰器工厂：处理会话创建前的参数预处理"""
        def wrapper(**kwargs):
            cookies = kwargs.pop('cookies', self.config.cookies)
            headers = kwargs.pop('headers', None)
            return func(cookies=cookies, headers=headers, **kwargs)

        async def async_wrapper(**kwargs):
            cookies = kwargs.pop('cookies', self.config.cookies)
            headers = kwargs.pop('headers', None)
            # if headers is None:
            #     headers = self.headers
            limit = kwargs.pop('limit', 0)
            limit_per_host = kwargs.pop('limit_per_host', 100)
            verify_ssl = kwargs.pop('verify_ssl', True)
            timeout = kwargs.pop('timeout', self.config.timeout)
            return await func(cookies=cookies, headers=headers, limit=limit, 
                            limit_per_host=limit_per_host, verify_ssl=verify_ssl, 
                            timeout=timeout, **kwargs)
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper


class TBRequests(BaseRequests):
    """同步HTTP请求类（同步/同步）"""
    
    def __init__(self, config: BaseRequests.Config, logger=None):
        super().__init__(config, logger)
        self._sync_request = self._init_request_decorator(self._sync_request)
        self.create_session = self._init_session_decorator(self._create_session)

    def _create_session(self, cookies: Dict, headers: Dict) -> requests.Session:
        """创建同步会话对象核心逻辑"""
        session = requests.Session()
        if cookies:
            session.cookies.update(cookies)
        if headers:
            session.headers.update(headers)
        else:
            session.headers.update(self.default_headers)
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
        })
        return session

    def create_session(self, cookies: Dict = None, headers: Dict = None) -> requests.Session:
        """创建同步会话对象"""
        try:
            return self._create_session(cookies, headers)
        except Exception as e:
            self.error(f'create_session:创建会话失败，错误信息：{e}', self.create_session.__name__)
            raise Exception(f'create_session:创建会话失败，错误信息：{e}')

    def _sync_request(self, method: str, url: str, headers: Dict = None, cookies: Dict = None,
                     session: requests.Session = None, timeout: float = None, delay: float = None,
                     retries: int = None, return_type: str = 'text', **kwargs) -> Optional[Any]:
        """同步请求核心方法"""
        f_name=  self. _sync_request.__name__
        for attempt in range(retries + 1):
            try:
                if session:
                    response = session.request(method, url, headers=headers, cookies=cookies,
                                              timeout=timeout, **kwargs)
                else:
                    response = requests.request(method, url, headers=headers, cookies=cookies,
                                               timeout=timeout, **kwargs)
                
                if response.status_code in [403, 404, 500, 502, 504, 520]:
                    error_msg = f"HTTP错误 {response.status_code} {response.reason}"
                    raise HTTPStatusException(error_msg, url=url, status_code=response.status_code, reason=response.reason)
                
                if return_type == 'content':
                    return response.content
                elif return_type == 'json':
                    return response.json()
                elif return_type == 'text':
                    content = response.content
                    text = self._decode_response_text(content, url)
                    
                    if self.meet_yzm(text):
                        raise CaptchaException(f'检测到验证码，url：{url}')
                    
                    return text
                else:
                    raise ValueError(f"不支持的return_type类型 {return_type}")
                    
            except requests.Timeout as e:
                if attempt < retries:
                    self.warning(f"请求 {url} 超时，第 {attempt + 1} 次重试: {str(e)}",f_name)
                    import time
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"请求 {url} 超时，已达最大重试次数: {str(e)}",f_name)
                    raise TimeoutException(f"请求超时，已达到最大重试次数 {retries} 次", url=url, timeout=timeout, e=e)
            except requests.ConnectionError as e:
                if attempt < retries:
                    self.warning(f"请求 {url} 连接失败，第 {attempt + 1} 次重试: {str(e)}",f_name)
                    import time
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"请求 {url} 连接失败，已达最大重试次数: {str(e)}",f_name)
                    raise NetworkException(f"网络连接失败，已达到最大重试次数 {retries} 次", url=url, e=e)
            except requests.exceptions.SSLError as e:
                if attempt < retries:
                    self.warning(f"请求 {url} SSL错误，第 {attempt + 1} 次重试: {str(e)}",f_name)
                    import time
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"请求 {url} SSL错误，已达最大重试次数: {str(e)}",f_name)
                    raise SSLException(f"SSL证书验证失败，已达到最大重试次数 {retries} 次", url=url, e=e)
            except requests.HTTPError as e:
                if attempt < retries:
                    self.warning(f"请求 {url} HTTP错误，第 {attempt + 1} 次重试: {str(e)}",f_name)
                    import time
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"请求 {url} HTTP错误，已达最大重试次数: {str(e)}",f_name)
                    raise HTTPStatusException(f"HTTP请求失败，已达到最大重试次数 {retries} 次", url=url, e=e)
            except requests.exceptions.ProxyError as e:
                if attempt < retries:
                    self.warning(f"请求 {url} 代理错误，第 {attempt + 1} 次重试: {str(e)}",f_name)
                    import time
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"请求 {url} 代理错误，已达最大重试次数: {str(e)}",f_name)
                    raise ProxyException(f"代理连接失败，已达到最大重试次数 {retries} 次", proxy=str(e), e=e)
            except requests.exceptions.JSONDecodeError as e:
                self.error(f"请求 {url} JSON解析失败: {str(e)}",f_name)
                raise ResponseParseException(f"JSON响应解析失败", url=url, parse_type='json')
            except CaptchaException as e:
                self.error(f'验证码报错：！！！！！！！！！{e}',f_name)
                return None
            except Exception as e:
                if attempt < retries:
                    self.warning(f"请求 {url} 失败，第 {attempt + 1} 次重试: {str(e)}",f_name)
                    import time
                    time.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f'!!!!!!!!!!{method}:未知错误，错误信息：{e}，url：{url}',f_name)
                    raise MaxRetriesException(f"请求失败，已达到最大重试次数 {retries} 次", url=url, max_retries=retries, e=e)
        return None

    def get(self, url: str, session: requests.Session = None, **kwargs) -> Optional[Any]:
        """GET请求"""
        return self._sync_request('GET', url, session=session, **kwargs)

    def post(self, url: str, session: requests.Session = None, **kwargs) -> Optional[Any]:
        """POST请求"""
        return self._sync_request('POST', url, session=session, **kwargs)


class YBRequests(BaseRequests):
    """异步HTTP请求类（异步/异步）"""
    
    def __init__(self, config: BaseRequests.Config, logger=None):
        super().__init__(config, logger)
        self._async_request = self._init_request_decorator(self._async_request)

    async def _create_session(self, limit: int, limit_per_host: int, cookies: Dict,
                            headers: Dict, verify_ssl: bool, timeout: float) -> aiohttp.ClientSession:
        """创建异步会话对象核心逻辑"""
        actual_timeout = timeout if timeout is not None else self.config.timeout
        connector = aiohttp.TCPConnector(limit=limit, limit_per_host=limit_per_host, verify_ssl=verify_ssl)
        session = aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            cookies=cookies if cookies else self.config.cookies,
            timeout=aiohttp.ClientTimeout(total=actual_timeout * 3, connect=actual_timeout),
            proxy=random.choice(self.config.proxy_list) if self.config.proxy_list else None,
            trust_env=True
        )
        return session

    async def create_session(self, limit: int = 0, limit_per_host: int = 100, cookies: Dict = None,
                           headers: Dict = None, verify_ssl: bool = True, timeout: float = None) -> aiohttp.ClientSession:
        """创建异步会话对象"""
        if self.config is None:
            self.error('create_session:配置对象不能为空', YBRequests.create_session.__name__)
            raise ValueError('create_session:配置对象不能为空')
        
        try:
            return await self._create_session(limit, limit_per_host, cookies, headers, verify_ssl, timeout)
        except Exception as e:
            self.error(f'创建异步会话失败: {e}', YBRequests.create_session.__name__)
            raise e

    async def _async_request(self, method: str, url: str, headers: Dict = None,
                            session: aiohttp.ClientSession = None, timeout: float = None,
                            delay: float = None, retries: int = None, return_type: str = 'text',
                            **kwargs) -> Optional[Any]:
        
        f_name =  self._async_request.__name__
        time.sleep(0.01)
        """异步请求核心方法"""
        for attempt in range(retries + 1):
            try:
                async with session.request(method=method, url=url, headers=headers, timeout=timeout, **kwargs) as response:
                    if response.status in [403, 404, 500, 502, 504, 520]:
                        error_msg = f"HTTP错误 {response.status} {response.reason}"
                        raise HTTPStatusException(error_msg, url=url, status_code=response.status, reason=response.reason)
                    
                    if return_type == 'content':
                        return await response.content.read()
                    elif return_type == 'json':
                        return await response.json()
                    elif return_type == 'text':
                        content = await response.content.read()
                        text = self._decode_response_text(content, url, charset=response.charset)
                        
                        if self.meet_yzm(text):
                            raise CaptchaException(f'检测到验证码，url：{url}')
                        
                        return text
                    else:
                        raise ValueError(f"不支持的return_type类型 {return_type}")
            except HTTPStatusException as e:
                raise MeetCheckError(check_type=e.reason, url=e.url)

            except asyncio.TimeoutError as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} 超时，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"_async_request请求 {url} 超时，已达最大重试次数: {str(e)}", f_name)
                    raise TimeoutException(f"请求超时，已达到最大重试次数 {retries} 次", url=url, timeout=timeout, e=e)
            except aiohttp.ClientConnectorError as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} 连接失败，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"_async_request请求 {url} 连接失败，已达最大重试次数: {str(e)}", f_name)
                    raise NetworkException(f"网络连接失败，已达到最大重试次数 {retries} 次", url=url, e=e)
            except aiohttp.ClientConnectionError as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} 连接错误，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"_async_request请求 {url} 连接错误，已达最大重试次数: {str(e)}", f_name)
                    raise NetworkException(f"客户端连接错误，已达到最大重试次数 {retries} 次", url=url, e=e)
            except aiohttp.ClientSSLError as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} SSL错误，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"_async_request请求 {url} SSL错误，已达最大重试次数: {str(e)}", f_name)
                    raise SSLException(f"SSL证书验证失败，已达到最大重试次数 {retries} 次", url=url, e=e)
            except aiohttp.ClientResponseError as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} HTTP错误，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"_async_request请求 {url} HTTP错误，已达最大重试次数: {str(e)}", f_name)
                    raise HTTPStatusException(f"HTTP请求失败，已达到最大重试次数 {retries} 次", url=url, status_code=e.status, reason=e.message, e=e)
            except aiohttp.ClientProxyConnectionError as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} 代理错误，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f"_async_request请求 {url} 代理错误，已达最大重试次数: {str(e)}", f_name)
                    raise ProxyException(f"代理连接失败，已达到最大重试次数 {retries} 次", proxy=str(e), e=e)
            except aiohttp.ContentTypeError as e:
                self.error(f"_async_request请求 {url} 内容类型错误: {str(e)}", f_name)
                raise ResponseParseException(f"响应内容类型解析失败", url=url, parse_type='content_type', e=e)
            except (ValueError, aiohttp.ClientPayloadError) as e:
                self.error(f"_async_request请求 {url} 响应解析失败: {str(e)}", f_name)
                raise ResponseParseException(f"响应数据解析失败", url=url, parse_type='unknown', e=e)
            except CaptchaException as e:
                self.error(f'验证码报错：！！！！！！！！！{e}', f_name)
                return None
            except Exception as e:
                if attempt < retries:
                    self.warning(f"_async_request请求 {url} 失败，第 {attempt + 1} 次重试: {str(e)}", f_name)
                    await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
                else:
                    self.error(f'!!!!!!!!!!{method}:未知错误，错误信息：{e}，url：{url}', f_name)
                    raise MaxRetriesException(f"请求失败，已达到最大重试次数 {retries} 次", url=url, max_retries=retries, e=e)
        return None

    async def get(self, url: str, session: aiohttp.ClientSession = None, **kwargs) -> Optional[Any]:
        """异步GET请求"""
        return await self._async_request('GET', url, session=session, **kwargs)

    async def post(self, url: str, session: aiohttp.ClientSession = None, **kwargs) -> Optional[Any]:
        """异步POST请求"""
        return await self._async_request('POST', url, session=session, **kwargs)


class Requests(Ljp_BaseClass):
    """
    HTTP请求统一入口类
    提供同步和异步两种请求方式，兼容旧版API
    """
    Config = BaseRequests.Config

    def __init__(self, config: Config = None, logger=None):
        """
        初始化HTTP请求类
        
        Args:
            config: 配置对象
            logger: 日志记录器
        """
        super().__init__(logger)
        self.config = config or self.Config()
        self.TBRequests = TBRequests(self.config, logger)
        self.YBRequests = YBRequests(self.config, logger)
        self.ls_session = None


    async def async_create_session(self, limit: int = 0, limit_per_host: int = 100, cookies: Dict = None,
                                 headers: Dict = None, verify_ssl: bool = True, wrapper: bool = False) -> Union[aiohttp.ClientSession, 'YBSession']:
        """
        创建异步会话对象（兼容旧版API）

        Args:
            limit: 连接池大小限制
            limit_per_host: 每个主机的连接数限制
            cookies: cookies字典
            headers: 请求头字典
            verify_ssl: 是否验证SSL证书
            wrapper: 是否返回封装的Session对象（默认False返回原生session）

        Returns:
            aiohttp.ClientSession对象或YBSession封装对象
        """
        try:
            session = await self.YBRequests.create_session(limit=limit, limit_per_host=limit_per_host,
                                                       cookies=cookies, headers=headers, verify_ssl=verify_ssl)
            if wrapper:
                return YBSession(session, self.YBRequests)
            return session
        except Exception as e:
            self.error(f'创建异步会话失败: {e}', Requests.async_create_session.__name__)
            raise e

    def create_session(self, cookies: Dict = None, headers: Dict = None, wrapper: bool = False) -> Union[requests.Session, 'TBSession']:
        """
        创建同步会话对象（兼容旧版API）

        Args:
            cookies: cookies字典
            headers: 请求头字典
            wrapper: 是否返回封装的Session对象（默认False返回原生session）

        Returns:
            requests.Session对象或TBSession封装对象
        """
        try:
            session = self.TBRequests.create_session(cookies=cookies, headers=headers)
            if wrapper:
                return TBSession(session, self.TBRequests)
            return session
        except Exception as e:
            self.error(f'创建同步会话失败: {e}', Requests.create_session.__name__)
            raise e

    async def async_get(self, url: str, res_encoding: str = None,
                       return_type: str = 'text', session: aiohttp.ClientSession = None, **kwargs):
        """
        异步GET请求（兼容旧版API）
        
        Args:
            url: 请求URL
            res_encoding: 响应编码
            return_type: 返回类型（text/content/json）
            session: aiohttp会话对象
            **kwargs: 其他请求参数
            
        Returns:
            请求结果
        """
        return await self.YBRequests.get(url, session=session, return_type=return_type, **kwargs)

    async def async_post(self, url: str, res_encoding: str = None,
                        return_type: str = 'text', session: aiohttp.ClientSession = None, **kwargs) -> Optional[Any]:
        """
        异步POST请求（兼容旧版API）
        
        Args:
            url: 请求URL
            res_encoding: 响应编码
            return_type: 返回类型（text/content/json）
            session: aiohttp会话对象
            **kwargs: 其他请求参数
            
        Returns:
            请求结果
        """
        return await self.YBRequests.post(url, session=session, return_type=return_type, **kwargs)

    def get(self, url: str, session: requests.Session = None, **kwargs) -> Optional[Any]:
        """
        同步GET请求
        
        Args:
            url: 请求URL
            session: requests会话对象
            **kwargs: 其他请求参数
            
        Returns:
            请求结果
        """
        if session is None:
            session = self.create_session(**kwargs)
        return self.TBRequests.get(url, session=session, **kwargs)

    def post(self, url: str, session: requests.Session = None, **kwargs) -> Optional[Any]:
        """
        同步POST请求
        
        Args:
            url: 请求URL
            session: requests会话对象
            **kwargs: 其他请求参数
            
        Returns:
            请求结果
        """
        if session is None:
            session = self.create_session(**kwargs)
        return self.TBRequests.post(url, session=session, **kwargs)

    def get_cookies(self, session) -> Dict:
        """获取会话的cookies（支持同步/异步会话）"""
        return self.TBRequests.get_cookies(session)

    def update_cookies(self, session, cookies):
        """更新会话的cookies（支持同步/异步会话）"""
        self.TBRequests.update_cookies(session, cookies)

    def get_headers(self, session):
        """获取会话的headers（支持同步/异步会话）"""
        return self.TBRequests.get_headers(session)


class TBSession:
    """同步Session封装类，提供更便捷的请求接口"""

    def __init__(self, session: requests.Session, tb_requests: TBRequests):
        """初始化Session封装

        Args:
            session: requests.Session对象
            tb_requests: TBRequests实例，用于配置和工具方法
        """
        self._session = session
        self._tb_requests = tb_requests

    def get(self, url: str, **kwargs) -> Optional[Any]:
        """发送GET请求

        Args:
            url: 请求URL
            **kwargs: 其他请求参数（timeout, headers, cookies等）

        Returns:
            请求结果
        """
        return self._tb_requests.get(url, session=self._session, **kwargs)

    def post(self, url: str, **kwargs) -> Optional[Any]:
        """发送POST请求

        Args:
            url: 请求URL
            **kwargs: 其他请求参数（timeout, headers, cookies等）

        Returns:
            请求结果
        """
        return self._tb_requests.post(url, session=self._session, **kwargs)

    def close(self):
        """关闭Session"""
        self._session.close()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭"""
        self.close()


class YBSession:
    """异步Session封装类，提供更便捷的请求接口"""

    def __init__(self, session: aiohttp.ClientSession, yb_requests: YBRequests):
        """初始化异步Session封装

        Args:
            session: aiohttp.ClientSession对象
            yb_requests: YBRequests实例，用于配置和工具方法
        """
        self._session = session
        self._yb_requests = yb_requests

    async def get(self, url: str, **kwargs) -> Optional[Any]:
        """发送异步GET请求

        Args:
            url: 请求URL
            **kwargs: 其他请求参数（timeout, headers, cookies等）

        Returns:
            请求结果
        """
        return await self._yb_requests.get(url, session=self._session, **kwargs)

    async def post(self, url: str, **kwargs) -> Optional[Any]:
        """发送异步POST请求

        Args:
            url: 请求URL
            **kwargs: 其他请求参数（timeout, headers, cookies等）

        Returns:
            请求结果
        """
        return await self._yb_requests.post(url, session=self._session, **kwargs)

    async def close(self):
        """关闭异步Session"""
        await self._session.close()

    async def __aenter__(self):
        """支持异步上下文管理器"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文时自动关闭"""
        await self.close()


class Html:
    """HTML工具类，提供HTML解析和处理功能"""

    @staticmethod
    def html_drop_script(html_content: str) -> str:
        """
        注释掉所有的script标签，防止js脚本干扰
        
        Args:
            html_content: HTML内容
            
        Returns:
            处理后的HTML内容
        """
        html_content = html_content.replace('<script', '<!-- <script')
        html_content = html_content.replace('</script>', '</script> -->')
        return html_content

    @staticmethod
    def save_file(html_content: str, path: str = 'test.html') -> None:
        """
        保存HTML文件
        
        Args:
            html_content: HTML内容
            path: 保存路径
        """
        html_content = Html.html_drop_script(html_content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    @staticmethod
    def strip(text: str) -> str:
        """
        移除字符串中的所有空格、制表符和换行符
        
        Args:
            text: 输入的字符串
            
        Returns:
            移除空格后的字符串
        """
        return text.strip().replace('\xa0', '').replace('\r', '').replace('\n', '').replace('\t', '')

    @staticmethod
    def ls_strip(ls):
        s = [
            Html.strip(str_element)
            for str_element in ls
            if str_element is not None
               and isinstance(str_element, str)
               and Html.strip(str_element)
        ]
        return '\n'.join(s)

    @staticmethod
    def str_to_html(res: str):
        """
        将字符串转换为HTML对象
        
        Args:
            res: HTML字符串
            
        Returns:
            lxml HTML对象
        """
        return etree.HTML(res)

    @staticmethod
    def drop_xml(html_str: str):
        """
        移除XML声明并转换为HTML对象
        
        Args:
            html_str: HTML字符串
            
        Returns:
            lxml HTML对象
        """
        html = html_str.replace('<?xml version="1.0" encoding="UTF-8" ?>', '')
        return Html.str_to_html(html)

    @staticmethod
    def xpath_ls(html,xpath):
        return '\n'.join(html.xpath(xpath))


if __name__ == '__main__':
    import asyncio
    
    # 同步测试
    print('=== 同步测试 ===')
    url = 'https://www.baidu.com'
    req = Requests(Requests.Config())
    session = req.create_session()
    res = req.get(url, session=session)
    print(f'同步请求状态码: {len(res) > 0 and "成功" or "失败"}')
    print(f'响应长度: {len(res)} 字符')
    print()
    
    # 异步测试
    async def async_test():
        print('=== 异步测试 ===')
        url = 'https://www.baidu.com'
        req = Requests(Requests.Config())
        async_session = await req.async_create_session()
        res = await req.async_get(url, session=async_session)
        print(f'异步请求状态码: {len(res) > 0 and "成功" or "失败"}')
        print(f'响应长度: {len(res)} 字符')
        await async_session.close()
        print()
        
        # 异常测试
        print('=== 自定义异常测试 ===')
        
        # 测试超时异常
        try:
            timeout_req = Requests(Requests.Config(timeout=0.001))
            timeout_res = timeout_req.get('https://www.baidu.com', session=session)
        except TimeoutException as e:
            print(f'✓ 超时异常: {e}')
            print(f'  URL: {e.url}, 超时时间: {e.timeout}, 原始异常: {type(e.e).__name__}')
        except Exception as e:
            print(f'✗ 其他异常: {type(e).__name__}: {e}')
        
        # 测试HTTP状态码异常
        try:
            status_req = Requests(Requests.Config())
            status_res = status_req.get('https://httpbin.org/status/404', session=session)
        except HTTPStatusException as e:
            print(f'✓ HTTP状态码异常: {e}')
            print(f'  URL: {e.url}, 状态码: {e.status_code}, 原因: {e.reason}, 原始异常: {type(e.e).__name__}')
        except Exception as e:
            print(f'✗ 其他异常: {type(e).__name__}: {e}')
        
        # 测试网络连接异常
        try:
            network_req = Requests(Requests.Config(max_retries=1))
            network_res = network_req.get('https://this-domain-does-not-exist-12345.com', session=session)
        except NetworkException as e:
            print(f'✓ 网络连接异常: {e}')
            print(f'  URL: {e.url}, 状态码: {e.status_code}, 原始异常: {type(e.e).__name__}')
        except MaxRetriesException as e:
            print(f'✓ 最大重试次数异常: {e}')
            print(f'  URL: {e.url}, 最大重试次数: {e.max_retries}, 原始异常: {type(e.e).__name__}')
        except Exception as e:
            print(f'✗ 其他异常: {type(e).__name__}: {e}')
        
        # 测试异步超时异常
        print()
        print('=== 异步异常测试 ===')
        async_timeout_req = Requests(Requests.Config(timeout=0.001))
        async_timeout_session = await async_timeout_req.async_create_session()
        try:
            async_timeout_res = await async_timeout_req.async_get('https://www.baidu.com', session=async_timeout_session)
        except TimeoutException as e:
            print(f'✓ 异步超时异常: {e}')
            print(f'  URL: {e.url}, 超时时间: {e.timeout}')
            try:
                raise MaxRetriesException(f'作答超时:{e}', e=e)
            except Exception as e:
                print(f'e:{e}')
        except Exception as e:
            print(f'✗ 其他异常: {type(e).__name__}: {e}')
        finally:
            await async_timeout_session.close()
    
    asyncio.run(async_test())
