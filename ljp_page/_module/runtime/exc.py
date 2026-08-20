from __future__ import annotations

import asyncio
from typing import Any, Iterable, Literal

from ljp_page._core.base import Ljp_BaseClass_Logger
from .backends import Async,ThreadPool,BackendRouter
from .registry import TaskRegistry
from .task import Task, TaskSubmitConfig
from ljp_page._module.tools.bind import coerce_bind_task,BindTask
from ljp_page.logger import loguru_logger
__all__ = ["LJPExc","BindTask"]

class LJPExc:
    """统一调度入口，负责协调任务提交与后端路由。"""
    Mode_Type = Literal["auto", "sync", "async", "thread", "process"]
    _SEMAPHORE_DEFAULTS = ("sem1", "sem2")

    def __init__(
        self,
        log: Any = None,
        *,
        thread_pool: ThreadPool | None = None,
        asy: Async | None = None,
        thread_max_workers: int | None = None,
        thread_name_prefix: str = "LjpExcThreadPool",
        async_mode: int = 1,
        sem1_concurrent: int = 20,
        sem2_concurrent: int = 100,
        semaphore_limits: dict[str, int] | None = None,
        history_limit: int = 1000,
    ) -> None:
        self.log = log or loguru_logger
        self._registry = TaskRegistry(history_limit=history_limit)
        self._semaphores = self._build_named_semaphores(
            sem1_concurrent,
            sem2_concurrent,
            semaphore_limits,
        )
        self._router = BackendRouter(
            logger=loguru_logger,
            thread_pool=thread_pool,
            asy=asy,
            thread_max_workers=thread_max_workers,
            thread_name_prefix=thread_name_prefix,
            async_mode=async_mode,
        )

    @property
    def thread_pool(self) -> ThreadPool | None:
        """返回线程池实例。"""
        return self._router.thread_pool

    @thread_pool.setter
    def thread_pool(self, value: ThreadPool | None) -> None:
        """替换线程池实例。"""
        self._router.thread_pool = value

    @property
    def asy(self) -> Async | None:
        """返回异步运行时实例。"""
        return self._router.asy

    @asy.setter
    def asy(self, value: Async | None) -> None:
        """替换异步运行时实例。"""
        self._router.asy = value

    @property
    def process_pool(self) -> Any:
        """预留进程池实例。"""
        return self._router.process_pool

    @process_pool.setter
    def process_pool(self, value: Any) -> None:
        """预留进程池实例写入入口。"""
        self._router.process_pool = value

    @staticmethod
    def create_semaphore(num):
        return asyncio.Semaphore(max(1, num))

    @classmethod
    def _build_named_semaphores(
        cls,
        sem1_limit: int,
        sem2_limit: int,
        semaphore_limits: dict[str, int] | None = None,
    ) -> dict[str, asyncio.Semaphore]:
        limits = {cls._SEMAPHORE_DEFAULTS[0]: sem1_limit, cls._SEMAPHORE_DEFAULTS[1]: sem2_limit}
        if semaphore_limits:
            limits.update(semaphore_limits)
        return {name: cls.create_semaphore(limit) for name, limit in limits.items()}

    def set_semaphore(self, name: str, num: int) -> asyncio.Semaphore:
        semaphore = self.create_semaphore(num)
        self._semaphores[name] = semaphore
        return semaphore

    def get_semaphore(self, name: str = "sem1") -> asyncio.Semaphore:
        if name not in self._semaphores:
            raise KeyError(f"未定义的并发池: {name}")
        return self._semaphores[name]

    def _resolve_semaphores(
        self,
        semaphore: str | asyncio.Semaphore | None = None,
        semaphores: Iterable[str | asyncio.Semaphore] | None = None,
        default_name: str | None = None,
    ) -> tuple[tuple[asyncio.Semaphore, ...], tuple[str, ...]]:
        result: list[asyncio.Semaphore] = []
        names: list[str] = []
        if semaphore is None and semaphores is None and default_name is not None:
            semaphore = default_name
        if semaphore is not None:
            sem, name = self._resolve_one_semaphore(semaphore)
            result.append(sem)
            names.append(name)
        if semaphores is not None:
            for item in semaphores:
                sem, name = self._resolve_one_semaphore(item)
                result.append(sem)
                names.append(name)
        return tuple(result), tuple(names)

    def _resolve_one_semaphore(
        self,
        semaphore: str | asyncio.Semaphore,
    ) -> tuple[asyncio.Semaphore, str]:
        if isinstance(semaphore, str):
            return self.get_semaphore(semaphore), semaphore
        return semaphore, "custom"

    def bind(self, target: Any, *args: Any, **kwargs: Any) -> BindTask:
        """绑定目标任务参数，避免与调度参数冲突。"""
        return coerce_bind_task(target, *args, **kwargs)

    def submit(
        self,
        target: Any,
        *args: Any,
        mode: LJPExc.Mode_Type = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
        semaphore: str | asyncio.Semaphore | None = None,
        semaphores: Iterable[str | asyncio.Semaphore] | None = None,
        **kwargs: Any,
    ) -> Task[Any]:
        """统一提交单任务，始终返回 TaskHandle。"""
        resolved_semaphores, semaphore_names = self._resolve_semaphores(
            semaphore,
            semaphores,
            default_name="sem1",
        )
        config = self._build_submit_config(
            mode=mode,
            task_id=task_id,
            timeout=timeout,
            callback=callback,
            semaphores=resolved_semaphores,
            semaphore_names=semaphore_names,
        )
        bound_task = coerce_bind_task(target, *args, **kwargs)
        return self._submit_bind_task(bound_task, config)

    def submit_inside(
        self,
        target: Any,
        *args: Any,
        mode: LJPExc.Mode_Type = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
        semaphore: str | asyncio.Semaphore | None = None,
        semaphores: Iterable[str | asyncio.Semaphore] | None = None,
        **kwargs: Any,
    ) -> Task[Any]:
        """按 inside 语义提交任务；默认使用 sem2 并发池。"""
        resolved_semaphores, semaphore_names = self._resolve_semaphores(
            semaphore,
            semaphores,
            default_name="sem2",
        )
        return self._submit_bind_task(
            coerce_bind_task(target, *args, **kwargs),
            self._build_submit_config(
                mode=mode,
                task_id=task_id,
                timeout=timeout,
                callback=callback,
                semaphores=resolved_semaphores,
                semaphore_names=semaphore_names,
            )
        )

    def submit_many(
        self,
        tasks: Iterable[Any],
        *,
        mode: LJPExc.Mode_Type = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
        semaphore: str | asyncio.Semaphore | None = None,
        semaphores: Iterable[str | asyncio.Semaphore] | None = None,
    ) -> list[Task[Any]]:
        """批量提交任务，返回统一句柄列表。"""
        resolved_semaphores, semaphore_names = self._resolve_semaphores(
            semaphore,
            semaphores,
            default_name="sem1",
        )
        return self._submit_many_bind_task(
            tasks,
            self._build_submit_config(
                mode=mode,
                task_id=task_id,
                timeout=timeout,
                callback=callback,
                allocate_task_id=False,
                semaphores=resolved_semaphores,
                semaphore_names=semaphore_names,
            ),
        )

    def submit_many_inside(
        self,
        tasks: Iterable[Any],
        *,
        mode: LJPExc.Mode_Type = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
        semaphore: str | asyncio.Semaphore | None = None,
        semaphores: Iterable[str | asyncio.Semaphore] | None = None,
    ) -> list[Task[Any]]:
        """按 inside 语义批量提交任务；默认使用 sem2 并发池。"""
        resolved_semaphores, semaphore_names = self._resolve_semaphores(
            semaphore,
            semaphores,
            default_name="sem2",
        )
        return self._submit_many_bind_task(
            tasks,
            self._build_submit_config(
                mode=mode,
                task_id=task_id,
                timeout=timeout,
                callback=callback,
                allocate_task_id=False,
                semaphores=resolved_semaphores,
                semaphore_names=semaphore_names,
            ),
        )

    def _submit_bind_task(
        self,
        bind_task: BindTask,
        config: TaskSubmitConfig,
    ) -> Task[Any]:
        """统一处理单个 BoundTask 的后端路由、句柄封装与注册。"""
        resolved_mode, backend = self._router.select_backend(bind_task, config.mode)
        raw_future = backend.submit(bind_task, config)

        handle = Task(
            raw_future,
            task_id=config.task_id or "",
            mode_requested=config.mode,
            mode_resolved=resolved_mode,
            backend_name=backend.backend_name,
            semaphore_names=config.semaphore_names,
            bound_task=bind_task,
        )
        self._registry.track(handle)

        if config.callback is not None:
            handle.add_done_callback(config.callback)

        return handle

    def _submit_many_bind_task(
        self,
        tasks: Iterable[Any],
        config: TaskSubmitConfig,
    ) -> list[Task[Any]]:
        """按统一配置批量提交任务。"""
        handles: list[Task[Any]] = []
        for index, item in enumerate(tasks, start=1):
            child_config = self._build_child_config(config, index)
            bind_task = self._coerce_task(item)
            handles.append(
                self._submit_bind_task(
                    bind_task,
                    child_config,
                )
            )
        return handles

    def _coerce_task(self, item: Any) -> BindTask:
        """标准化 submit_many 的批量输入项。"""
        if not isinstance(item, tuple):
            return coerce_bind_task(item)

        if len(item) != 3:
            raise ValueError("submit_many 的元组任务必须是 (target, args, kwargs)")

        target, item_args, item_kwargs = item
        if not isinstance(item_args, tuple) or not isinstance(item_kwargs, dict):
            raise TypeError("submit_many 的元组任务格式必须是 (target, tuple, dict)")

        return coerce_bind_task(target, *item_args, **item_kwargs)

    def _build_child_config(self, config: TaskSubmitConfig, index: int) -> TaskSubmitConfig:
        """为子任务派生任务 ID，未指定父 ID 时自动分配唯一 ID。"""
        child_task_id = self._build_child_task_id(config.task_id, index)
        if child_task_id is None:
            child_task_id = self._registry.allocate_task_id()
        return config.with_task_id(child_task_id)

    @staticmethod
    def _build_child_task_id(parent_task_id: str | None, index: int) -> str | None:
        """为批量提交生成子任务 ID。"""
        if parent_task_id is None:
            return None
        return f"{parent_task_id}:{index}"

    def _build_submit_config(
        self,
        *,
        mode: str,
        task_id: str | None = None,
        timeout: float | None = None,
        callback: Any = None,
        allocate_task_id: bool = True,
        semaphores: tuple[asyncio.Semaphore, ...] = (),
        semaphore_names: tuple[str, ...] = (),
    ) -> TaskSubmitConfig:
        """构造统一任务配置。"""
        self._router.validate_mode(mode)
        if callback is not None and not callable(callback):
            raise TypeError("callback 必须是可调用对象")

        resolved_task_id = self._registry.allocate_task_id(task_id) if allocate_task_id else task_id
        return TaskSubmitConfig(
            mode=mode,
            task_id=resolved_task_id,
            timeout=timeout,
            callback=callback,
            semaphores=semaphores,
            semaphore_names=semaphore_names,
        )


    def cancel(self, task_id: str | None = None) -> bool | int:
        """取消指定任务；task_id 为空时取消全部活动任务。"""
        return self._registry.cancel(task_id)

    def cancel_all(self) -> int:
        """取消全部活动任务。"""
        cancelled = self._registry.cancel()
        return int(cancelled)

    def get_task_handle(self, task_id: str) -> Task[Any] | None:
        """按任务 ID 获取句柄。"""
        return self._registry.get_handle(task_id)

    def get_task_status(self, task_id: str) -> str:
        """返回任务状态文本。"""
        return self._registry.get_status(task_id)

    def get_all_task_ids(self) -> list[str]:
        """返回活动任务和最近历史任务 ID。"""
        return self._registry.get_all_task_ids()

    def wait_task(self, task_id: str, timeout: float | None = None) -> Any:
        """等待指定任务结束。"""
        return self._registry.wait_task(task_id, timeout=timeout)

    def wait_all_tasks(self, timeout: float | None = None) -> list[Any]:
        """等待当前可见任务结束。"""
        return self._registry.wait_all_tasks(timeout=timeout)

    def get_stats(self) -> dict[str, int]:
        """返回统一任务统计快照。"""
        return self._registry.get_stats()

    def shutdown(
        self,
        wait: bool = True,
        cancel_futures: bool = False,
        async_timeout: float = 5.0,
    ) -> None:
        """关闭统一调度器。"""
        if cancel_futures:
            self.cancel_all()

        self._router.shutdown(
            wait=wait,
            cancel_futures=cancel_futures,
            async_timeout=async_timeout,
        )
        self.log.info('统一调度器关闭')


    def __enter__(self) -> "LJPExc":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()
