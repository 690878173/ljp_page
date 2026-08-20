"""流水线执行器基类 —— 业务爬虫的唯一继承入口。"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from ljp_page._core.utils.other import f_mark
from ljp_page._module.runtime import LJPExc
from ljp_page.logger import loguru_logger

from .config import Config
from .controller import LifecycleController
from .enums import PipelineMode
from .file_manager import FileManager
from .models import P1Item, P1Result, P2Item, P2Result, P3Item
from .parser import HtmlParser
from .request import BaseRequest, RequestManager
from .scheduler import PipelineScheduler


class BasePc(ABC):
    """流水线爬虫基类。

    子类需要实现:
        get_p1_result(p1_id) -> P1Result   — P1 列表解析
        get_p2_result(p1_item) -> P2Result — P2 详情解析
        get_manager() -> type              — 返回业务管理器类

    可选覆盖:
        check_meet_fp(html) -> bool       — 反爬检测
        fp_do(session, url, **kw)         — 反爬处理
        before_run() / after_run()        — 生命周期钩子
        html_parse_error(html)            — 解析错误回调
    """

    # ---- 构造与依赖注入 ----

    def __init__(self, config: Config, ui: Any = None) -> None:
        self.config = config
        self.ui = ui

        # 生命周期控制
        self.controller = LifecycleController()

        # 运行时
        self.exc = LJPExc(loguru_logger)
        self.exc.set_semaphore("sem2", config.chapter_concurrency)

        # 组件
        self.file_manager = FileManager(config)
        self.parser_manager = HtmlParser(self.exc)

        # 请求管理器（回调绑定反爬）
        self.req = RequestManager(
            config=config,
            on_verify_check=self.check_meet_fp,
            on_verify_handle=self.fp_do,
        )

        # 调度器（回调绑定业务逻辑）
        self.scheduler = PipelineScheduler(
            config=config,
            controller=self.controller,
            exc=self.exc,
            on_fetch_p1=self.get_p1_result,
            on_process_p2=self.get_p2_result,
        )

        # 快捷访问
        self.directory = self.file_manager.directory

        # 模式分发
        self._mode_handlers = {
            PipelineMode.MODE1: self.scheduler.mode1,
            PipelineMode.MODE2: self.scheduler.mode2,
            PipelineMode.MODE3: self.scheduler.mode3,
        }

        self.manager: Any = None
        self.build_other()

    # ---- 业务钩子 ----

    def build_other(self) -> None:
        self.manager = self.get_manager()

    @abstractmethod
    def get_manager(self) -> type:
        ...

    @property
    def session(self):
        return self.req.session

    @session.setter
    def session(self, value):
        self.req.session = value

    @property
    def stop_flag(self) -> bool:
        return self.controller.stopped

    @stop_flag.setter
    def stop_flag(self, value: bool) -> None:
        if value:
            self.controller.stop()

    @property
    def pause_flag(self) -> bool:
        return self.controller.paused

    @property
    def pause_event(self):
        return self.controller._pause_event

    # ---- 生命周期 ----

    async def init_components(self) -> None:
        await self.req.init()
        await self.file_manager.init()
        await self.parser_manager.init()

    def run(self, blocking: bool = True):
        res = self.exc.submit(self._run())
        if not blocking:
            return res
        try:
            res.result()
            loguru_logger.info("所有任务完成")
        except KeyboardInterrupt:
            loguru_logger.warning("用户中断")
            return None
        finally:
            self._stop()

    async def _run(self) -> None:
        self.scheduler.reset_p1_queue()
        await self.init_components()
        await self.before_run()
        handler = self._mode_handlers.get(self.config.mode)
        if handler is None:
            loguru_logger.error(f"未知模式: {self.config.mode}")
            return
        await handler()
        await self.after_run()

    @f_mark("运行前钩子")
    async def before_run(self) -> None:
        pass

    @f_mark("运行后钩子")
    async def after_run(self) -> None:
        pass

    # ---- 控制接口 ----

    def stop(self) -> None:
        self.controller.stop()

    def pause(self) -> None:
        self.controller.pause()
        loguru_logger.info("任务暂停")

    def resume(self) -> None:
        self.controller.resume()
        loguru_logger.info("任务继续")

    def close(self) -> None:
        self._stop()

    def _stop(self) -> None:
        if self.controller.mark_stopped() == "already":
            return
        loguru_logger.debug("正在停止...")
        timeout = self.config.session_close_timeout
        for component, name in [
            (self.req, "session"),
            (self.file_manager, "file manager"),
        ]:
            try:
                self.exc.submit(component.close(), mode="async", timeout=timeout).result(timeout=timeout)
            except Exception as exc:
                loguru_logger.error(f"{name} 关闭失败: {exc}")
        try:
            self.exc.shutdown()
        except Exception as exc:
            loguru_logger.error(f"runtime 关闭失败: {exc}")

    # ---- 抽象方法（业务层实现） ----

    @f_mark("反爬检测")
    @abstractmethod
    async def check_meet_fp(self, html: str) -> bool:
        return False

    @f_mark("反爬处理")
    @abstractmethod
    async def fp_do(self, session: Any, url: str, *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    async def get_p1_result(self, p1_id: str) -> P1Result:
        return P1Result(items=[P1Item(url=p1_id, name="")])

    @abstractmethod
    async def get_p2_result(self, p1_item: Any) -> P2Result | None:
        ...

    def html_parse_error(self, html: str) -> None:
        pass
