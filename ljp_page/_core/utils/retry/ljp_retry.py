import asyncio
import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Coroutine, List, Optional, Type, TypeVar, Union

from ljp_page.logger import logger

T = TypeVar('T')

class Constants:

    ATTEMPT = 'attempt'

@dataclass
class RetryConfig:
    max_retries: int = 2
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
    on_retry: Optional[Callable] = None
    delay: float = 0
    exponential_backoff: bool = False

    def __post_init__(self):
        self.delay = max(0.0, self.delay)

    def calculate_delay(self, attempt: int) -> float:
        if not self.delay:
            return 0
        return self.delay * (2**attempt if self.exponential_backoff else 1)

    async def call_callback(self, caller_instance: Any) -> None:
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
        Wait for delay.

        Args:
            attempt (int): The current attempt number
        """
        wait_time = self.calculate_delay(attempt)
        if wait_time:
            await asyncio.sleep(wait_time)

    def is_matching_exception(self, exc: Exception) -> bool:
        exc_types = self.exceptions if isinstance(self.exceptions, (list, tuple)) else (self.exceptions,)
        return isinstance(exc, exc_types)

    def should_retry(self, exc: Exception, other: Exception) -> bool:
        return self.is_matching_exception(exc) or self.is_matching_exception(other)



def retry(
    config = None,
    max_retries: int = 2,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    on_retry: Optional[Callable] = None,
    delay: float = 0,
    exponential_backoff: bool = False,
    exception_to_raise: Optional[Exception] = None,
):
    """
    重试装饰器，只打印一次重试信息
    强制要求：被装饰函数必须包含 **kwargs 参数，用于接收重试次数注入
    """
    if config is None:
        config = RetryConfig(
            max_retries=max_retries,
            exceptions=exceptions,
            on_retry=on_retry,
            delay=delay,
            exponential_backoff=exponential_backoff,
        )

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        # ========== 定义阶段强制校验签名 ==========
        sig = inspect.signature(func)
        has_var_kw = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )
        if not has_var_kw:
            raise TypeError(
                f"被 retry 装饰的函数 {func.__name__} 必须包含 **kwargs 参数，"
                f"用于接收重试注入的 {Constants.ATTEMPT} 关键字参数"
            )
        # =================================================

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            caller_instance = args[0] if args else None

            for attempt in range(config.max_retries + 1):
                kwargs[Constants.ATTEMPT] = attempt
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    if not config.is_matching_exception(exc):
                        raise exc
                    if attempt == 0:
                        logger.error(f'进行重试 -->  {exc}')
                    last_exception = exc

                    if attempt < config.max_retries:
                        await config.handle_delay(attempt + 1)
                        await config.call_callback(caller_instance)
                    continue

            if last_exception is not None:
                raise exception_to_raise or last_exception

            raise RuntimeError('Unreachable: 所有重试均已耗尽且未发生异常')

        return wrapper

    return decorator



__all__ = [
    'retry',
    'RetryConfig',
    'Constants'
]
