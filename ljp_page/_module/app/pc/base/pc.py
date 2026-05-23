from __future__ import annotations

import asyncio
import threading
from abc import abstractmethod

from ljp_page._core.base import Ljp_BaseClass_Logger
from ljp_page._core.utils.other import f_mark
from ljp_page._module.runtime import LJPExc
from ljp_page.logger import logger

from .file_manager import PcFileManager
from .model import Config, ModeType, P1Item, P1Result, P2Item, P2Result, P3Item
from .parser import PcParser
from .request_manager import PcRequest
from .scheduler import PcScheduler


class BasePc(Ljp_BaseClass_Logger):
    """new_pc 门面基类。

    BasePc 对外仍然是业务类唯一需要继承的父类；内部通过 req、scheduler、
    file_hd、exc 组合出请求、调度、文件和运行时能力。
    """

    Config = Config
    P1Result = P1Result
    P2Result = P2Result
    P1Item = P1Item
    P2Item = P2Item
    P3Item = P3Item

    def __init__(self, config: Config, main_ui=None):
        super().__init__()
        self.config = config
        self.ui = main_ui
        self.logger = logger
        self.stop_flag = False
        self.pause_flag = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()

        self.meet_fp_event = asyncio.Event()
        self.meet_fp_lock = asyncio.Lock()
        self._stop_lock = threading.RLock()
        self._stopped = False
        self.exc = LJPExc(self.logger)
        self.exc.set_semaphore("sem2", self.config.chapter_concurrency)

        self.file_hd = PcFileManager(self.config)
        self.resource_manager = self.file_hd
        self.directory = self.file_hd.directory
        self.file_handler = self.file_hd.file_handler
        self.Fp = self.req.Fp
        self.parser = PcParser(self.exc, self.logger)

        self.scheduler = PcScheduler(self, self.config, self.exc, self.logger)

        self.mode_handlers = {
            ModeType.MODE1: self.scheduler.mode1,
            ModeType.MODE2: self.scheduler.mode2,
            ModeType.MODE3: self.scheduler.mode3,
        }
        self.build_other()

    def get_req(self):
        return PcRequest(self,config=self.config)

    def build_other(self) -> None:
        self.manager = self.get_manager()
        self.req = self.get_req()

    @abstractmethod
    def get_manager(self):
        pass


    async def check_meet_fp(self, res) -> bool:
        return False

    async def fp_do(self, session, url, *args, **kwargs):
        pass

    def html_parse_error(self, html):
        pass

    async def _p1_work(self, p1_id):
        return [p1_id]


    def run(self, blocking: bool = True):
        res = self.exc.submit(self._run())
        if not blocking:
            return res

        try:
            res.result()
            self.info("all tasks completed")
        except KeyboardInterrupt:
            self.warning("interrupted by user")
            return None
        finally:
            self._stop()

    async def _run(self):
        self.scheduler.reset_p1_queue()
        await self.req.init_session()
        await self.before_run()
        handler = self.mode_handlers.get(self.config.mode)
        if handler is None:
            self.error(f"unknown mode: {self.config.mode}")
            return
        await handler()
        await self.after_run()

    @f_mark('运行前执行操作')
    async def before_run(self):
        pass
    @f_mark('运行后操作')
    async def after_run(self):
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

    def _stop(self):
        if self._stopped:
            return
        self._stopped = True
        self.debug("stop")

        try:
            self.exc.submit(
                self.req.close(),
                mode="async",
                timeout=self.config.session_close_timeout,
            ).result(timeout=self.config.session_close_timeout)
        except Exception as exc:
            self.error(f"session close error: {exc}")

        try:
            self.exc.submit(
                self.file_hd.close(),
                mode="async",
                timeout=self.config.session_close_timeout,
            ).result(timeout=self.config.session_close_timeout)
        except Exception as exc:
            self.error(f"file handler close error: {exc}")

        try:
            self.exc.shutdown()
        except Exception as exc:
            self.error(f"runtime shutdown error: {exc}")

    def close(self) -> None:
        self._stop()


__all__ = ["BasePc"]
