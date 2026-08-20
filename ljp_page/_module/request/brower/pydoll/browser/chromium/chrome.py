from __future__ import annotations

from ljp_page.logger import loguru_logger
import platform
from typing import TYPE_CHECKING, Optional

from ljp_page._module.request.brower.pydoll.browser.chromium.base import Browser
from ljp_page._module.request.brower.pydoll.browser.managers import ChromiumOptionsManager
from ljp_page._module.request.brower.pydoll.exceptions import UnsupportedOS
from ljp_page._module.request.brower.pydoll.utils import validate_browser_paths

__all__ = ['Chrome']

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.options import ChromiumOptions


class Chrome(Browser):
    """用于 CDP 自动化的 Chrome 浏览器实现。"""

    def __init__(
        self,
        options: Optional[ChromiumOptions] = None,
        connection_port: Optional[int] = None,
    ):
        """初始化 Chrome 浏览器实例。

        参数：
            options：Chrome 配置选项（如果无则默认）。
            connection_port：CDP WebSocket 端口（如果没有则随机）。"""
        options_manager = ChromiumOptionsManager(options)
        super().__init__(options_manager, connection_port)

    @staticmethod
    def _get_default_binary_location():
        """根据操作系统获取默认的 Chrome 可执行路径。

        返回：
            Chrome 可执行文件的路径。

        加薪：
            UnsupportedOS：如果操作系统不受支持。
            ValueError：如果在默认位置找不到可执行文件。"""
        os_name = platform.system()
        loguru_logger.debug(f'Resolving default Chrome binary for OS: {os_name}')

        browser_paths = {
            'Windows': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ],
            'Linux': [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
            ],
            'Darwin': [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ],
        }

        browser_path = browser_paths.get(os_name)

        if not browser_path:
            loguru_logger.error(f'Unsupported OS: {os_name}')
            raise UnsupportedOS(f'Unsupported OS: {os_name}')

        path = validate_browser_paths(browser_path)
        loguru_logger.debug(f'Using Chrome binary: {path}')
        return path
