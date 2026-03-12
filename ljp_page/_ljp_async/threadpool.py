from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, TypeVar, cast

from .._ljp_coro.base_class import Ljp_BaseClass

_T = TypeVar("_T")


@dataclass(slots=True)
class PoolStats:
    """线程池状态统计。"""

    submitted: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0
    cancelled: int = 0

    def snapshot(self) -> dict[str, int]:
        """返回不可共享的统计快照，防止外部篡改内部状态。"""
        return {
            "submitted": self.submitted,
            "running": self.running,
            "success": self.success,
            "failed": self.failed,
            "cancelled": self.cancelled,
        }


class ThreadPool(Ljp_BaseClass):
    """对 ThreadPoolExecutor 的轻量封装，增加任务跟踪和状态统计。"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_name_prefix: str = "LjpThreadPool",
        logger: Any = None,
    ) -> None:
        super().__init__(logger=logger)
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix

        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
        )

        # 所有共享变量统一由同一把锁保护。
        self._lock = threading.RLock()
        self._futures: dict[str, Future[Any]] = {}
        self._stats = PoolStats()
        self._shutdown = False
        self._auto_task_seq = 0

    def _refresh_running_locked(self) -> None:
        """在持锁状态下刷新运行中任务数。"""
        self._stats.running = len(self._futures)

    def _build_task_id_locked(self, task_id: Optional[str]) -> str:
        """在持锁状态下生成并校验任务 ID。"""
        if task_id is not None:
            if task_id in self._futures:
                raise ValueError(f"任务ID已存在，禁止覆盖: {task_id}")
            return task_id

        while True:
            self._auto_task_seq += 1
            generated = f"task-{self._auto_task_seq}"
            if generated not in self._futures:
                return generated

    def _attach_internal_done_callback(self, future: Future[Any], task_id: str) -> None:
        """注册内部完成回调，负责回收任务和更新统计。"""

        def _on_done(done_future: Future[Any]) -> None:
            was_cancelled = False
            task_exception: BaseException | None = None
            try:
                if done_future.cancelled():
                    was_cancelled = True
                else:
                    task_exception = done_future.exception()
            except BaseException as query_error:  # pragma: no cover
                task_exception = query_error

            with self._lock:
                self._futures.pop(task_id, None)
                if was_cancelled:
                    self._stats.cancelled += 1
                elif task_exception is None:
                    self._stats.success += 1
                else:
                    self._stats.failed += 1
                self._refresh_running_locked()

            if task_exception is not None and not was_cancelled:
                self.error(
                    f"线程池任务执行失败(task_id={task_id}): {task_exception}",
                    self.submit.__name__,
                )

        future.add_done_callback(_on_done)

    def _attach_callback(
        self,
        future: Future[Any],
        callback: Callable[[Any], Any],
        task_id: str,
    ) -> None:
        """给 Future 绑定安全回调，隔离用户回调异常。"""

        def _wrapper(done_future: Future[Any]) -> None:
            try:
                if done_future.cancelled():
                    return

                exception = done_future.exception()
                if exception is not None:
                    callback(exception)
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
        func: Callable[..., _T],
        *args: Any,
        task_id: Optional[str] = None,
        callback: Optional[Callable[[Any], Any]] = None,
        **kwargs: Any,
    ) -> Future[_T]:
        """
        提交一个任务到线程池。

        - 支持自定义 task_id，用于后续取消。
        - task_id 不能与当前未完成任务重复。
        - callback 异常会被隔离，不会影响线程池。
        """
        if callback is not None and not callable(callback):
            raise TypeError("callback 必须是可调用对象")

        with self._lock:
            if self._shutdown:
                raise RuntimeError("线程池已关闭，无法提交新任务")

            resolved_task_id = self._build_task_id_locked(task_id)
            try:
                future = self._executor.submit(func, *args, **kwargs)
            except RuntimeError as exc:
                # 防御外部直接关闭 executor 的场景，维持统一错误语义。
                self._shutdown = True
                raise RuntimeError("线程池已关闭，无法提交新任务") from exc

            self._futures[resolved_task_id] = future
            self._stats.submitted += 1
            self._refresh_running_locked()

        self._attach_internal_done_callback(future, resolved_task_id)
        if callback is not None:
            self._attach_callback(future, callback, resolved_task_id)

        return cast(Future[_T], future)

    def submit_many(
        self,
        tasks: Iterable[
            Callable[..., _T] | tuple[Callable[..., _T], tuple[Any, ...], dict[str, Any]]
        ],
    ) -> list[Future[_T]]:
        """批量提交多个任务。"""
        futures: list[Future[_T]] = []
        for task in tasks:
            if callable(task):
                futures.append(self.submit(task))
                continue

            func, args, kwargs = task
            futures.append(self.submit(func, *args, **kwargs))
        return futures

    def map(
        self,
        func: Callable[..., _T],
        *iterables: Iterable[Any],
        timeout: Optional[float] = None,
        chunksize: int = 1,
    ) -> list[_T]:
        """并发映射，语义同内置 map，但由线程池并行执行。"""
        with self._lock:
            if self._shutdown:
                raise RuntimeError("线程池已关闭")

        try:
            return list(
                self._executor.map(
                    func,
                    *iterables,
                    timeout=timeout,
                    chunksize=chunksize,
                )
            )
        except RuntimeError as exc:
            with self._lock:
                if self._shutdown:
                    raise RuntimeError("线程池已关闭") from exc
            raise

    def cancel(self, task_id: str) -> bool:
        """根据任务 ID 取消任务。仅对未开始执行的任务生效。"""
        with self._lock:
            future = self._futures.get(task_id)

        if future is None:
            return False

        return future.cancel()

    def cancel_all(self) -> int:
        """尝试取消所有在跟踪中的任务，返回取消成功数量。"""
        cancelled = 0
        with self._lock:
            futures = list(self._futures.values())

        for future in futures:
            if future.cancel():
                cancelled += 1

        return cancelled

    def get_stats(self) -> dict[str, int]:
        """获取线程池统计快照。"""
        with self._lock:
            self._refresh_running_locked()
            return self._stats.snapshot()

    def get_task_ids(self) -> list[str]:
        """获取当前仍在跟踪中的任务 ID 列表。"""
        with self._lock:
            return list(self._futures.keys())

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """关闭线程池。"""
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True

        self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)

    def __enter__(self) -> "ThreadPool":
        """支持 with 上下文。"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出 with 时自动关闭线程池。"""
        self.shutdown()


__all__ = ["ThreadPool"]
