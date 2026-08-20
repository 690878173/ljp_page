
import os
import shutil
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from ljp_page.logger import loguru_logger


__all__ = ['TempDirectoryManager']

class TempDirectoryManager:
    """管理 CDP 浏览器自动化的临时目录生命周期。

    为浏览器配置文件和句柄创建隔离的临时目录
    通过重试机制对锁定文件进行安全清理。"""

    def __init__(self, temp_dir_factory: Callable[[], TemporaryDirectory] = TemporaryDirectory):
        """初始化临时目录管理器。

        参数：
            temp_dir_factory：创建临时目录的函数。
                必须返回 TemporaryDirectory 兼容对象。"""
        self._temp_dir_factory = temp_dir_factory
        self._temp_dirs: list[TemporaryDirectory] = []
        loguru_logger.debug('TempDirectoryManager initialized')

    def create_temp_dir(self) -> TemporaryDirectory:
        """创建并跟踪新的临时目录以供浏览器使用。

        返回：
            浏览器 --user-data-dir 参数的 TemporaryDirectory 对象。"""
        temp_dir = self._temp_dir_factory()
        self._temp_dirs.append(temp_dir)
        loguru_logger.debug(f'Created temp directory: {temp_dir.name}')
        return temp_dir

    @staticmethod
    def retry_process_file(func: Callable[[str], None], path: str, retry_times: int = 10):
        """对锁定的文件执行带有重试逻辑的文件操作。

        参数：
            func：在路径上执行的函数。
            path：要操作的文件或目录路径。
            retry_times：最大重试次数（负数=无限制）。

        加薪：
            PermissionError：如果在所有重试后操作失败。"""
        retry_time = 0
        while retry_times < 0 or retry_time < retry_times:
            retry_time += 1
            try:
                func(path)
                break
            except PermissionError:
                time.sleep(0.1)
                loguru_logger.debug(
                    f'Retrying file operation due to PermissionError (attempt {retry_time})'
                )
        else:
            raise PermissionError()

    def handle_cleanup_error(self, func: Callable[[str], None], path: str, exc_info: tuple):
        """使用特定于浏览器的解决方法处理目录清理期间的错误。

        参数：
            func：失败的原始函数。
            path：无法处理的路径。
            exc_info：异常信息元组。

        注意：
            处理 Chromium 特定的锁定文件，例如 CrashpadMetrics。"""
        matches = ['CrashpadMetrics-active.pma']
        match_substrings = ['Safe Browsing', 'Safe Browsing Cookies']
        #Windows 上通常会锁定额外的图案；比较不区分大小写
        windows_locked_substrings = [
            '\\cache\\',
            '/cache/',
            'no_vary_search',
            'journal.baj',
            '\\network\\cookies',
            '/network/cookies',
            'cookies-journal',
            '\\local storage\\',
            '/local storage/',
            '\\local storage\\leveldb\\',
            '/local storage/leveldb/',
            'leveldb',
            'indexeddb',
        ]
        exc_type, exc_value, _ = exc_info

        if exc_type is PermissionError:
            filename = Path(path).name
            #已知的 Chromium 文件可能在 Windows 上短暂保持锁定状态
            path_lc = path.lower()
            windows_match = os.name == 'nt' and any(
                substr in path_lc for substr in windows_locked_substrings
            )
            if (
                filename in matches
                or any(substr in path for substr in match_substrings)
                or windows_match
            ):
                try:
                    self.retry_process_file(func, path)
                    return
                except PermissionError:
                    loguru_logger.warning(f'Ignoring locked Chrome file during cleanup: {path}')
                    return
        elif exc_type is OSError:
            return
        raise exc_value

    def cleanup(self):
        """删除所有跟踪的临时目录并进行错误处理。

        使用自定义错误处理程序来解决特定于浏览器的文件锁定问题。
        即使某些文件拒绝删除，也会继续清理。"""
        for temp_dir in self._temp_dirs:
            loguru_logger.info(f'Cleaning up temp directory: {temp_dir.name}')
            shutil.rmtree(temp_dir.name, onerror=self.handle_cleanup_error)
            remaining = Path(temp_dir.name)
            if not remaining.exists():
                continue

            for attempt in range(10):
                time.sleep(0.2)
                try:
                    shutil.rmtree(temp_dir.name, onerror=self.handle_cleanup_error)
                except Exception:  #noqa：BLE001 - 尽力清理
                    pass
                if not remaining.exists():
                    loguru_logger.debug(
                        f'Temp directory removed after retry #{attempt + 1}: {temp_dir.name}'
                    )
                    break
            if remaining.exists():
                loguru_logger.warning(
                    f'Temp directory still present after retries (leftover files may remain): '
                    f'{temp_dir.name}'
                )
