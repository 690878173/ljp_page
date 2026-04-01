# 03-31-22-35-00
"""PC crawler runtime base class."""

from __future__ import annotations

import asyncio
import inspect
import threading
from typing import Any, Dict, List, Optional

from ....file import Directory, FileHandle
from ....logger import Logger
from ....modules.request import Requests
from ljp_page.core.base.Ljp_base_class import Ljp_BaseClass

from .models import Mode, P1Result, P2ParseResult, P2Result, P3ParseResult, P3Result, PcConfig
from .runtime_executor import CrawlerRuntime, CrawlerRuntimeConfig


class BasePc(Ljp_BaseClass):
    """Shared runtime base class for PC crawlers."""

    Config = PcConfig
    P1Result = P1Result
    P2ParseResult = P2ParseResult
    P3ParseResult = P3ParseResult
    P2Result = P2Result
    P3Result = P3Result

    def __init__(
        self,
        config: Config,
        log: Logger = None,
        MainWindows_ui: Any = None,
        stop_flag: bool = False,
        pause_flag: bool = False,
    ) -> None:
        self.config = config
        self.ui = MainWindows_ui

        self.queue_1: asyncio.Queue = asyncio.Queue()
        self.work_queue: asyncio.Queue = asyncio.Queue()

        self.stop_flag = stop_flag
        self.pause_flag = pause_flag
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.session: Optional[Any] = None
        self._session_lock = asyncio.Lock()

        self.log = log or Logger()
        super().__init__(self.log)

        self._build_runtime()
        self.mode_handlers = {
            Mode.MODE1: self._mode1,
            Mode.MODE2: self._mode2,
            Mode.MODE3: self._mode3,
        }
        self._stop_lock = threading.RLock()
        self._stopped = False

    def _build_runtime(self) -> None:
        req_config = self.config.build_request_config()
        self.req = Requests(req_config, logger=self.log)
        self.runtime = CrawlerRuntime(
            CrawlerRuntimeConfig(
                thread_max_workers=self.config.threadpool_thread_num,
                async_outer_concurrent=self.config.runtime_outer_concurrent,
                async_inner_concurrent=self.config.runtime_inner_concurrent,
            ),
            logger=self.log,
        )

        self.directory = Directory(self.config.save_path, logger=self.log)
        self.file_handle = FileHandle(max_open_files=self.config.max_open_files, logger=self.log)

    def _should_exit(self) -> bool:
        if self.stop_flag:
            return True
        return self.ui is None and self.work_queue.empty() and self.queue_1.empty()

    def stop(self) -> None:
        self.stop_flag = True
        self.pause_event.set()

    def pause(self) -> None:
        self.pause_flag = True
        self.pause_event.clear()
        self.info("task paused")

    def resume(self) -> None:
        self.pause_flag = False
        self.pause_event.set()
        self.info("task resumed")

    async def meet_fanpa(self, exc: Exception, func: Any, *args: Any, **kwargs: Any) -> Any:
        self.error(f"anti crawler triggered: {exc}")
        await asyncio.sleep(20)
        try:
            return await func(self, *args, **kwargs)
        except Exception:
            self.pause()
            await self.pause_event.wait()
            return await func(self, *args, **kwargs)

    async def init_login(self) -> None:
        return None

    async def _create_session_impl(self, headers: Optional[Dict[str, str]] = None) -> Any:
        return await self.req.async_create_session(headers=headers)

    async def init_session(self, headers: Optional[Dict[str, str]] = None) -> None:
        if self.session is not None:
            return
        async with self._session_lock:
            if self.session is not None:
                return
            default_headers = self.config.request_headers
            self.session = await self._create_session_impl(headers=headers or default_headers)
            await self.init_login()
            self.info("session initialized")

    def change_session_cookies(self, cookies: Dict[str, str], session: Any = None) -> None:
        target_session = session or self.session
        self.config.update_request_cookies(cookies)
        if target_session is not None:
            self.req.update_cookies(target_session, cookies)

    def add_task(self, work_id: Any) -> None:
        try:
            if not self.runtime.call_soon_threadsafe(self.work_queue.put_nowait, work_id):
                self.work_queue.put_nowait(work_id)
            self.info(f"task queued: {work_id}")
        except Exception as exc:
            self.error(f"add task failed: {exc}")

    async def parse_html(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return await self.runtime.run_in_thread(func, *args, **kwargs)

    async def work(self, work_id: Any) -> None:
        raise NotImplementedError("work must be implemented")

    async def _base_mode(self, work_id: Any) -> None:
        try:
            await self.init_session()
            await self.work(work_id)
        except asyncio.CancelledError:
            self.info(f"task cancelled: {work_id}")
            raise
        except Exception as exc:
            self.error(f"task failed {work_id}: {exc}")

    async def _worker(self) -> None:
        await asyncio.sleep(self.config.worker_startup_delay)
        while True:
            if self.stop_flag:
                break
            await self.pause_event.wait()
            if self._should_exit():
                break

            has_task = False
            try:
                work_id = await asyncio.wait_for(
                    self.work_queue.get(),
                    timeout=self.config.queue_get_timeout,
                )
                has_task = True
                await self._base_mode(work_id)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                self.info("worker cancelled")
                raise
            except Exception as exc:
                self.error(f"worker error: {exc}")
            finally:
                if has_task:
                    self.work_queue.task_done()

    async def _mode1(self) -> None:
        await self._transfer_seed_to_work_queue()
        tasks = [self._worker() for _ in range(self.config.max_workers)]
        await self.runtime.gather_inside(tasks, return_exceptions=True)

    async def _mode2(self) -> None:
        async def producer() -> None:
            while True:
                if self.stop_flag:
                    break
                await self.pause_event.wait()

                try:
                    page_id = self.queue_1.get_nowait()
                except asyncio.QueueEmpty:
                    break

                try:
                    self.info(f"processing page: {page_id}")
                    items = await self._process_page(page_id)
                    for item in items:
                        await self.work_queue.put(item)
                    self.info(f"page {page_id} generated {len(items)} tasks")
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self.error(f"page process failed {page_id}: {exc}")
                finally:
                    self.queue_1.task_done()

        tasks = [producer()] + [self._worker() for _ in range(self.config.max_workers)]
        await self.runtime.gather_inside(tasks, return_exceptions=True)

    async def _mode3(self) -> None:
        return None

    async def _process_page(self, page_id: Any) -> List[Any]:
        raise NotImplementedError("_process_page must be implemented for mode2")

    async def _transfer_seed_to_work_queue(self) -> None:
        while True:
            if self.stop_flag:
                break
            try:
                work_id = self.queue_1.get_nowait()
            except asyncio.QueueEmpty:
                break
            await self.work_queue.put(work_id)
            self.queue_1.task_done()

    def _initialize_seed_queue(self) -> None:
        while True:
            try:
                self.queue_1.get_nowait()
                self.queue_1.task_done()
            except asyncio.QueueEmpty:
                break

        for work_id in self.config.id_ls:
            self.queue_1.put_nowait(work_id)

    async def _execute_mode(self) -> None:
        handler = self.mode_handlers.get(self.config.mode)
        if handler is None:
            self.error(f"unknown mode: {self.config.mode}")
            return
        await handler()

    async def _run(self) -> None:
        self._initialize_seed_queue()
        await self.init_session()
        await self._execute_mode()

    def run(self, blocking: bool = True) -> Optional[Any]:
        try:
            result = self.runtime.run_async(self._run(), blocking=blocking)
            if blocking:
                self.info("all tasks completed")
            return result
        except KeyboardInterrupt:
            self.warning("interrupted by user")
            return None
        finally:
            if blocking:
                self._stop()

    def _await_cleanup(self, value: Any, timeout: float) -> None:
        if not inspect.isawaitable(value):
            return

        loop = self.runtime.get_event_loop()
        try:
            if loop and loop.is_running():
                future = asyncio.run_coroutine_threadsafe(value, loop)
                future.result(timeout=timeout)
                return
            asyncio.run(value)
        except Exception as exc:
            self.warning(f"cleanup coroutine failed: {exc}")

    def _close_session(self) -> None:
        current = self.session
        self.session = None
        if current is None:
            return

        close_method = getattr(current, "close", None)
        if close_method is None:
            return

        try:
            self._await_cleanup(close_method(), timeout=self.config.session_close_timeout)
        except Exception as exc:
            self.warning(f"close session failed: {exc}")

    def _cleanup_file_handle(self) -> None:
        if self.file_handle:
            self._await_cleanup(
                self.file_handle.close_all(),
                timeout=self.config.session_close_timeout,
            )

    def _shutdown_runtime(self) -> None:
        if self.runtime:
            self.runtime.shutdown(wait=True, cancel_futures=False, async_timeout=5.0)

    def _stop(self) -> None:
        with self._stop_lock:
            if self._stopped:
                return
            self._stopped = True

        self._close_session()
        self._cleanup_file_handle()
        self._shutdown_runtime()

    def __del__(self) -> None:
        try:
            self._stop()
        except Exception:
            pass


__all__ = ["BasePc"]
