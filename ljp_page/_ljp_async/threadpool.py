"""Custom thread pool wrapper with task tracking and Future compatibility."""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Iterable, Optional, TypeVar

from .._ljp_coro.base_class import Ljp_BaseClass

_T = TypeVar("_T")


class ThreadPool(Ljp_BaseClass):
    """Thin wrapper around ``ThreadPoolExecutor`` with task bookkeeping."""

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
        self._lock = threading.Lock()
        self._futures: dict[str, Future[Any]] = {}
        self._stats = {
            "submitted": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "cancelled": 0,
        }
        self._shutdown = False

    def _register_future(self, future: Future[_T], task_id: str) -> Future[_T]:
        with self._lock:
            self._futures[task_id] = future
            self._stats["submitted"] += 1
            self._stats["running"] += 1

        def _on_done(done_future: Future[_T]) -> None:
            with self._lock:
                self._futures.pop(task_id, None)
                self._stats["running"] = max(0, self._stats["running"] - 1)
                if done_future.cancelled():
                    self._stats["cancelled"] += 1
                else:
                    exception = done_future.exception()
                    if exception is None:
                        self._stats["success"] += 1
                    else:
                        self._stats["failed"] += 1
            if not done_future.cancelled():
                exception = done_future.exception()
                if exception is not None:
                    self.error(f"线程池任务失败: {exception}", self.submit.__name__)

        future.add_done_callback(_on_done)
        return future

    @staticmethod
    def _build_task_id(task_id: Optional[str], future: Future[Any]) -> str:
        return task_id or str(id(future))

    def submit(
        self,
        func: Callable[..., _T],
        *args: Any,
        task_id: Optional[str] = None,
        callback: Optional[Callable[[Any], Any]] = None,
        **kwargs: Any,
    ) -> Future[_T]:
        """Submit a callable and return a standard concurrent future."""

        if self._shutdown:
            raise RuntimeError("ThreadPool has been shut down")

        future = self._executor.submit(func, *args, **kwargs)
        registered = self._register_future(future, self._build_task_id(task_id, future))
        if callback:
            self._attach_callback(registered, callback)
        return registered

    def submit_many(
        self,
        tasks: Iterable[
            Callable[..., _T] | tuple[Callable[..., _T], tuple[Any, ...], dict[str, Any]]
        ],
    ) -> list[Future[_T]]:
        """Submit multiple tasks at once."""

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
        """Apply ``func`` to the provided iterables and return realized results."""

        if self._shutdown:
            raise RuntimeError("ThreadPool has been shut down")
        return list(
            self._executor.map(
                func,
                *iterables,
                timeout=timeout,
                chunksize=chunksize,
            )
        )

    @staticmethod
    def _attach_callback(future: Future[Any], callback: Callable[[Any], Any]) -> None:
        def _wrapper(done_future: Future[Any]) -> None:
            if done_future.cancelled():
                return
            exception = done_future.exception()
            if exception is not None:
                callback(exception)
                return
            callback(done_future.result())

        future.add_done_callback(_wrapper)

    def cancel(self, task_id: str) -> bool:
        """Cancel a task by id if it has not started."""

        with self._lock:
            future = self._futures.get(task_id)
        if future is None:
            return False
        return future.cancel()

    def cancel_all(self) -> int:
        """Cancel all pending tasks and return the number cancelled."""

        cancelled = 0
        with self._lock:
            futures = list(self._futures.values())
        for future in futures:
            if future.cancel():
                cancelled += 1
        return cancelled

    def get_stats(self) -> dict[str, int]:
        """Return a snapshot of pool statistics."""

        with self._lock:
            return dict(self._stats)

    def get_task_ids(self) -> list[str]:
        """Return currently tracked task ids."""

        with self._lock:
            return list(self._futures.keys())

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """Shut down the underlying executor."""

        if self._shutdown:
            return
        self._shutdown = True
        self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
        if cancel_futures:
            with self._lock:
                self._futures.clear()
                self._stats["running"] = 0

    def __enter__(self) -> "ThreadPool":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()


__all__ = ["ThreadPool"]
