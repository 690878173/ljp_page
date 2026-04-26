from __future__ import annotations

from ljp_page.logger import logger
import platform
from typing import TYPE_CHECKING, Optional

from ljp_page._modules.pydoll.browser.chromium.base import Browser
from ljp_page._modules.pydoll.browser.managers import ChromiumOptionsManager
from ljp_page._modules.pydoll.exceptions import UnsupportedOS
from ljp_page._modules.pydoll.utils import validate_browser_paths

if TYPE_CHECKING:
    from ljp_page._modules.pydoll.browser.options import Options



class Edge(Browser):
    """CDP 自动化的边缘浏览器实现。"""

    def __init__(
        self,
        options: Optional[Options] = None,
        connection_port: Optional[int] = None,
    ):
        """初始化 Edge 浏览器实例。

        参数：
            options：边缘配置选项（如果无则默认）。
            connection_port：CDP WebSocket 端口（如果没有则随机）。"""
        options_manager = ChromiumOptionsManager(options)
        super().__init__(options_manager, connection_port)

    @staticmethod
    def _get_default_binary_location():
        """根据操作系统获取默认的 Edge 可执行路径。

        返回：
            Edge 可执行文件的路径。

        加薪：
            UnsupportedOS：如果操作系统不受支持。
            ValueError：如果在默认位置找不到可执行文件。"""
        os_name = platform.system()
        logger.debug(f'Resolving default Edge binary for OS: {os_name}')

        browser_paths = {
            'Windows': [
                (
                    r'C:\Program Files\Microsoft\Edge\Application'
                    r'\msedge.exe'
                ),
                (
                    r'C:\Program Files (x86)\Microsoft\Edge'
                    r'\Application\msedge.exe'
                ),
            ],
            'Linux': [
                '/usr/bin/microsoft-edge',
            ],
            'Darwin': [
                ('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
            ],
        }

        browser_path = browser_paths.get(os_name)

        if not browser_path:
            logger.error(f'Unsupported OS: {os_name}')
            raise UnsupportedOS()

        path = validate_browser_paths(browser_path)
        logger.debug(f'Using Edge binary: {path}')
        return path
