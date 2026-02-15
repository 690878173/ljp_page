
import os
import sys
from typing import Literal

from ..._ljp_coro.base_class import Ljp_BaseClass


def singleton(cls):
    # 单例装饰器
    _instance = {}
    def wrapper(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return wrapper


@singleton
class Logger(Ljp_BaseClass):
    def __init__(self, log_file_path: str = None, log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'):
        super().__init__()

        if log_file_path is None:
            current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            self.log_file_path = os.path.join(current_dir, 'log.log')
        else:
            self.log_file_path = log_file_path

        self.log_level = log_level.upper() if log_level else 'INFO'
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_levels:
            self.log_level = 'INFO'
        from loguru import logger
        logger.remove()
        logger.add(
            sys.stdout,
            level=self.log_level,

            format='<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level: <8}</level> | <level>{message}</level>',
            enqueue=True
        )
        logger.add(
            self.log_file_path,
            level=self.log_level,
            encoding='utf-8',  # 显式指定编码
            rotation="10 MB",  # 轮转，避免日志文件过大
            retention=5,  # 保留最近5个日志文件
            compression="gz",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            enqueue=True
        )
        self.logger = logger
