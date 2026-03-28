from __future__ import annotations

import asyncio
import inspect
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ....modules.request import Requests
from ....async_ import Async
from ....exceptions import MeetCheckError, No, Notfound
from ....file import Directory, FileHandle
from ....logger import Logger
from ....threadpool import ThreadPool
from ljp_page.core.base.base_class import Ljp_BaseClass, Ljp_Decorator


class Mode:
    # 运行模式常量
    MODE1 = "mode1"
    MODE2 = "mode2"
    MODE3 = "mode3"


class BasePc(Ljp_BaseClass):
    # 基础调度框架：统一会话、队列、并发控制
    @dataclass
    class Config:
        base_url: str
        save_path: str
        p2_url: str
        p1_url: Optional[str] = None

        threadpool_thread_num: int = 10
        max_workers: int = 5
        start_id: int = 1
        end_id: int = 5
        id_ls: Optional[List[Any]] = None

        proxy_list: Optional[List[str]] = None
        max_retries: int = 3
        timeout: float = 10.0
        cookies: Dict[str, str] = field(default_factory=dict)
        headers: Dict[str, str] = field(default_factory=dict)

        mode: str = Mode.MODE1
        worker_startup_delay: float = 1.0
        queue_get_timeout: float = 2.0
        session_close_timeout: float = 2.0

        def __post_init__(self) -> None:
            self._validate_base_params()
            self._validate_p2_url()
            self._validate_save_path()
            self._validate_id_list()
            self._validate_mode_specific_params()

        def _validate_base_params(self) -> None:
            if not self.base_url:
                raise ValueError("config error: base_url cannot be empty")
            if not self.base_url.startswith("http"):
                raise ValueError(f"config error: base_url must start with http/https: {self.base_url}")

        def _validate_p2_url(self) -> None:
            if not self.p2_url:
                raise ValueError("config error: p2_url cannot be empty")
            if "{}" not in self.p2_url:
                raise ValueError(f"config error: p2_url must include '{{}}': {self.p2_url}")
            if not self.p2_url.startswith("http"):
                raise ValueError(f"config error: p2_url must start with http/https: {self.p2_url}")

        def _validate_save_path(self) -> None:
            if not self.save_path:
                raise ValueError("config error: save_path cannot be empty")

        def _validate_id_list(self) -> None:
            if self.id_ls is None:
                if self.start_id > self.end_id:
                    raise ValueError(
                        f"config error: start_id({self.start_id}) cannot be larger than end_id({self.end_id})"
                    )
                self.id_ls = list(range(self.start_id, self.end_id + 1))
            elif not isinstance(self.id_ls, list):
                self.id_ls = list(self.id_ls)

        def _validate_mode_specific_params(self) -> None:
            if self.mode == Mode.MODE2:
                if not self.p1_url:
                    raise ValueError("config error: mode2 requires p1_url")
                if "{}" not in self.p1_url:
                    raise ValueError(f"config error: p1_url must include '{{}}': {self.p1_url}")
                if not self.p1_url.startswith("http"):
                    raise ValueError(f"config error: p1_url must start with http/https: {self.p1_url}")

    @dataclass
    class P1Result:
        items: List[Any] = field(default_factory=list)
        next_url: Optional[str] = None

    @dataclass
    class P2ParseResult:
        title: str
        author: str
        description: str
        p3s: List[Tuple[str, str]]
        next_url: Optional[str] = None

    @dataclass
    class P3ParseResult:
        title: str
        content: str
        next_url: Optional[str] = None

    @dataclass
    class P2Result:
        id: Any
        url: str
        title: str
        author: str
        description: str
        p3s: List[Tuple[str, str]]
        total_p3: int

    @dataclass
    class P3Result:
        p2_title: str
        id: int
        title: str
        url: str
        content: str

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

    def _build_runtime(self) -> None:
        req_config = Requests.Config(
            proxy_list=self.config.proxy_list,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
            cookies=self.config.cookies,
            headers=self.config.headers,
        )
        self.req = Requests(req_config, logger=self.log)
        self.threadpool = ThreadPool(max_workers=self.config.threadpool_thread_num, logger=self.log)
        self.asy = Async(logger=self.log)
        self.Directory = Directory(self.config.save_path, logger=self.log)
        self.File_handle = FileHandle(max_open_files=200, logger=self.log)

    @staticmethod
    def name(fun: Any) -> str:
        return fun.__name__

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
        pass

    async def _create_session_impl(self, headers: Optional[Dict[str, str]] = None) -> Any:
        return await self.req.async_create_session(headers=headers)

    async def init_session(self, headers: Optional[Dict[str, str]] = None) -> None:
        if self.session is not None:
            return
        async with self._session_lock:
            if self.session is not None:
                return
            self.session = await self._create_session_impl(headers=headers or self.config.headers)
            await self.init_login()
            self.info("session initialized")

    def change_session_cookies(self, cookies: Dict[str, str], session: Any = None) -> None:
        target_session = session or self.session
        self.config.cookies.update(cookies)
        if target_session is not None:
            self.req.update_cookies(target_session, cookies)

    def add_task(self, work_id: Any) -> None:
        try:
            if self.asy and self.asy.loop and self.asy.loop.is_running():
                self.asy.loop.call_soon_threadsafe(self.work_queue.put_nowait, work_id)
            else:
                self.work_queue.put_nowait(work_id)
            self.info(f"task queued: {work_id}")
        except Exception as exc:
            self.error(f"add task failed: {exc}")

    async def parse_html(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        # 解析逻辑放到线程池，避免阻塞事件循环
        return await asyncio.wrap_future(self.threadpool.submit(func, *args, **kwargs))

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
                    self.work_queue.get(), timeout=self.config.queue_get_timeout
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
        await self.asy.submit_inside_s(tasks, return_exceptions=True)

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
        await self.asy.submit_inside_s(tasks, return_exceptions=True)

    async def _mode3(self) -> None:
        pass

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
            result = self.asy.submit(self._run(), await_result=blocking)
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

        loop = self.asy.loop if self.asy else None
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
        if self.File_handle:
            self._await_cleanup(
                self.File_handle.close_all(), timeout=self.config.session_close_timeout
            )

    def _shutdown_threadpool(self) -> None:
        if self.threadpool:
            self.threadpool.shutdown()

    def _stop_async(self) -> None:
        if self.asy:
            self.asy.stop()

    def _stop(self) -> None:
        self._close_session()
        self._cleanup_file_handle()
        self._shutdown_threadpool()
        self._stop_async()

    def __del__(self) -> None:
        try:
            self._stop()
        except Exception:
            pass


class BaseManager(Ljp_BaseClass):
    # 章节写入管理器：负责顺序写盘和收尾动作
    P2Result = BasePc.P2Result
    P3Result = BasePc.P3Result

    def __init__(self, pc: "Pc", data: P2Result, file_handle: Any, log: Logger) -> None:
        self.pc = pc
        self.data = data
        self.file_handle = file_handle
        self.logger = log

        self.expected_id = 1
        self.pending: Dict[int, BaseManager.P3Result] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

        super().__init__(self.logger)

    async def add_p3(self, p3: P3Result) -> None:
        raise NotImplementedError("add_p3 must be implemented")

    async def init(self) -> bool:
        if self._initialized:
            return True
        self._initialized = True

        try:
            result = self.target_init()
            if inspect.isawaitable(result):
                await result
            self.info(f"manager initialized: {self.data.title}")
            return True
        except Exception as exc:
            self.error(f"manager init failed: {self.data.title}, error: {exc}")
            return False

    async def target_init(self) -> None:
        pass

    async def finish(self) -> None:
        self.info(f"manager finished: {self.data.title}")

    @staticmethod
    def sanitize_filename(title: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', "_", title)

    @staticmethod
    def get_file_path(title: str) -> str:
        return f"{title}.txt"

    def _get_p_mode(self, title: str, index: int) -> str:
        return title


class Pc(BasePc):
    # 文本站点业务基类：实现 p1/p2/p3 主流程
    def __init__(
        self,
        config: BasePc.Config,
        log: Logger = None,
        MainWindows_ui: Any = None,
        stop_flag: bool = False,
        pause_flag: bool = False,
    ) -> None:
        super().__init__(
            config=config,
            log=log,
            MainWindows_ui=MainWindows_ui,
            stop_flag=stop_flag,
            pause_flag=pause_flag,
        )
        self.manager = self.get_manager()
        if self.manager is None:
            raise NotImplementedError("get_manager must return manager class")

    @Ljp_Decorator.handle_exceptions(MeetCheckError, BasePc.meet_fanpa)
    async def get(self, session: Any, url: str, *args: Any, **kwargs: Any) -> Any:
        self.debug(f"request url: {url}", self.get.__name__)
        return await self.req.async_get(session=session, url=url, *args, **kwargs)

    def parse_p1(self, res_html: str, url: str) -> BasePc.P1Result:
        raise NotImplementedError("parse_p1 is required")

    def parse_p2(self, res_html: str, url: str) -> BasePc.P2ParseResult:
        raise NotImplementedError("parse_p2 is required")

    def parse_p3(self, res_html: str, url: str) -> BasePc.P3ParseResult:
        raise NotImplementedError("parse_p3 is required")

    async def _process_page(self, page_id: Any) -> List[Any]:
        if not self.config.p1_url:
            raise ValueError("mode2 requires p1_url")

        page_url = self.config.p1_url.format(page_id)
        html_str = await self.get(session=self.session, url=page_url)
        if not html_str:
            return []

        result = await self.parse_html(self.parse_p1, html_str, page_url)
        if not isinstance(result, self.P1Result):
            raise TypeError("parse_p1 must return P1Result")
        return result.items

    async def _fetch_p2(self, p2_id: Any) -> BasePc.P2Result:
        base_url = self.config.p2_url.format(p2_id)
        current_url = base_url

        all_p3s: List[Tuple[str, str]] = []
        title = ""
        author = ""
        description = ""

        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            try:
                html_str = await self.get(session=self.session, url=current_url)
                if not html_str:
                    raise No(f"empty p2 response: id={p2_id}, url={current_url}")

                parsed = await self.parse_html(self.parse_p2, html_str, current_url)
                if not isinstance(parsed, self.P2ParseResult):
                    raise TypeError("parse_p2 must return P2ParseResult")

                if not title:
                    title = parsed.title
                if not author:
                    author = parsed.author
                if not description:
                    description = parsed.description

                if parsed.p3s:
                    all_p3s.extend(parsed.p3s)

                if not parsed.next_url or parsed.next_url == current_url:
                    break
                current_url = parsed.next_url

            except MeetCheckError:
                continue
            except Exception as exc:
                self.error(f"fetch p2 failed: id={p2_id}, url={current_url}, error={exc}")
                raise No(f"fetch p2 failed: id={p2_id}, url={current_url}", e=exc)

        return self.P2Result(
            id=p2_id,
            url=base_url,
            title=title or str(p2_id),
            author=author,
            description=description,
            p3s=all_p3s,
            total_p3=len(all_p3s),
        )

    async def _parse_p3_info(
        self,
        p3_id: int,
        p3: Tuple[str, str],
        p2_title: str,
        manager: BaseManager,
    ) -> None:
        chapter_title, chapter_url = p3
        current_url = chapter_url
        chunks: List[str] = []

        while current_url:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            try:
                html_str = await self.get(session=self.session, url=current_url)
                if not html_str:
                    self.warning(f"empty p3 response: id={p3_id}, url={current_url}")
                    break

                parsed = await self.parse_html(self.parse_p3, html_str, current_url)
                if not isinstance(parsed, self.P3ParseResult):
                    raise TypeError("parse_p3 must return P3ParseResult")

                if not chapter_title:
                    chapter_title = parsed.title
                if parsed.content and parsed.content.strip():
                    chunks.append(parsed.content)

                if not parsed.next_url or parsed.next_url == current_url:
                    break
                current_url = parsed.next_url

            except MeetCheckError:
                continue
            except Exception as exc:
                self.error(f"fetch p3 failed: id={p3_id}, url={current_url}, error={exc}")
                break

        p3_result = self.P3Result(
            p2_title=p2_title,
            id=p3_id,
            title=chapter_title,
            url=chapter_url,
            content="\n".join(chunks),
        )
        await manager.add_p3(p3_result)

    async def download(self, p2_result: BasePc.P2Result) -> None:
        try:
            safe_title = self.manager.sanitize_filename(p2_result.title)
            path = self.manager.get_file_path(safe_title)
            file_path = self.Directory.get_file_path(path)
            file_handle = await self._get_file_handle(file_path)
            if file_handle is None:
                raise No(f"get file handle failed: {file_path}")

            manager = self.manager(self, p2_result, file_handle, self.log)
            if not await manager.init():
                return

            tasks = []
            for chapter_id, chapter in enumerate(p2_result.p3s, start=1):
                tasks.append(self._parse_p3_info(chapter_id, chapter, p2_result.title, manager))

            results = await self.asy.submit_inside_s(tasks, return_exceptions=True)
            for item in results:
                if isinstance(item, Exception):
                    self.error(f"chapter task error: {item}")

            await manager.finish()
        except Exception as exc:
            self.error(f"download flow failed: {exc}")
            raise No("download flow failed", e=exc)

    async def work(self, work_id: Any) -> None:
        try:
            p2_result = await self._fetch_p2(work_id)
            if self.ui and hasattr(self.ui, "add_p2"):
                ui_result = self.ui.add_p2(p2_result)
                if inspect.isawaitable(ui_result):
                    await ui_result
            else:
                await self.download(p2_result)
        except Notfound as exc:
            self.warning(f"resource not found id={work_id}: {exc}")
        except Exception as exc:
            self.error(f"work failed id={work_id}: {exc}")

    def get_manager(self) -> Any:
        raise NotImplementedError("get_manager is required")

    async def _get_file_handle(self, file_path: str) -> Any:
        return await self.File_handle.get(file_path)


class Ys(Pc):
    class Manager(BaseManager):
        pass

    def get_manager(self) -> Any:
        self.manager = self.Manager
        return self.manager


if __name__ == "__main__":
    pass
