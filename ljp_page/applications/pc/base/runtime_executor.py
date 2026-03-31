# 03-28-23-40-00
"""PC 爬虫运行时调度器：统一接入 LJPExc。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Sequence

from ljp_page.core.base.Ljp_base_class import Ljp_BaseClass
from ljp_page.runtime.ljp_exc.exc import LJPExc
from ljp_page.runtime.ljp_exc.task import TaskHandle


@dataclass(slots=True)
class CrawlerRuntimeConfig:
    """运行时并发配置。"""

    thread_max_workers: int = 10
    async_outer_concurrent: int = 20
    async_inner_concurrent: int = 100


class CrawlerRuntime(Ljp_BaseClass):
    """统一调度封装，负责线程任务与协程任务的提交。"""

    def __init__(self, config: CrawlerRuntimeConfig, logger: Any = None) -> None:
        super().__init__(logger=logger)
        self.config = config
        self.exc = LJPExc(
            logger=logger,
            thread_max_workers=config.thread_max_workers,
            async_outer_concurrent=config.async_outer_concurrent,
            async_inner_concurrent=config.async_inner_concurrent,
        )

    @property
    def thread_pool(self) -> Any:
        return self.exc.thread_pool

    @property
    def async_runtime(self) -> Any:
        return self.exc.asy

    def get_event_loop(self) -> asyncio.AbstractEventLoop | None:
        runtime = self.exc.asy
        if runtime is None:
            return None
        loop = runtime.loop
        if loop is None or loop.is_closed() or not loop.is_running():
            return None
        return loop

    def call_soon_threadsafe(self, callback: Callable[..., Any], *args: Any) -> bool:
        loop = self.get_event_loop()
        if loop is None:
            return False
        loop.call_soon_threadsafe(callback, *args)
        return True

    def run_async(self, coro: Awaitable[Any], blocking: bool = True) -> Any:
        """提交外层协程任务。blocking=True 时直接返回结果。"""

        handle = self.exc.submit(coro, mode="async")
        if blocking:
            return handle.result()
        return handle

    async def run_in_thread(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """在线程池中执行同步函数，并在协程中等待结果。"""

        handle = self.exc.submit(func, *args, mode="thread", **kwargs)
        return await handle

    async def gather_inside(
        self,
        coroutines: Iterable[Awaitable[Any]],
        *,
        return_exceptions: bool = False,
    ) -> list[Any]:
        """在内层并发语义下批量执行协程任务。"""

        tasks: Sequence[Awaitable[Any]] = list(coroutines)
        if not tasks:
            return []

        handles: list[TaskHandle[Any]] = self.exc.submit_many_inside(tasks, mode="async")
        results: list[Any] = []
        for handle in handles:
            try:
                results.append(await handle)
            except Exception as exc:
                if return_exceptions:
                    results.append(exc)
                else:
                    raise
        return results

    def shutdown(
        self,
        *,
        wait: bool = True,
        cancel_futures: bool = False,
        async_timeout: float = 5.0,
    ) -> None:
        self.exc.shutdown(
            wait=wait,
            cancel_futures=cancel_futures,
            async_timeout=async_timeout,
        )


__all__ = ["CrawlerRuntime", "CrawlerRuntimeConfig"]
