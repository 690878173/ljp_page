from ljp_page.logger import logger
import subprocess
from typing import Callable, Optional




class BrowserProcessManager:
    """管理 CDP 自动化的浏览器进程生命周期。

    以适当的方式处理流程创建、监控和终止
    资源清理和正常关闭。"""

    def __init__(
        self,
        process_creator: Optional[Callable[[list[str]], subprocess.Popen]] = None,
    ):
        """初始化浏览器进程管理器。

        参数：
            process_creator：创建浏览器进程的自定义函数。
                必须接受命令列表并返回 subprocess.Popen 对象。
                如果没有，则使用默认子流程实现。"""
        self._process_creator = process_creator or self._default_process_creator
        self._process: Optional[subprocess.Popen] = None
        logger.debug(
            f'BrowserProcessManager initialized; custom process_creator={bool(process_creator)}'
        )

    def start_browser_process(
        self,
        binary_location: str,
        port: int,
        arguments: list[str],
    ) -> subprocess.Popen:
        """启动浏览器进程并启用 CDP 调试。

        参数：
            binary_location：浏览器可执行文件的路径。
            port：CDP WebSocket 连接的 TCP 端口。
            参数：附加命令行参数。

        返回：
            已启动浏览器进程实例。

        注意：
            自动添加 --remote-debugging-port 参数。"""
        logger.debug(f'Starting browser process: {binary_location} on port {port}')
        command = [
            binary_location,
            f'--remote-debugging-port={port}',
            *arguments,
        ]
        logger.debug(f'Command: {command}')
        self._process = self._process_creator(command)
        logger.debug(
            f'Browser process started: pid={self._process.pid if self._process else "unknown"}'
        )
        return self._process

    @staticmethod
    def _default_process_creator(command: list[str]) -> subprocess.Popen:
        """创建具有输出捕获的浏览器进程，以防止控制台混乱。"""
        logger.debug(f'Creating process: {command}')
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def stop_process(self):
        """通过正常关闭来终止浏览器进程。

        首先尝试 SIGTERM，然后在 15 秒超时后尝试 SIGKILL。
        即使没有进程正在运行，也可以安全调用。"""
        if self._process:
            logger.info(f'Stopping browser process pid={self._process.pid}')
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
                logger.debug('Process terminated gracefully')
            except subprocess.TimeoutExpired:
                logger.warning('Process did not terminate in 15s; sending SIGKILL')
                self._process.kill()
                logger.debug('Process killed')
