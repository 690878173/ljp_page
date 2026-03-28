# 03-26-21-33-30
from __future__ import annotations

from typing import Any, Iterable

from ljp_page.core.base.base_class import Ljp_BaseClass
from ..ljp_async import Async
from ..threadpool import ThreadPool
from .backends import BackendRouter
from .registry import TaskRegistry
from .task import BoundTask, TaskHandle, TaskSubmitConfig, coerce_bound_task


class LJPExc(Ljp_BaseClass):
    """统一调度入口，负责协调任务提交与后端路由。"""

    def __init__(
        self,
        logger: Any = None,
        *,
        thread_pool: ThreadPool | None = None,
        asy: Async | None = None,
        thread_max_workers: int | None = None,
        thread_name_prefix: str = "LjpExcThreadPool",
        async_mode: int = 1,
        async_outer_concurrent: int = 20,
        async_inner_concurrent: int = 100,
        history_limit: int = 1000,
    ) -> None:
        super().__init__(logger=logger)
        self._registry = TaskRegistry(history_limit=history_limit)
        self._router = BackendRouter(
            logger=logger,
            thread_pool=thread_pool,
            asy=asy,
            thread_max_workers=thread_max_workers,
            thread_name_prefix=thread_name_prefix,
            async_mode=async_mode,
            async_outer_concurrent=async_outer_concurrent,
            async_inner_concurrent=async_inner_concurrent,
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

    def bind(self, target: Any, *args: Any, **kwargs: Any) -> BoundTask:
        """绑定目标任务参数，避免与调度参数冲突。"""
        return coerce_bound_task(target, *args, **kwargs)

    def submit(
        self,
        target: Any,
        *args: Any,
        mode: str = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> TaskHandle[Any]:
        """统一提交单任务，始终返回 TaskHandle。"""
        config = self._build_submit_config(
            mode=mode,
            layer="outer",
            task_id=task_id,
            timeout=timeout,
            callback=callback,
        )
        bound_task = coerce_bound_task(target, *args, **kwargs)
        return self._submit_bound_task(bound_task, config, callback=config.callback)

    def submit_inside(
        self,
        target: Any,
        *args: Any,
        mode: str = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> TaskHandle[Any]:
        """以内层并发语义提交任务。"""
        return self._submit_bound_task(
            coerce_bound_task(target, *args, **kwargs),
            self._build_submit_config(
                mode=mode,
                layer="inner",
                task_id=task_id,
                timeout=timeout,
                callback=callback,
            ),
            callback=callback,
        )

    def submit_many(
        self,
        tasks: Iterable[Any],
        *,
        mode: str = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
    ) -> list[TaskHandle[Any]]:
        """批量提交任务，返回统一句柄列表。"""
        return self._submit_many_with_config(
            tasks,
            self._build_submit_config(
                mode=mode,
                layer="outer",
                task_id=task_id,
                timeout=timeout,
                callback=callback,
                allocate_task_id=False,
            ),
        )

    def submit_many_inside(
        self,
        tasks: Iterable[Any],
        *,
        mode: str = "auto",
        task_id: str | None = None,
        callback: Any = None,
        timeout: float | None = None,
    ) -> list[TaskHandle[Any]]:
        """以内层并发语义批量提交任务。"""
        return self._submit_many_with_config(
            tasks,
            self._build_submit_config(
                mode=mode,
                layer="inner",
                task_id=task_id,
                timeout=timeout,
                callback=callback,
                allocate_task_id=False,
            ),
        )

    def cancel(self, task_id: str | None = None) -> bool | int:
        """取消指定任务；task_id 为空时取消全部活动任务。"""
        return self._registry.cancel(task_id)

    def cancel_all(self) -> int:
        """取消全部活动任务。"""
        cancelled = self._registry.cancel()
        return int(cancelled)

    def get_task_handle(self, task_id: str) -> TaskHandle[Any] | None:
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

    def __enter__(self) -> "LJPExc":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def _submit_bound_task(
        self,
        bound_task: BoundTask,
        config: TaskSubmitConfig,
        *,
        callback: Any = None,
    ) -> TaskHandle[Any]:
        """统一处理单个 BoundTask 的后端路由、句柄封装与注册。"""
        resolved_mode, backend = self._router.select_backend(bound_task, config.mode)
        raw_future = backend.submit(bound_task, config)

        handle = TaskHandle(
            raw_future,
            task_id=config.task_id or "",
            mode_requested=config.mode,
            mode_resolved=resolved_mode,
            layer=config.layer,
            backend_name=backend.backend_name,
            bound_task=bound_task,
        )
        self._registry.track(handle)

        if callback is not None:
            handle.add_done_callback(callback)

        return handle

    def _submit_many_with_config(
        self,
        tasks: Iterable[Any],
        config: TaskSubmitConfig,
    ) -> list[TaskHandle[Any]]:
        """按统一配置批量提交任务。"""
        handles: list[TaskHandle[Any]] = []
        for index, item in enumerate(tasks, start=1):
            child_config = self._build_child_config(config, index)
            bound_task = self._coerce_batch_item(item)
            handles.append(
                self._submit_bound_task(
                    bound_task,
                    child_config,
                    callback=config.callback,
                )
            )
        return handles

    def _coerce_batch_item(self, item: Any) -> BoundTask:
        """标准化 submit_many 的批量输入项。"""
        if not isinstance(item, tuple):
            return coerce_bound_task(item)

        if len(item) != 3:
            raise ValueError("submit_many 的元组任务必须是 (target, args, kwargs)")

        target, item_args, item_kwargs = item
        if not isinstance(item_args, tuple) or not isinstance(item_kwargs, dict):
            raise TypeError("submit_many 的元组任务格式必须是 (target, tuple, dict)")

        return coerce_bound_task(target, *item_args, **item_kwargs)

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
        layer: str,
        task_id: str | None = None,
        timeout: float | None = None,
        callback: Any = None,
        allocate_task_id: bool = True,
    ) -> TaskSubmitConfig:
        """构造统一任务配置。"""
        self._router.validate_mode(mode)
        if layer not in {"outer", "inner"}:
            raise ValueError(f"不支持的 layer: {layer}")
        if callback is not None and not callable(callback):
            raise TypeError("callback 必须是可调用对象")

        resolved_task_id = self._registry.allocate_task_id(task_id) if allocate_task_id else task_id
        return TaskSubmitConfig(
            mode=mode,
            layer=layer,
            task_id=resolved_task_id,
            timeout=timeout,
            callback=callback,
        )
