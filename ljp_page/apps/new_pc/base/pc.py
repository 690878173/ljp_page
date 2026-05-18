
import asyncio
import threading
from abc import abstractmethod
import inspect
from urllib.parse import urlparse

from ljp_page._core._base_class import Ljp_Logger
from ljp_page._core._exceptions import ParseError
from ljp_page._modules.request.cg_session.session import AsyncSession as Session
from ljp_page._modules.request.cg_session.fp import FP

from ljp_page._runtime.ljp_exc import LJPExc
from ljp_page.logger import logger

from .model import Config, ModeType, P2Item, P2Result, P3Item, P1Result,P1Item
from ljp_page._modules.file import Directory, FileHandler

class _BasePc(Ljp_Logger):
    Config = Config

    stop_flag = False
    pause_flag = False
    P1Result = P1Result
    P2Result = P2Result
    P1Item = P1Item
    P2Item = P2Item
    P3Item = P3Item

    Fp = FP()


    def __init__(self, config: Config,main_ui = None):
        super().__init__()
        self.config = config
        self.ui = main_ui
        self.logger = logger
        self.Fp = FP()
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.meet_fp_event = asyncio.Event()
        self.meet_fp_lock = asyncio.Lock()

        self._stop_lock = threading.RLock()
        self.session =  None
        self._session_lock = asyncio.Lock()

        self.p1_queue = asyncio.Queue()
        self.p2_queue = asyncio.Queue()
        self.p3_queue = asyncio.Queue()







        self.mode_handlers = {
            ModeType.MODE1: self._mode1,
            ModeType.MODE2: self._mode2,
            ModeType.MODE3: self._mode3,
        }

        self._stopped = False


        self._build_runtime()
        self.build_other()

    def _build_runtime(self):
        self.exc = LJPExc(self.logger)

    def build_other(self):
        pass

    def stop(self) -> None:
        self.stop_flag = True
        self.pause_event.set()

    def pause(self) -> None:
        self.pause_flag = True
        self.pause_event.clear()
        self.info("任务暂停")

    def resume(self) -> None:
        self.pause_flag = False
        self.pause_event.set()
        self.info("任务继续")

    def _it_queue(self):
        while True:
            try:
                self.p1_queue.get_nowait()
                self.p1_queue.task_done()
            except asyncio.QueueEmpty:
                break

        for p1_id in self.config.id_ls:
            self.p1_queue.put_nowait(p1_id)

    def _it_p2_queue(self):
        while True:
            try:
                self.p2_queue.get_nowait()
                self.p2_queue.task_done()
            except asyncio.QueueEmpty:
                break

        for p2_id in self.config.id_ls:
            self.p2_queue.put_nowait(p2_id)

    async def init_session(self) -> None:
        if self.session is not None:
            return
        async with self._session_lock:
            if self.session is not None:
                return
            self.session = Session(self.config.ljp_config,logger=self.logger)
            self.info("session 初始化")

    async def fp(self,res):
        return False

    async def fp_do(self,session,url,*args,**kwargs):
        pass



    @abstractmethod
    def run(self, blocking: bool = True):
        pass

    @abstractmethod
    async def _run(self):
        pass

    @abstractmethod
    async def _mode1(self):
        # 直接传入id返回详细页面
        pass

    @abstractmethod
    async def _mode2(self):
        # id是分页页面，再次进入才是详细页面
        pass

    @abstractmethod
    async def _mode3(self):
        pass


