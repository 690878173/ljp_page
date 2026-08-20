"""流水线调度器 —— P1→P2 生产者消费者队列。"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable

from ljp_page._module.runtime import LJPExc
from ljp_page.logger import loguru_logger

from .config import Config
from .controller import LifecycleController


class PipelineScheduler:
    """管理 P1→P2 流水线的队列与工作循环。

    通过回调与 BasePc 解耦：
        on_fetch_p1(p1_id) -> P1Result
        on_process_p2(p1_item) -> None
    """

    _STOP = object()

    def __init__(
        self,
        config: Config,
        controller: LifecycleController,
        exc: LJPExc,
        on_fetch_p1: Callable[[str], Awaitable[Any]],
        on_process_p2: Callable[[Any], Awaitable[Any]],
    ) -> None:
        self.config = config
        self.controller = controller
        self.exc = exc
        self._on_fetch_p1 = on_fetch_p1
        self._on_process_p2 = on_process_p2
        self.p1_queue: asyncio.Queue[str] = asyncio.Queue()
        self.p2_queue: asyncio.Queue[Any] = asyncio.Queue()

    # ---- 队列操作 ----

    def reset_p1_queue(self) -> None:
        self._clear(self.p1_queue)
        for p1_id in self.config.id_list:
            self.p1_queue.put_nowait(p1_id)

    def reset_p2_queue_from_config(self) -> None:
        self._clear(self.p2_queue)
        for p2_id in self.config.id_list:
            self.p2_queue.put_nowait(p2_id)

    @staticmethod
    def _clear(q: asyncio.Queue) -> None:
        while True:
            try:
                q.get_nowait()
                q.task_done()
            except asyncio.QueueEmpty:
                break

    # ---- 工作循环 ----

    async def _p1_worker(self) -> None:
        while not self.controller.stopped:
            await self.controller.wait_if_paused()
            if self.p1_queue.empty():
                break
            try:
                p1_id = self.p1_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue
            try:
                result = await self._on_fetch_p1(p1_id)
                for item in result.items:
                    await self.p2_queue.put(item)
                loguru_logger.info(f"P1 [{p1_id}] 产出 {len(result.items)} 个任务")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                loguru_logger.error(f"P1 worker 失败 [{p1_id}]: {exc}")
            finally:
                self.p1_queue.task_done()

    async def _p2_worker(self) -> None:
        await asyncio.sleep(self.config.worker_startup_delay)
        while not self.controller.stopped:
            await self.controller.wait_if_paused()
            try:
                item = await asyncio.wait_for(
                    self.p2_queue.get(), timeout=self.config.queue_get_timeout,
                )
                if item is self._STOP:
                    break
                await self._on_process_p2(item)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                loguru_logger.error(f"P2 worker 失败: {exc}")
            finally:
                self.p2_queue.task_done()

    # ---- 模式入口 ----

    async def mode1(self) -> None:
        """MODE1: 直接从 config.id_list 驱动 P2。"""
        worker_count = max(1, self.config.max_workers)
        self.reset_p2_queue_from_config()
        await self._put_stop_flags(worker_count)
        handles = self.exc.submit_many(
            [self._p2_worker() for _ in range(worker_count)], mode="async",
        )
        for h in handles:
            await h

    async def mode2(self) -> None:
        """MODE2: 单 P1 → 多 P2 串行流水线。"""
        await self._run_pipeline(p1_count=1, p2_count=max(1, self.config.max_workers))

    async def mode3(self) -> None:
        """MODE3: 多 P1 → 多 P2 并行流水线。"""
        p1_count = max(1, min(self.config.max_workers, len(self.config.id_list or [])))
        p2_count = max(1, self.config.max_workers)
        await self._run_pipeline(p1_count=p1_count, p2_count=p2_count)

    async def _run_pipeline(self, p1_count: int, p2_count: int) -> None:
        p1_handles = self.exc.submit_many(
            [self._p1_worker() for _ in range(p1_count)], mode="async",
        )
        p2_handles = self.exc.submit_many(
            [self._p2_worker() for _ in range(p2_count)], mode="async",
        )
        try:
            for h in p1_handles:
                await h
        finally:
            await self._put_stop_flags(p2_count)
        for h in p2_handles:
            await h

    async def _put_stop_flags(self, count: int) -> None:
        for _ in range(count):
            await self.p2_queue.put(self._STOP)
