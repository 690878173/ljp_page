import asyncio
import traceback
from functools import wraps
from typing import Any, Callable, Coroutine, List, Optional, Type, TypeVar, Union
from ljp_page._core.base import Ljp_base_class
T = TypeVar('T')


class RetryConfig:
    """
    重试配置类
    统一管理所有重试相关的参数和逻辑
    """

    def __init__(
        self,
        max_retries: int = 5,
        exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
        on_retry: Optional[Callable] = None,
        delay: float = 0,
        exponential_backoff: bool = False,
    ):
        # 最大重试次数
        self.max_retries = max_retries
        # 需要重试的异常类型（单个或列表）
        self.exceptions = exceptions
        # 重试时执行的回调函数
        self.on_retry = on_retry
        # 重试基础延迟（秒）
        self.delay = delay
        # 是否开启指数退避
        self.exponential_backoff = exponential_backoff

    def calculate_delay(self, attempt: int) -> float:
        """计算重试等待时间"""
        if not self.delay:
            return 0
        return self.delay * (2**attempt if self.exponential_backoff else 1)

    async def call_callback(self, caller_instance: Any) -> None:
        """调用重试回调函数，兼容不同参数格式"""
        if not self.on_retry:
            return

        try:
            await self.on_retry(caller_instance)
        except TypeError as e:
            error_msg = str(e)
            if (
                'takes 1 positional argument but 2 were given' in error_msg
                or 'takes 0 positional arguments but 1 was given' in error_msg
            ):
                try:
                    await self.on_retry()
                    return
                except Exception as e_inner:
                    raise e_inner
            raise e
        except Exception as e:
            raise e

    async def handle_delay(self, attempt: int) -> None:
        """
        执行延迟等待
        :param attempt: 当前重试次数（从 1 开始）
        """
        wait_time = self.calculate_delay(attempt)
        if wait_time:
            await asyncio.sleep(wait_time)

    def is_matching_exception(self, exc: Exception) -> bool:
        """判断当前异常是否需要重试"""
        if isinstance(self.exceptions, (list, tuple)):
            return any(isinstance(exc, e) for e in self.exceptions)
        return isinstance(exc, self.exceptions)


def retry(
    max_retries: int = 2,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    on_retry: Optional[Callable] = None,
    delay: float = 0,
    exponential_backoff: bool = False,
    exception_to_raise: Optional[Exception] = None,
    logger = None
):
    """
    异步函数重试装饰器
    捕获指定异常并自动重试，适合 async 函数使用

    参数说明：
        max_retries: 最大重试次数
        exceptions: 需要重试的异常类型
        on_retry: 每次重试后执行的回调
        delay: 基础延迟时间
        exponential_backoff: 是否开启指数退避
        exception_to_raise: 重试耗尽后抛出的自定义异常
    """
    # 初始化配置
    config = RetryConfig(
        max_retries=max_retries,
        exceptions=exceptions,
        on_retry=on_retry,
        delay=delay,
        exponential_backoff=exponential_backoff,
    )

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            caller_instance = args[0] if args else None
            logger = getattr(caller_instance, "logger", None)
            config = getattr(getattr(caller_instance, "config", object()),"retry", RetryConfig())
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    if logger:
                        logger.error(
                            f"函数 {func.__name__} 执行异常：{traceback.format_exc()}"
                        )

                    if not config.is_matching_exception(exc):
                        raise

                    last_exception = exc

                    if attempt < config.max_retries:
                        await config.handle_delay(attempt + 1)
                        await config.call_callback(caller_instance)

            if last_exception is not None:
                raise last_exception

            raise RuntimeError("无法到达：所有重试耗尽但未捕获到异常")

        return wrapper
    return decorator


class Retry(Ljp_base_class):
    def __init__(self,config: RetryConfig = None,logger=None):
        self.config = config or RetryConfig()
        super().__init__(logger=logger)

    def _(self,exception_to_raise):
        def decorator(
                func: Callable[..., Coroutine[Any, Any, T]],
        ) -> Callable[..., Coroutine[Any, Any, T]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                last_exception: Optional[Exception] = None
                # 获取类实例（如果是类方法）
                caller_instance = args[0] if args else None

                # 循环执行重试
                for attempt in range(self.config.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        # 打印错误堆栈
                        self.error(
                            f'函数 {func.__name__} 执行异常：'
                            f'{traceback.format_exc()}'
                        )

                        # 异常不在重试范围内，直接抛出
                        if not self.config.is_matching_exception(exc):
                            raise exc

                        last_exception = exc

                        # 未达到最大重试次数 → 等待 + 执行回调
                        if attempt < self.config.max_retries:
                            await self.config.handle_delay(attempt + 1)
                            await self.config.call_callback(caller_instance)
                        continue

                # 所有重试都失败，抛出最后一次异常
                if last_exception is not None:
                    raise exception_to_raise or last_exception

                raise RuntimeError('无法到达：所有重试耗尽但未捕获到异常')

            return wrapper

        return decorator

    def __call__(self,exception_to_raise=None):
        return self._(exception_to_raise)
