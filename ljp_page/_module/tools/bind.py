from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable

@dataclass(slots=True)
class BindArg:
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class BindTask:
    """保存目标函数及其绑定参数，避免与调度参数冲突。"""

    target: Any
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    name: str | None = None

    @property
    def target_name(self) -> str:
        """返回任务展示名称。"""
        if self.name:
            return self.name
        if hasattr(self.target, "__name__"):
            return str(self.target.__name__)
        return self.target.__class__.__name__

    def is_async_target(self) -> bool:
        """判断目标是否应走异步后端。"""
        if inspect.isawaitable(self.target):
            return True
        if inspect.iscoroutinefunction(self.target):
            return True

        call_method = getattr(self.target, "__call__", None)
        return call_method is not None and inspect.iscoroutinefunction(call_method)

    def call(self) -> Any:
        """执行同步调用。"""
        if self.is_async_target():
            raise TypeError("当前任务是异步目标，不能使用同步/线程后端执行")
        if not callable(self.target):
            raise TypeError("当前任务目标不可调用")
        return self.target(*self.args, **self.kwargs)

    def create_awaitable(self) -> Awaitable[Any]:
        """延迟构造 awaitable，避免过早创建协程对象。"""
        if inspect.isawaitable(self.target):
            if self.args or self.kwargs:
                raise TypeError("awaitable 对象不能再额外绑定参数")
            return self.target

        if not callable(self.target):
            raise TypeError("当前任务目标不可调用，无法构造异步任务")

        result = self.target(*self.args, **self.kwargs)
        if not inspect.isawaitable(result):
            raise TypeError("async 模式要求目标是协程函数或返回 awaitable 的可调用对象")
        return result




def coerce_bind_task(target: Any, *args: Any, **kwargs: Any) -> BindTask:
    """将输入标准化为 BindTask。"""
    if isinstance(target, BindTask):
        if args or kwargs:
            raise ValueError("BoundTask 已经绑定参数，不能再次传入 args 或 kwargs")
        return target

    if not callable(target) and not inspect.isawaitable(target):
        raise TypeError("target 必须是可调用对象、协程对象或 awaitable 对象")

    return BindTask(target=target, args=tuple(args), kwargs=dict(kwargs))



__all__ = ["BindArg", "BindTask", "coerce_bind_task"]