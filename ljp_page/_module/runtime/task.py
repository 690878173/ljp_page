from __future__ import annotations

import asyncio
from concurrent.futures import Future
from dataclasses import dataclass, replace
from typing import Any, Callable, Generic, TypeVar, TYPE_CHECKING

_T = TypeVar("_T")

if TYPE_CHECKING:
    from ljp_page._module.tools.bind import BindTask

@dataclass(slots=True)
class TaskSubmitConfig:
    """统一任务配置。"""

    mode: str = "auto"
    task_id: str | None = None
    timeout: float | None = None
    callback: Callable[[Any], Any] | None = None
    semaphores: tuple[asyncio.Semaphore, ...] = ()
    semaphore_names: tuple[str, ...] = ()

    def with_task_id(self, task_id: str | None) -> "TaskSubmitConfig":
        """返回仅替换任务 ID 后的新配置。"""
        return replace(self, task_id=task_id)


@dataclass(slots=True, frozen=True)
class TaskMeta:
    """集中保存句柄元信息，减少大量任务场景下的实例开销。"""

    task_id: str
    mode_requested: str
    mode_resolved: str
    backend_name: str
    target_name: str = "submit"
    semaphore_names: tuple[str, ...] = ()


class Task(Generic[_T]):
    """统一任务句柄，对外屏蔽底层 Future 类型差异。"""

    __slots__ = ("_future", "_meta", "_bound_task")

    def __init__(
        self,
        future: Future[_T],
        *,
        task_id: str,
        mode_requested: str,
        mode_resolved: str,
        backend_name: str,
        semaphore_names: tuple[str, ...] = (),
        bound_task: BindTask | None = None,
    ) -> None:
        """初始化任务句柄。

        Args:
            future: 底层的 Future 对象
            task_id: 任务唯一 ID
            mode_requested: 用户请求的执行模式（thread/async）
            mode_resolved: 实际使用的执行模式
            backend_name: 执行后端名称
            semaphore_names: 限流信号量名称
            bound_task: 绑定的任务对象（可选）
        """
        self._future = future
        resolved_target_name = bound_task.target_name if bound_task is not None else "submit"
        self._meta = TaskMeta(
            task_id=task_id,
            mode_requested=mode_requested,
            mode_resolved=mode_resolved,
            backend_name=backend_name,
            target_name=resolved_target_name,
            semaphore_names=semaphore_names,
        )
        self._bound_task = bound_task

    @property
    def future(self) -> Future[_T]:
        """返回底层 Future。"""
        return self._future

    @property
    def task_id(self) -> str:
        """返回任务 ID。"""
        return self._meta.task_id

    @property
    def mode_requested(self) -> str:
        """返回调用方请求的执行模式。"""
        return self._meta.mode_requested

    @property
    def mode_resolved(self) -> str:
        """返回路由解析后的实际模式。"""
        return self._meta.mode_resolved

    @property
    def layer(self) -> str:
        """兼容旧接口：返回当前任务使用的并发池。"""
        return ",".join(self._meta.semaphore_names)

    @property
    def semaphore_names(self) -> tuple[str, ...]:
        """返回当前任务使用的命名并发池。"""
        return self._meta.semaphore_names

    @property
    def backend_name(self) -> str:
        """返回实际后端名称。"""
        return self._meta.backend_name

    @property
    def bound_task(self) -> BindTask | None:
        """返回关联的绑定任务定义。"""
        return self._bound_task

    @property
    def target_name(self) -> str:
        """返回任务目标名称。"""
        return self._meta.target_name

    @property
    def status(self) -> str:
        """返回统一状态文本。"""
        if self._future.cancelled():
            return "cancelled"
        if self._future.done():
            try:
                exception = self._future.exception()
            except BaseException:
                return "failed"
            return "failed" if exception is not None else "done"
        if self._future.running():
            return "running"
        return "pending"

    def done(self) -> bool:
        """判断任务是否已结束。"""
        return self._future.done()

    def running(self) -> bool:
        """判断任务是否正在执行。"""
        return self._future.running()

    def cancelled(self) -> bool:
        """判断任务是否已取消。"""
        return self._future.cancelled()

    def cancel(self) -> bool:
        """取消任务。"""
        return self._future.cancel()

    def _check_blocking_wait_allowed(self, method_name: str) -> None:
        """避免在异步事件循环中阻塞等待未完成任务。"""
        if self._future.done():
            return
        if self.mode_resolved != "async":
            return

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return

        raise RuntimeError(
            f"当前处于异步事件循环中，不能调用阻塞式 {method_name}() 等待未完成异步任务，"
            "请使用 await handle 或 await handle.wait_async()"
        )

    def result(self, timeout: float | None = None) -> _T:
        """等待并返回任务结果。"""
        self._check_blocking_wait_allowed("result")
        return self._future.result(timeout=timeout)

    async def wait_async(self) -> _T:
        """在异步上下文中等待任务结果。"""
        return await self

    def exception(self, timeout: float | None = None) -> BaseException | None:
        """等待并返回任务异常。"""
        self._check_blocking_wait_allowed("exception")
        return self._future.exception(timeout=timeout)

    def add_done_callback(self, callback: Callable[["Task[_T]"], Any]) -> "Task[_T]":
        """注册完成回调，回调参数统一为当前句柄。"""
        if not callable(callback):
            raise TypeError("callback 必须是可调用对象")

        def _wrapper(_: Future[_T]) -> None:
            callback(self)

        self._future.add_done_callback(_wrapper)
        return self

    def __await__(self) -> Any:
        """支持 `await handle`。"""
        return asyncio.wrap_future(self._future).__await__()

    def __repr__(self) -> str:
        return (
            f"TaskHandle(task_id={self.task_id!r}, status={self.status!r}, "
            f"mode={self.mode_resolved!r}, semaphores={self.semaphore_names!r}, "
            f"backend={self.backend_name!r})"
        )