class BasePc(_BasePc):

    def __init__(self, config: Config, main_ui = None):
        super().__init__(config, main_ui)

        self._p1_producer_finished = False

    @staticmethod
    def _is_absolute_url(value) -> bool:
        return urlparse(str(value or "")).scheme in {"http", "https"}

    def _normalize_url(self, value) -> str:
        url = str(value or "")
        if self._is_absolute_url(url):
            return url
        return url

    def _format_or_normalize_url(self, template, value) -> str:
        if hasattr(value, "url"):
            return self._normalize_url(value.url)
        if self._is_absolute_url(value):
            return str(value)
        if template:
            return self._normalize_url(template.format(value))
        return self._normalize_url(value)

    def format_p2_url(self,p2_id):
        return self._format_or_normalize_url(self.config.p2_url, p2_id)

    def format_p1_url(self,p1_id):
        return self._format_or_normalize_url(self.config.p1_url, p1_id)

    def format_p3_url(self,p3_id):
        return self._format_or_normalize_url(self.config.p3_url, p3_id)

    @abstractmethod
    def get_manager(self):
        pass

    def build_other(self) -> None:
        self.manager = self.get_manager()
        self.directory = Directory(
            self.config.save_path,
            directory_num=self.config.directory_num,
            mode=self.config.directory_mode,
            logger=self.logger,
        )
        self.file_handler = FileHandler(
            max_open_files=self.config.max_open_files,
            logger=self.logger,
        )
        self.exc.set_semaphore("sem2", self.config.chapter_concurrency)

    def html_parse_error(self,html):
        pass

    async def do_get(self,session,url,*args,**kwargs):
        self.debug(f"get url:{url}")
        kwargs.setdefault("return_type", "text")
        res = await session.get(url, *args, **kwargs)

        return res

    async def get(self, session, url, *args, **kwargs):
        seen_version = await self.Fp.before_request()
        res = await self.do_get(session, url, *args, **kwargs)

        if not await self.fp(res.text):
            return res

        await self.Fp.handle_blocked(
            seen_version,
            self.fp_do,
            session,
            url,
            *args,
            **kwargs,
        )

        return res


    async def parse_html(self,func,*args,**kwargs):
        try:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            handle = self.exc.submit(func, *args, mode="thread", **kwargs)
            return await handle
        except Exception as exc:
            raise ParseError(e=exc,message='解析出错')

    async def _p1_work_loop(self):
        while True:
            if self.stop_flag:
                break

            await self.pause_event.wait()

            if self._p1_producer_finished:
                break
            if self.p1_queue.empty():
                self._p1_producer_finished = True
                break

            try:
                p1_id = self.p1_queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue

            try:
                items = await self._p1_work(p1_id)
                for item in items:
                    await self.p2_queue.put(item)
                self.info(f'p1 {p1_id} 添加了{len(items)} 个任务')

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                self.error(f"_p1_work_loop failed {p1_id}: {exc}")
            finally:
                self.p1_queue.task_done()


    async def _p1_work(self, p1_id):
        return [p1_id]

    async def _p2_work_loop(self):
        await asyncio.sleep(self.config.worker_startup_delay)
        while True:
            if self.stop_flag:
                break
            await self.pause_event.wait()

            if self._p1_producer_finished and self.p2_queue.empty():
                self.debug("p2 队列全部处理完成")
                break

            has_task = False
            try:
                p2_id = await asyncio.wait_for(
                    self.p2_queue.get(),
                    timeout=self.config.queue_get_timeout,
                )
                has_task = True
                await self._p2_work(p2_id)

            except asyncio.TimeoutError:
                self.warning(f"_p2_work_loop 获取超时")
                continue
            except asyncio.CancelledError:
                self.info("worker cancelled")
                raise
            except Exception as exc:
                self.error(f"worker error: {exc}")
            finally:
                if has_task:
                    self.p2_queue.task_done()


    @abstractmethod
    async def p2_work(self, p2_id):
        pass

    async def _p2_work(self,p2_id):
        self.debug(f'_p2_work: {p2_id}')
        try:
            await self.init_session()
            await self.p2_work(p2_id)

        except asyncio.CancelledError:
            self.info(f"任务取消: {p2_id}")
            raise

        except Exception as exc:
            self.error(f"task failed {p2_id}: {exc}")



    async def _mode1(self):
        self._p1_producer_finished = True
        self._it_p2_queue()
        tasks = [self._p2_work_loop() for _ in range(self.config.max_workers)]
        hds = self.exc.submit_many(tasks, mode="async")
        res = []
        for task in hds:
            res.append(await task)

    async def _mode2(self):
        tasks = [self._p1_work_loop()] + [
            self._p2_work_loop() for _ in range(self.config.max_workers)
        ]
        hds = self.exc.submit_many(tasks, mode="async")
        res = []
        for task in hds:
            res.append(await task)


    async def _mode3(self):
        self._p1_producer_finished = False
        p1_worker_count = max(1, min(self.config.max_workers, len(self.config.id_ls or [])))
        p2_worker_count = max(1, self.config.max_workers)
        tasks = [self._p1_work_loop() for _ in range(p1_worker_count)] + [
            self._p2_work_loop() for _ in range(p2_worker_count)
        ]
        hds = self.exc.submit_many(tasks, mode="async")
        res = []
        for task in hds:
            res.append(await task)



    async def before_run(self):
        pass

    async def after_run(self):
        pass


    def run(self, blocking: bool = True):
        try:
            res = self.exc.submit(self._run())
            res.result()
            if blocking:
                self.info("all tasks completed")

        except KeyboardInterrupt:
            self.warning("interrupted by user")
            return None
        finally:

            self._stop()

    async def _run(self):
        self._it_queue()
        await self.init_session()
        await self.before_run()
        handler = self.mode_handlers.get(self.config.mode)
        if handler is None:
            self.error(f"unknown mode: {self.config.mode}")
            return
        await handler()
        self._p1_producer_finished = True

        await self.after_run()



    def _stop(self):
        try:
            self.debug("stop")
            if self.session is not None:
                self.exc.submit(
                    self.session.close(),
                    timeout=self.config.session_close_timeout,
                ).result(timeout=self.config.session_close_timeout)

            if self.file_handler is not None:
                self.exc.submit(
                    self.file_handler.close_all(),
                    mode="async",
                    timeout=self.config.session_close_timeout,
                ).result(timeout=self.config.session_close_timeout)

            self.exc.shutdown()
        except Exception as exc:
            self.error(f"stop error: {exc}")

















