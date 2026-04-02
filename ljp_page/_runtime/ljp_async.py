# 04-01-20-27-00
"""轻量异步运行时。"""

from __future__ import annotations

import asyncio
import inspect
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ljp_page._core.base.Ljp_base_class import Ljp_BaseClass
from ljp_page._core.exceptions import No


@dataclass(slots=True)
class AsyncStats:
    """异步任务统计信息。"""

    total: int = 0
    success: int = 0
    failed: int = 0
    cancelled: int = 0
    running: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "running": self.running,
        }


class Async(Ljp_BaseClass):
    """在后台线程维护事件循环的异步运行时。"""

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

        self.loop: asyncio.AbstractEventLoop | None = None
        self.loop_thread: threading.Thread | None = None

        self._started = threading.Event()
        self._lock = threading.RLock()
        self._task_seq = 0
        self._tasks: dict[str, Future[Any]] = {}
        self._task_history: dict[str, Future[Any]] = {}
        self._stats = AsyncStats()

        self._outer_semaphore: asyncio.Semaphore | None = None
        self._inner_semaphore: asyncio.Semaphore | None = None

        self._start_loop()

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with self._lock:
            self.loop = loop
            self._outer_semaphore = asyncio.Semaphore(self.max_concurrent)
            self._inner_semaphore = asyncio.Semaphore(self.max_inner_concurrent)
        self._started.set()

        try:
            loop.run_forever()
        finally:
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
            loop.close()
            with self._lock:
                self.loop = None
                self._outer_semaphore = None
                self._inner_semaphore = None

    def _start_loop(self) -> None:
        with self._lock:
            if self.loop is not None and self.loop.is_running():
                return
            self._started.clear()
            self.loop_thread = threading.Thread(
                target=self._run_loop,
                daemon=self.mode == 0,
                name="Async-Loop-Thread",
            )
            self.loop_thread.start()

        if not self._started.wait(timeout=5):
            raise RuntimeError("事件循环启动超时")

    def start(self) -> None:
        self._start_loop()

    def stop(self, timeout: float = 5.0) -> None:
        with self._lock:
            loop = self.loop
            thread = self.loop_thread
            tasks = list(self._tasks.values())

        for future in tasks:
            future.cancel()

        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)

        if thread is not None and thread.is_alive() and threading.current_thread() is not thread:
            thread.join(timeout=timeout)

    def is_running(self) -> bool:
        with self._lock:
            return self.loop is not None and self.loop.is_running()

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        if not self.is_running():
            self.start()
        with self._lock:
            if self.loop is None:
                raise RuntimeError("事件循环不可用")
            return self.loop

    async def _wrapped_outer_coro(self, awaitable: Awaitable[Any]) -> Any:
        if self._outer_semaphore is None:
            raise RuntimeError("外层信号量不可用")
        async with self._outer_semaphore:
            return await awaitable

    async def _wrapped_inner_coro(self, awaitable: Awaitable[Any]) -> Any:
        if self._inner_semaphore is None:
            raise RuntimeError("内层信号量不可用")
        async with self._inner_semaphore:
            return await awaitable

    def _next_task_id(self, task_id: str | None) -> str:
        if task_id is not None:
            return task_id
        self._task_seq += 1
        return f"task-{self._task_seq}"

    def _attach_done_callback(self, task_id: str, future: Future[Any]) -> None:
        def _on_done(done_future: Future[Any]) -> None:
            with self._lock:
                self._tasks.pop(task_id, None)
                self._task_history[task_id] = done_future
                if done_future.cancelled():
                    self._stats.cancelled += 1
                else:
                    exception = done_future.exception()
                    if exception is None:
                        self._stats.success += 1
                    else:
                        self._stats.failed += 1
                self._stats.running = len(self._tasks)

        future.add_done_callback(_on_done)

    def submit(
        self,
        coro: Awaitable[Any],
        callback: Callable[[Any], Any] | None = None,
        timeout: float | None = None,
        task_id: str | None = None,
        return_exceptions: bool = False,
        await_result: bool = False,
    ) -> Future[Any] | Any:
        if not inspect.isawaitable(coro):
            raise TypeError("coro 必须是可等待对象")

        wrapped: Awaitable[Any] = self._wrapped_outer_coro(coro)
        if timeout is not None:
            wrapped = asyncio.wait_for(wrapped, timeout=timeout)

        loop = self.get_event_loop()
        future = asyncio.run_coroutine_threadsafe(wrapped, loop)
        resolved_task_id = self._next_task_id(task_id)

        with self._lock:
            self._tasks[resolved_task_id] = future
            self._stats.total += 1
            self._stats.running = len(self._tasks)

        self._attach_done_callback(resolved_task_id, future)

        if callback is not None:
            def _cb(done_future: Future[Any]) -> None:
                try:
                    if return_exceptions:
                        if done_future.cancelled():
                            callback(asyncio.CancelledError())
                            return
                        exc = done_future.exception()
                        callback(exc if exc is not None else done_future.result())
                        return
                    callback(done_future.result())
                except Exception as exc:
                    self.error(f"任务回调执行失败(task_id={resolved_task_id}): {exc}")

            future.add_done_callback(_cb)

        if await_result:
            return future.result()
        return future

    def submit_s(
        self,
        async_ls: list[Awaitable[Any] | tuple[Awaitable[Any], Callable[[Any], Any] | None]],
        timeout: float | None = None,
        return_exceptions: bool = False,
        await_result: bool = False,
    ) -> list[Future[Any]] | list[Any]:
        futures: list[Future[Any]] = []
        for item in async_ls:
            if isinstance(item, tuple):
                coro, callback = item
            else:
                coro, callback = item, None
            future = self.submit(
                coro,
                callback=callback,
                timeout=timeout,
                return_exceptions=return_exceptions,
                await_result=False,
            )
            futures.append(future)

        if await_result:
            return [future.result() for future in futures]
        return futures

    async def submit_inside(self, coro: Awaitable[Any]) -> Any:
        if not inspect.isawaitable(coro):
            raise TypeError("coro 必须是可等待对象")
        return await self._wrapped_inner_coro(coro)

    async def submit_inside_s(
        self,
        coros: list[Awaitable[Any]],
        return_exceptions: bool = False,
    ) -> list[Any]:
        try:
            wrapped_coros = [self.submit_inside(coro) for coro in coros]
            return await asyncio.gather(*wrapped_coros, return_exceptions=return_exceptions)
        except Exception as exc:
            self.error(f"批量子任务执行失败: {exc}", self.submit_inside_s.__name__)
            raise No("批量子任务执行失败", f=self.submit_inside_s, e=exc)

    async def submit_async(self, coro: Awaitable[Any]) -> Any:
        future = self.submit(coro)
        return await asyncio.wrap_future(future)

    def cancel(self, task_id: str | None = None) -> bool | int:
        if task_id is not None:
            with self._lock:
                future = self._tasks.get(task_id)
            if future is None:
                return False
            return future.cancel()

        with self._lock:
            futures = list(self._tasks.values())
        cancelled = 0
        for future in futures:
            if future.cancel():
                cancelled += 1
        return cancelled

    def get_stats(self) -> dict[str, int]:
        with self._lock:
            self._stats.running = len(self._tasks)
            return self._stats.snapshot()

    def get_task_status(self, task_id: str) -> str:
        with self._lock:
            future = self._tasks.get(task_id) or self._task_history.get(task_id)
        if future is None:
            return "not_found"
        if future.cancelled():
            return "cancelled"
        if future.done():
            return "done"
        return "running"

    def get_all_task_ids(self) -> list[str]:
        with self._lock:
            active = list(self._tasks.keys())
            history = [task_id for task_id in self._task_history if task_id not in self._tasks]
        return active + history

    def wait_task(self, task_id: str, timeout: float | None = None) -> Any:
        with self._lock:
            future = self._tasks.get(task_id) or self._task_history.get(task_id)
        if future is None:
            raise ValueError(f"任务 {task_id} 不存在")
        return future.result(timeout=timeout)

    def wait_all_tasks(self, timeout: float | None = None) -> list[Any]:
        with self._lock:
            futures = list(self._tasks.values()) + list(self._task_history.values())

        deduped: list[Future[Any]] = []
        seen: set[int] = set()
        for future in futures:
            future_id = id(future)
            if future_id in seen:
                continue
            seen.add(future_id)
            deduped.append(future)
        return [future.result(timeout=timeout) for future in deduped]

    def __enter__(self) -> "Async":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()


__all__ = ["Async", "AsyncStats"]
