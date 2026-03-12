from __future__ import annotations

import asyncio
import inspect
import threading
import time
from collections import OrderedDict
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Coroutine, Dict, Iterable, Optional, Tuple, TypeVar, Union, cast

from .._ljp_coro.base_class import Ljp_BaseClass
from .._ljp_coro.exceptions import No

_T = TypeVar("_T")


@dataclass(slots=True)
class AsyncStats:
    """异步任务统计信息。"""

    total: int = 0
    success: int = 0
    failed: int = 0
    cancelled: int = 0
    running: int = 0

    def snapshot(self) -> Dict[str, int]:
        """返回外部不可变更的统计快照。"""
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "running": self.running,
        }


class _AsyncBase(Ljp_BaseClass):
    """异步管理器基础类，负责事件循环生命周期和任务跟踪。"""

    def __init__(
        self,
        mode: int = 1,
        max_concurrent: int = 20,
        max_inner_concurrent: int = 100,
        logger: Any = None,
    ) -> None:
        super().__init__(logger=logger)
        self.mode = mode
        self.max_concurrent = max_concurrent
        self.max_inner_concurrent = max_inner_concurrent

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.inner_semaphore: Optional[asyncio.Semaphore] = None

        self._lock = threading.RLock()
        self._loop_started = threading.Event()
        self._loop_boot_error: Optional[BaseException] = None
        self._stopping = False
        self._task_seq = 0

        # _tasks 仅保留运行中的任务，_task_history 缓存最近完成任务，避免无限增长。
        self._tasks: Dict[str, Future[Any]] = {}
        self._task_history: OrderedDict[str, Future[Any]] = OrderedDict()
        self._submitted_coroutines: Dict[str, Coroutine[Any, Any, Any]] = {}
        self._history_limit = 1000
        self._stats = AsyncStats()

        self._start_loop()

    @staticmethod
    def _close_if_coroutine(obj: Any) -> None:
        """在未被调度时关闭协程，避免 RuntimeWarning。"""
        if asyncio.iscoroutine(obj):
            obj.close()

    def _refresh_running_locked(self) -> None:
        """在持锁状态下刷新 running 计数。"""
        self._stats.running = len(self._tasks)

    def _build_task_id_locked(self, task_id: Optional[str]) -> str:
        """在持锁状态下生成并校验 task_id。"""
        if task_id is not None:
            if task_id in self._tasks:
                raise ValueError(f"任务ID已存在，禁止覆盖: {task_id}")
            return task_id

        while True:
            self._task_seq += 1
            generated = f"task-{self._task_seq}"
            if generated not in self._tasks:
                return generated

    def _record_history_locked(self, task_id: str, future: Future[Any]) -> None:
        """记录已完成任务的最近历史。"""
        self._task_history.pop(task_id, None)
        self._task_history[task_id] = future

        while len(self._task_history) > self._history_limit:
            self._task_history.popitem(last=False)

    def _register_task_locked(self, task_id: str, future: Future[Any]) -> None:
        """注册任务并更新统计。"""
        self._task_history.pop(task_id, None)
        self._submitted_coroutines.pop(task_id, None)
        self._tasks[task_id] = future
        self._stats.total += 1
        self._refresh_running_locked()

    def _run_loop(self) -> None:
        """后台线程入口：创建并运行事件循环。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with self._lock:
            self.loop = loop
            self.semaphore = asyncio.Semaphore(self.max_concurrent)
            self.inner_semaphore = asyncio.Semaphore(self.max_inner_concurrent)
            self._loop_boot_error = None
            self._stopping = False

        # 仅在事件循环真正进入 run_forever 后再置位，避免启动竞态。
        loop.call_soon(self._loop_started.set)
        self.info(f"事件循环线程已创建，最大并发={self.max_concurrent}", self._run_loop.__name__)

        try:
            loop.run_forever()
        except Exception as exc:  # pragma: no cover
            with self._lock:
                self._loop_boot_error = exc
            self.error(f"事件循环异常: {exc}", self._run_loop.__name__)
        finally:
            try:
                pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            except Exception as exc:  # pragma: no cover
                self.warning(f"事件循环关闭清理异常: {exc}", self._run_loop.__name__)
            finally:
                if not loop.is_closed():
                    loop.close()

                with self._lock:
                    if self.loop is loop:
                        self.loop = None
                        self.semaphore = None
                        self.inner_semaphore = None
                    self._stopping = False

                self.info("事件循环已关闭", self._run_loop.__name__)
                self._loop_started.set()

    def _start_loop(self) -> None:
        """启动事件循环线程。"""
        with self._lock:
            if self.loop and self.loop.is_running() and self.loop_thread and self.loop_thread.is_alive():
                return

            self._loop_started.clear()
            self.loop_thread = threading.Thread(
                target=self._run_loop,
                daemon=self.mode == 0,
                name="Async-Loop-Thread",
            )
            self.loop_thread.start()

        if not self._loop_started.wait(timeout=5):
            raise RuntimeError("事件循环启动超时")

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            with self._lock:
                loop = self.loop
                boot_error = self._loop_boot_error

                if boot_error is not None:
                    raise RuntimeError("事件循环启动失败") from boot_error
                if loop is not None and not loop.is_closed() and loop.is_running():
                    return

            time.sleep(0.01)

        raise RuntimeError("事件循环启动失败")

    def start(self) -> None:
        """显式启动事件循环。"""
        self._start_loop()

    def stop(self, timeout: float = 5.0) -> None:
        """停止事件循环并尝试取消未完成任务。"""
        with self._lock:
            loop = self.loop
            loop_thread = self.loop_thread
            if loop is None or not loop.is_running():
                return
            self._stopping = True

        self.info("正在停止事件循环...", self.stop.__name__)

        cancelled_count = self._cancel_all_tasks()
        if cancelled_count > 0:
            self.info(f"已请求取消 {cancelled_count} 个任务", self.stop.__name__)

        if loop.is_running():
            loop.call_soon_threadsafe(loop.stop)

        if loop_thread and loop_thread.is_alive() and threading.current_thread() is not loop_thread:
            loop_thread.join(timeout=timeout)
            if loop_thread.is_alive():
                self.warning("事件循环线程停止超时", self.stop.__name__)

        with self._lock:
            self._stopping = False

    def is_running(self) -> bool:
        """检查事件循环是否正在运行。"""
        with self._lock:
            return self.loop is not None and self.loop.is_running()

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """获取可用事件循环，不可用时自动重启。"""
        if not self.is_running():
            self.start()

        with self._lock:
            if self.loop is None or self.loop.is_closed() or not self.loop.is_running():
                raise RuntimeError("事件循环不可用")
            return self.loop

    async def _wrapped_outer_coro(self, awaitable: Awaitable[_T]) -> _T:
        """外层并发控制。"""
        semaphore = self.semaphore
        if semaphore is None:
            raise RuntimeError("外层信号量不可用")

        async with semaphore:
            return await awaitable

    async def _wrapped_inner_coro(self, awaitable: Awaitable[_T]) -> _T:
        """内层并发控制。"""
        semaphore = self.inner_semaphore
        if semaphore is None:
            raise RuntimeError("内层信号量不可用")

        async with semaphore:
            return await awaitable

    def _cancel_task(self, task_id: str) -> bool:
        """取消指定运行中的任务。"""
        with self._lock:
            future = self._tasks.get(task_id)

        if future is None:
            return False

        return future.cancel()

    def _cancel_all_tasks(self) -> int:
        """取消所有运行中的任务，返回成功请求取消的数量。"""
        with self._lock:
            futures = list(self._tasks.values())

        cancelled_count = 0
        for future in futures:
            if future.cancel():
                cancelled_count += 1

        return cancelled_count


class Async(_AsyncBase):
    """异步任务管理器，支持任意线程提交协程。"""

    def _attach_internal_done_callback(self, future: Future[Any], task_id: str) -> None:
        """统一任务完成回调：更新统计、回收任务、记录历史。"""

        def _on_done(done_future: Future[Any]) -> None:
            status = "failed"
            exception: BaseException | None = None
            try:
                if done_future.cancelled():
                    status = "cancelled"
                else:
                    exception = done_future.exception()
                    status = "success" if exception is None else "failed"
            except BaseException as query_error:  # pragma: no cover
                exception = query_error
                status = "failed"

            with self._lock:
                self._tasks.pop(task_id, None)
                self._record_history_locked(task_id, done_future)
                raw_coro = self._submitted_coroutines.pop(task_id, None)
                if raw_coro is not None:
                    try:
                        raw_coro.close()
                    except RuntimeError:  # pragma: no cover
                        pass

                if status == "success":
                    self._stats.success += 1
                elif status == "cancelled":
                    self._stats.cancelled += 1
                else:
                    self._stats.failed += 1

                self._refresh_running_locked()

            if status == "failed" and exception is not None:
                self.error(
                    f"任务执行失败(task_id={task_id}): {exception}",
                    self.submit.__name__,
                )

        future.add_done_callback(_on_done)

    def _attach_callback(
        self,
        future: Future[Any],
        task_id: str,
        callback: Callable[[Any], Any],
        return_exceptions: bool,
    ) -> None:
        """绑定用户回调，并隔离回调异常。"""

        def _wrapper(done_future: Future[Any]) -> None:
            try:
                if return_exceptions:
                    if done_future.cancelled():
                        callback(asyncio.CancelledError())
                        return

                    exception = done_future.exception()
                    callback(exception if exception is not None else done_future.result())
                    return

                callback(done_future.result())
            except Exception as callback_error:
                self.error(
                    f"任务回调执行失败(task_id={task_id}): {callback_error}",
                    self._attach_callback.__name__,
                )

        future.add_done_callback(_wrapper)

    def submit(
        self,
        coro: Awaitable[_T],
        callback: Optional[Callable[[Any], Any]] = None,
        timeout: Optional[float] = None,
        task_id: Optional[str] = None,
        return_exceptions: bool = False,
        await_result: bool = False,
    ) -> Union[Future[_T], _T]:
        """提交单个协程任务，可在任意线程调用。"""
        if not inspect.isawaitable(coro):
            raise TypeError("coro 必须是可等待对象")

        if callback is not None and not callable(callback):
            self._close_if_coroutine(coro)
            raise TypeError("callback 必须是可调用对象")

        loop = self.get_event_loop()

        if isinstance(coro, asyncio.Future) and coro.get_loop() is not loop:
            raise ValueError("不支持提交绑定到其他事件循环的 Future/Task，请提交协程对象")

        wrapped: Awaitable[_T] = self._wrapped_outer_coro(coro)
        if timeout is not None:
            wrapped = asyncio.wait_for(wrapped, timeout=timeout)

        with self._lock:
            if self._stopping:
                self._close_if_coroutine(wrapped)
                self._close_if_coroutine(coro)
                raise RuntimeError("事件循环正在停止，无法提交任务")

            try:
                resolved_task_id = self._build_task_id_locked(task_id)
            except Exception:
                self._close_if_coroutine(wrapped)
                self._close_if_coroutine(coro)
                raise

            try:
                future = asyncio.run_coroutine_threadsafe(
                    cast(Coroutine[Any, Any, _T], wrapped),
                    loop,
                )
            except Exception:
                self._close_if_coroutine(wrapped)
                self._close_if_coroutine(coro)
                raise

            self._register_task_locked(resolved_task_id, cast(Future[Any], future))
            if asyncio.iscoroutine(coro):
                self._submitted_coroutines[resolved_task_id] = cast(Coroutine[Any, Any, Any], coro)

        self._attach_internal_done_callback(cast(Future[Any], future), resolved_task_id)
        if callback is not None:
            self._attach_callback(
                cast(Future[Any], future),
                resolved_task_id,
                callback,
                return_exceptions,
            )

        if await_result:
            return future.result()
        return cast(Future[_T], future)

    def submit_s(
        self,
        async_ls: Iterable[Union[Awaitable[Any], Tuple[Awaitable[Any], Optional[Callable[[Any], Any]]]]],
        timeout: Optional[float] = None,
        return_exceptions: bool = False,
        await_result: bool = False,
    ) -> Union[list[Future[Any]], list[Any]]:
        """批量提交协程任务。"""
        futures: list[Future[Any]] = []
        for item in async_ls:
            if isinstance(item, tuple) and len(item) == 2:
                coro, callback = item
            else:
                coro = cast(Awaitable[Any], item)
                callback = None

            future = cast(
                Future[Any],
                self.submit(
                    coro,
                    callback=callback,
                    timeout=timeout,
                    return_exceptions=return_exceptions,
                ),
            )
            futures.append(future)

        if await_result:
            return [future.result() for future in futures]
        return futures

    async def submit_inside(self, coro: Awaitable[_T]) -> _T:
        """在协程内部提交子任务，使用内层并发控制。"""
        if not inspect.isawaitable(coro):
            raise TypeError("coro 必须是可等待对象")

        return await self._wrapped_inner_coro(coro)

    async def submit_inside_s(
        self,
        coros: Iterable[Awaitable[Any]],
        return_exceptions: bool = False,
    ) -> list[Any]:
        """在协程内部批量提交子任务，使用内层并发控制。"""
        try:
            wrapped_coros = [self.submit_inside(coro) for coro in coros]
            return await asyncio.gather(*wrapped_coros, return_exceptions=return_exceptions)
        except Exception as exc:
            self.error(f"批量子任务执行失败: {exc}", self.submit_inside_s.__name__)
            raise No("批量子任务执行失败", f=self.submit_inside_s, e=exc)

    async def submit_async(self, coro: Awaitable[_T]) -> _T:
        """在异步上下文提交任务并等待结果。"""
        future = cast(Future[_T], self.submit(coro))
        return await asyncio.wrap_future(future)

    def cancel(self, task_id: Optional[str] = None) -> Union[bool, int]:
        """取消指定任务；task_id 为空时取消所有运行中任务。"""
        if task_id is not None:
            return self._cancel_task(task_id)
        return self._cancel_all_tasks()

    def get_stats(self) -> Dict[str, int]:
        """获取任务统计快照。"""
        with self._lock:
            self._refresh_running_locked()
            return self._stats.snapshot()

    def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态：running/done/cancelled/not_found。"""
        with self._lock:
            future = self._tasks.get(task_id)
            if future is None:
                future = self._task_history.get(task_id)

        if future is None:
            return "not_found"
        if future.cancelled():
            return "cancelled"
        if future.done():
            return "done"
        return "running"

    def get_all_task_ids(self) -> list[str]:
        """获取任务 ID 列表（运行中 + 最近完成历史）。"""
        with self._lock:
            active_ids = list(self._tasks.keys())
            history_ids = [task_id for task_id in self._task_history.keys() if task_id not in self._tasks]
        return active_ids + history_ids

    def wait_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待指定任务完成并返回结果。"""
        with self._lock:
            future = self._tasks.get(task_id)
            if future is None:
                future = self._task_history.get(task_id)

        if future is None:
            raise ValueError(f"任务 {task_id} 不存在")

        return future.result(timeout=timeout)

    def wait_all_tasks(self, timeout: Optional[float] = None) -> list[Any]:
        """等待当前可见任务（运行中 + 最近完成历史）完成。"""
        with self._lock:
            # 用 set 去重，避免同一个 Future 被重复等待。
            futures = list({id(future): future for future in [*self._tasks.values(), *self._task_history.values()]}.values())

        return [future.result(timeout=timeout) for future in futures]

    def __enter__(self) -> "Async":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()
