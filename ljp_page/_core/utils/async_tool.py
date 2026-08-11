
import inspect
from typing import Any, Callable, TypeVar, Awaitable

T = TypeVar('T')


async def resolve_value(value: Any,*args,**kwargs) -> Any:
    """
    统一解析可能为普通值、可调用对象或协程的输入。

    适用场景：
    - 配置值的动态加载（支持 lambda/函数）
    - 钩子函数（同步/异步混用）
    - CDP/网络请求返回值的统一等待

    用法：
        # 传入普通值
        await resolve_value(42)               # 返回 42

        # 传入同步方法（自动调用）
        await resolve_value(lambda x: x+1, 5) # 返回 6

        # 传入异步方法（调用并 await）
        await resolve_value(obj.async_fetch, id=10)

        # 传入已经实例化的协程
        await resolve_value(async_fetch(10))
    """
    # 1. 处理可调用对象（方法、函数、lambda）
    if callable(value):
        try:
            value = value(*args, **kwargs)
        except Exception as e:
            # 公共库建议抛出明确异常，便于上层捕获
            raise TypeError(f"调用 {value.__name__} 失败，请检查参数") from e

    # 2. 处理协程/等待对象（标准方式）
    if inspect.isawaitable(value):
        return await value

    # 3. 普通值原样返回
    return value