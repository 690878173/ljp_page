import asyncio
from functools import wraps
from typing import Union, Type, Tuple, Optional, Callable, Any


class Ljp_BaseClass:
    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, level, message, f_name=''):
        formatted_message = f'[{f_name}] {message}' if f_name else message
        if self.logger is None:
            print(formatted_message)
            return None

        try:
            log_method = getattr(self.logger, level, None)
            if log_method:
                log_method(formatted_message)
        except Exception as e:
            print(f"记录{level}级别日志失败：{str(e)}，原始日志内容：{formatted_message}")

    def debug(self, message, f_name=''):
        self._log("debug", message, f_name)

    def info(self, message, f_name=''):
        self._log("info", message, f_name)

    def error(self, message, f_name=''):
        self._log("error", message, f_name)

    def warning(self, message, f_name=''):
        self._log("warning", message, f_name)

    @staticmethod
    def name(func):
        return func.__name__



class Ljp_Decorator:

    @classmethod
    def handle_exceptions(cls,
            exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
            handler= None,
            reraise: bool = True,
            default_return: Any = None,
    ):
        """通用异常处理装饰器工厂

        Args:
            exceptions: 要捕获的异常类型或异常类型元组，默认捕获所有Exception
            handler: 自定义异常处理函数，接收异常对象,原函数，原函数参数作为参数
            reraise: 是否重新抛出异常，默认为True
            default_return: 发生异常且不重新抛出时的默认返回值

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if handler:
                        handler(args[0],e,func,*args[1:],**kwargs)
                    if reraise:
                        raise
                    return default_return

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if handler:
                        await handler(args[0],e,func,*args[1:],**kwargs)
                    if reraise:
                        raise
                    return default_return

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator
