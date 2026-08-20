from __future__ import annotations

from ljp_page.logger import loguru_logger
from typing import TYPE_CHECKING, Optional

from ljp_page._module.request.brower.pydoll.browser.interfaces import BrowserOptionsManager
from ljp_page._module.request.brower.pydoll.browser.options import ChromiumOptions
from ljp_page._module.request.brower.pydoll.exceptions import InvalidOptionsObject

__all__ = ['ChromiumOptionsManager']

if TYPE_CHECKING:
    from ljp_page._module.request.brower.pydoll.browser.options import Options



class ChromiumOptionsManager(BrowserOptionsManager):
    """管理基于 Chromium 的浏览器的浏览器选项配置。

    处理选项创建、验证并应用默认 CDP 参数
    适用于 Chrome 和 Edge 浏览器。"""

    def __init__(self, options: Optional[Options] = None):
        self.options = options
        loguru_logger.debug(
            f'ChromiumOptionsManager initialized with options='
            f'{type(options).__name__ if options is not None else "None"}'
        )

    def initialize_options(
        self,
    ) -> ChromiumOptions:
        """初始化并验证浏览器选项。

        如果未提供，则创建 ChromiumOptions，验证现有选项，
        并应用默认 CDP 参数。

        返回：
            正确配置的 ChromiumOptions 实例。

        加薪：
            InvalidOptionsObject：如果提供的选项不是 ChromiumOptions。"""
        if self.options is None:
            self.options = ChromiumOptions()
            loguru_logger.debug('No options provided; created default ChromiumOptions')

        if not isinstance(self.options, ChromiumOptions):
            loguru_logger.error(f'Invalid options type: {type(self.options)}; expected ChromiumOptions')
            raise InvalidOptionsObject(f'Expected ChromiumOptions, got {type(self.options)}')

        self.add_default_arguments()
        loguru_logger.debug('Options initialized and default arguments applied')
        return self.options

    def add_default_arguments(self):
        """添加 CDP 集成所需的默认参数。"""
        loguru_logger.debug('Adding default arguments for Chromium-based browsers')
