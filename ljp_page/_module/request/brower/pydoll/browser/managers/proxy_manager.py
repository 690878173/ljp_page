from __future__ import annotations

from ljp_page.logger import logger
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.options import Options


class ProxyManager:
    """管理 CDP 自动化的代理配置和凭据。

    从代理 URL 中提取嵌入的凭据，确保身份验证安全
    信息，并清理命令行参数。"""

    def __init__(self, options: Options):
        """使用浏览器选项初始化代理管理器。

        参数：
            options：可能包含代理配置的浏览器选项。
                如果找到凭据将进行修改。"""
        self.options = options
        logger.debug('ProxyManager initialized with options')

    def get_proxy_credentials(self) -> tuple[bool, tuple[Optional[str], Optional[str]]]:
        """提取并保护代理身份验证凭据。

        搜索代理设置，提取嵌入的凭据，
        并清理选项以消除凭证暴露。

        返回：
            (has_private_proxy, (用户名, 密码)) 的元组。"""
        private_proxy = False
        credentials: tuple[Optional[str], Optional[str]] = (None, None)

        proxy_arg = self._find_proxy_argument()

        if proxy_arg is not None:
            index, proxy_value = proxy_arg
            has_credentials, username, password, clean_proxy = self._parse_proxy(proxy_value)

            if has_credentials:
                self._update_proxy_argument(index, clean_proxy)
                private_proxy = True
                credentials = (username, password)
                logger.debug(
                    f'Proxy credentials extracted (user_set={bool(username)}); argument sanitized'
                )
            else:
                logger.debug('Proxy configured without embedded credentials')

        return private_proxy, credentials

    def _find_proxy_argument(self) -> Optional[tuple[int, str]]:
        """在浏览器选项中找到代理服务器配置。

        返回：
            如果找到，则为 (index, proxy_url) 元组，否则无。"""
        for index, arg in enumerate(self.options.arguments):
            if arg.startswith('--proxy-server='):
                value = arg.split('=', 1)[1]
                logger.debug(f'Found proxy argument at index {index}: {value}')
                return index, value
        return None

    @staticmethod
    def _parse_proxy(proxy_value: str) -> tuple[bool, Optional[str], Optional[str], str]:
        """解析代理 URL 以提取身份验证凭据。

        参数：
            proxy_value：代理 URL 可能包含用户名:密码@服务器:端口。

        返回：
            元组（has_credentials、用户名、密码、clean_proxy_url）。"""
        if '@' not in proxy_value:
            return False, None, None, proxy_value

        try:
            scheme = ''
            has_scheme = False
            if '://' in proxy_value:
                scheme, proxy_value = proxy_value.split('://', 1)
                has_scheme = True

            creds_part, server_part = proxy_value.split('@', 1)
            username, password = creds_part.split(':', 1)

            clean_proxy = f'{scheme}://{server_part}' if has_scheme else server_part
            return True, username, password, clean_proxy
        except ValueError:
            return False, None, None, proxy_value

    def _update_proxy_argument(self, index: int, clean_proxy: str) -> None:
        """将代理参数替换为无凭据版本。"""
        self.options.arguments[index] = f'--proxy-server={clean_proxy}'
        logger.debug(f'Proxy argument updated at index {index}: {clean_proxy}')
