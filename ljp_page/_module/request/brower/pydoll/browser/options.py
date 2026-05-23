from contextlib import suppress

from ljp_page._module.request.brower.pydoll.browser.interfaces import Options
from ljp_page._module.request.brower.pydoll.constants import PageLoadState
from ljp_page._module.request.brower.pydoll.exceptions import (
    ArgumentAlreadyExistsInOptions,
    ArgumentNotFoundInOptions,
    WrongPrefsDict,
)


class ChromiumOptions(Options):
    """用于管理浏览器实例的命令行选项的类。

    此类允许用户指定命令行参数和
    浏览器可执行文件的二进制位置。"""

    def __init__(self):
        """初始化选项实例。

        为命令行参数和字符串设置一个空列表
        浏览器的二进制位置。"""
        self._arguments = []
        self._binary_location = ''
        self._start_timeout = 10
        self._browser_preferences = {}
        self._headless = False
        self._webrtc_leak_protection = False
        self._page_load_state = PageLoadState.COMPLETE
        self.add_argument("--disable-search-engine-choice-screen")
        # self.add_argument("--guest")
        self.add_argument('--no-first-run')
        self.add_argument('--no-default-browser-check')

    @property
    def arguments(self) -> list[str]:
        """获取命令行参数的列表。

        返回：
            list：添加到选项的命令行参数列表。"""
        return self._arguments

    @arguments.setter
    def arguments(self, args_list: list[str]):
        """设置命令行参数列表。

        参数：
            args_list (list)：命令行参数列表。"""
        self._arguments = args_list

    @property
    def binary_location(self) -> str:
        """获取浏览器二进制文件的位置。

        返回：
            str：浏览器可执行文件的文件路径。"""
        return self._binary_location

    @binary_location.setter
    def binary_location(self, location: str):
        """设置浏览器二进制文件的位置。

        参数：
            location (str)：浏览器可执行文件的文件路径。"""
        self._binary_location = location

    @property
    def start_timeout(self) -> int:
        """获取验证浏览器运行状态的超时时间。

        返回：
            int：超时时间（以秒为单位）。"""
        return self._start_timeout

    @start_timeout.setter
    def start_timeout(self, timeout: int):
        """设置验证浏览器运行状态的超时时间。

        参数：
            timeout (int)：超时时间（以秒为单位）。"""
        self._start_timeout = timeout

    def add_argument(self, argument: str):
        """向选项添加命令行参数。

        参数：
            argument (str)：要添加的命令行参数。

        加薪：
            ArgumentAlreadyExistsInOptions：如果参数已在参数列表中。"""
        if argument not in self._arguments:
            self._arguments.append(argument)
        else:
            raise ArgumentAlreadyExistsInOptions(f'Argument already exists: {argument}')

    def remove_argument(self, argument: str):
        """从选项中删除命令行参数。

        参数：
            argument (str)：要删除的命令行参数。

        加薪：
            ArgumentNotFoundInOptions：如果参数不在参数列表中。"""
        if argument not in self._arguments:
            raise ArgumentNotFoundInOptions(f'Argument not found: {argument}')
        self._arguments.remove(argument)

    @property
    def browser_preferences(self) -> dict:
        return self._browser_preferences

    @browser_preferences.setter
    def browser_preferences(self, preferences: dict):
        if not isinstance(preferences, dict):
            raise ValueError('The experimental options value must be a dict.')

        if preferences.get('prefs'):
            raise WrongPrefsDict
        self._browser_preferences = {**self._browser_preferences, **preferences}

    def _set_pref_path(self, path: list, value):
        """在 self._browser_preferences 中安全地设置嵌套值，
        根据需要创建中间字典。

        论据：
            path -- 代表嵌套的键列表
                    路径（例如，['plugins'、'always_open_pdf_externally']）
            value -- 在给定路径设置的值"""
        d = self._browser_preferences
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value

    def _get_pref_path(self, path: list):
        """从 self._browser_preferences 安全地获取嵌套值。

        论据：
            path -- 代表嵌套的键列表
                    路径（例如，['plugins'、'always_open_pdf_externally']）

        返回：
            给定路径的值，如果路径不存在则为 None"""
        nested_preferences = self._browser_preferences
        with suppress(KeyError, TypeError):
            for key in path:
                nested_preferences = nested_preferences[key]
            return nested_preferences
        return None

    def set_default_download_directory(self, path: str):
        """设置保存下载文件的默认目录。

        用法：设置 Chrome 的“download.default_directory”首选项。

        论据：
            路径：下载目标文件夹的绝对路径。"""
        self._set_pref_path(['download', 'default_directory'], path)

    def set_accept_languages(self, languages: str):
        """设置浏览器接受的语言。

        用法：设置“intl.accept_languages”首选项。

        论据：
            languages：以逗号分隔的语言代码字符串（例如，'pt-BR,pt,en-US,en'）。"""
        self._set_pref_path(['intl', 'accept_languages'], languages)

    @property
    def prompt_for_download(self) -> bool:
        return self._get_pref_path(['download', 'prompt_for_download'])

    @prompt_for_download.setter
    def prompt_for_download(self, enabled: bool):
        """启用或禁用下载提示确认。

        用法：设置“download.prompt_for_download”首选项。

        论据：
            启用：如果为 True，Chrome 将在下载前要求确认。"""
        self._set_pref_path(['download', 'prompt_for_download'], enabled)

    @property
    def block_popups(self) -> bool:
        return self._get_pref_path(['profile', 'default_content_setting_values', 'popups']) == 0

    @block_popups.setter
    def block_popups(self, block: bool):
        """阻止或允许弹出窗口。

        用法：设置“profile.default_content_setting_values.popups”首选项。

        论据：
            block：如果为 True，弹出窗口将被阻止（值 = 0）；否则允许（值 = 1）。"""
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'popups'], 0 if block else 1
        )

    @property
    def password_manager_enabled(self) -> bool:
        return self._get_pref_path(['profile', 'password_manager_enabled'])

    @password_manager_enabled.setter
    def password_manager_enabled(self, enabled: bool):
        """启用或禁用 Chrome 的密码管理器。

        用法：设置“profile.password_manager_enabled”首选项。

        论据：
            启用：如果为 True，则密码管理器处于活动状态。"""
        self._set_pref_path(['profile', 'password_manager_enabled'], enabled)
        self._set_pref_path(['credentials_enable_service'], enabled)

    @property
    def block_notifications(self) -> bool:
        block_notifications_true_value = 2
        return (
            self._get_pref_path(['profile', 'default_content_setting_values', 'notifications'])
            == block_notifications_true_value
        )

    @block_notifications.setter
    def block_notifications(self, block: bool):
        """阻止或允许站点通知。

        用法：设置“profile.default_content_setting_values.notifications”首选项。

        论据：
            block：如果为 True，通知将被阻止（值 = 2）；
            否则允许（值 = 1）。"""
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'notifications'],
            2 if block else 1,
        )

    @property
    def allow_automatic_downloads(self) -> bool:
        return (
            self._get_pref_path([
                'profile',
                'default_content_setting_values',
                'automatic_downloads',
            ])
            == 1
        )

    @allow_automatic_downloads.setter
    def allow_automatic_downloads(self, allow: bool):
        """允许或阻止自动多次下载。

        用法：设置“profile.default_content_setting_values.automatic_downloads”首选项。

        论据：
            允许：如果为True，则允许自动下载（值= 1）；
            否则被阻止（值 = 2）。"""
        self._set_pref_path(
            ['profile', 'default_content_setting_values', 'automatic_downloads'],
            1 if allow else 2,
        )

    @property
    def open_pdf_externally(self) -> bool:
        return self._get_pref_path(['plugins', 'always_open_pdf_externally'])

    @open_pdf_externally.setter
    def open_pdf_externally(self, enabled: bool):
        """阻止或允许地理位置访问。

        用法：设置“profile.managed_default_content_settings.geolocation”首选项。

        论据：
            block：如果为 True，则阻止位置访问（值 = 2）；否则允许（值 = 1）。"""
        self._set_pref_path(['plugins', 'always_open_pdf_externally'], enabled)

    @property
    def headless(self) -> bool:
        return self._headless

    @headless.setter
    def headless(self, headless: bool):
        self._headless = headless
        has_argument = '--headless=new' in self.arguments
        methods_map = {True: self.add_argument, False: self.remove_argument}
        if headless == has_argument:
            return
        methods_map[headless]('--headless=new')

    @property
    def webrtc_leak_protection(self) -> bool:
        return self._webrtc_leak_protection

    @webrtc_leak_protection.setter
    def webrtc_leak_protection(self, enabled: bool):
        self._webrtc_leak_protection = enabled
        argument = '--force-webrtc-ip-handling-policy=disable_non_proxied_udp'
        has_argument = argument in self.arguments
        methods_map = {True: self.add_argument, False: self.remove_argument}
        if enabled == has_argument:
            return
        methods_map[enabled](argument)

    @property
    def page_load_state(self) -> PageLoadState:
        return self._page_load_state

    @page_load_state.setter
    def page_load_state(self, state: PageLoadState):
        self._page_load_state = state
