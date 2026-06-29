# 05-19-16-00-00
"""new_pc 队列调度组件。"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ljp_page._core.base import Ljp_BaseClass_Logger

if TYPE_CHECKING:
    from ljp_page._module.runtime import LJPExc

    from .model import Config
    from .pc import BasePc


class Pc_Base_Scheduler(Ljp_BaseClass_Logger):
    """封装 mode1/mode2/mode3 的生产消费队列。"""

    P2_STOP = object()

    def __init__(self, owner: BasePc, config: Config, exc: LJPExc, logger: Any = None) -> None:
        super().__init__()
        self.set_logger(logger)
        self.owner = owner
        self.config = config
        self.exc = exc
        self.p1_queue = asyncio.Queue()
        self.p2_queue = asyncio.Queue()
        self.p3_queue = asyncio.Queue()

    def reset_p1_queue(self) -> None:
        self._clear_queue(self.p1_queue)
        for p1_id in self.config.id_ls:
            self.p1_queue.put_nowait(p1_id)

    def reset_p2_queue_from_config(self) -> None:
        self._clear_queue(self.p2_queue)
        for p2_id in self.config.id_ls:
            self.p2_queue.put_nowait(p2_id)

    @staticmethod
    def _clear_queue(queue: asyncio.Queue) -> None:
        while True:
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break


    async def p1_work_loop(self) -> None:
        while True:
            if self.owner.stop_flag:
                break

            await self.owner.pause_event.wait()

            if self.p1_queue.empty():
                break

            try:
                p1_id = self.p1_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue

            try:
                res = await self.owner.get_p1_result(p1_id)
                items = res.items
                for item in items:
                    await self.p2_queue.put(item)
                self.info(f"p1 {p1_id} 添加了{len(items)} 个任务")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.error(f"p1_work_loop 失败 {p1_id}: {exc}")
            finally:
                self.p1_queue.task_done()

    async def p2_work_loop(self) -> None:
        await asyncio.sleep(self.config.worker_startup_delay)
        while True:
            if self.owner.stop_flag:
                break
            await self.owner.pause_event.wait()

            has_task = False
            try:
                p1_item = await asyncio.wait_for(
                    self.p2_queue.get(),
                    timeout=self.config.queue_get_timeout,
                )
                has_task = True
                if p1_item is self.P2_STOP:
                    self.debug("p2 worker 收到结束标识")
                    break
                await self.owner.get_p2_result(p1_item)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                self.info("worker cancelled")
                raise
            except Exception as exc:
                self.error(f"worker error: {exc}")
            finally:
                if has_task:
                    self.p2_queue.task_done()

    async def mode1(self) -> None:
        p2_worker_count = max(1, self.config.max_workers)
        self.reset_p2_queue_from_config()
        await self.put_p2_stop_flag(p2_worker_count)
        handles = self.exc.submit_many(
            [self.p2_work_loop() for _ in range(p2_worker_count)],
            mode="async",
        )
        for handle in handles:
            await handle

    async def mode2(self) -> None:
        await self.run_pipeline(p1_worker_count=1, p2_worker_count=max(1, self.config.max_workers))

    async def mode3(self) -> None:
        p1_worker_count = max(1, min(self.config.max_workers, len(self.config.id_ls or [])))
        p2_worker_count = max(1, self.config.max_workers)
        await self.run_pipeline(p1_worker_count=p1_worker_count, p2_worker_count=p2_worker_count)

    async def run_pipeline(self, p1_worker_count: int, p2_worker_count: int) -> None:
        p1_handles = self.exc.submit_many(
            [self.p1_work_loop() for _ in range(p1_worker_count)],
            mode="async",
        )
        p2_handles = self.exc.submit_many(
            [self.p2_work_loop() for _ in range(p2_worker_count)],
            mode="async",
        )

        try:
            for handle in p1_handles:
                await handle
        finally:
            await self.put_p2_stop_flag(p2_worker_count)

        for handle in p2_handles:
            await handle

    async def put_p2_stop_flag(self, worker_count: int) -> None:
        # 每个消费者都需要一个结束标识，避免只退出一个 worker。
        for _ in range(worker_count):
            await self.p2_queue.put(self.P2_STOP)


__all__ = ["Pc_Base_Scheduler"]
