# 03-26-21-33-30
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from .task import TaskHandle


@dataclass(slots=True)
class TaskRegistryStats:
    """统一任务注册表统计信息。"""

    total: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0
    cancelled: int = 0

    def snapshot(self) -> dict[str, int]:
        """返回不可变统计快照。"""
        return {
            "total": self.total,
            "running": self.running,
            "success": self.success,
            "failed": self.failed,
            "cancelled": self.cancelled,
        }


class TaskRegistry:
    """负责任务 ID、活动任务、历史任务与状态统计。"""

    def __init__(self, history_limit: int = 1000) -> None:
        self.history_limit = history_limit

        self._lock = threading.RLock()
        self._task_seq = 0
        self._active_handles: dict[str, TaskHandle[Any]] = {}
        self._history_handles: OrderedDict[str, TaskHandle[Any]] = OrderedDict()
        self._stats = TaskRegistryStats()

    def _refresh_running_locked(self) -> None:
        """在持锁状态下刷新运行中数量。"""
        self._stats.running = len(self._active_handles)

    def allocate_task_id(self, task_id: str | None = None) -> str:
        """生成并校验任务 ID。"""
        with self._lock:
            if task_id is not None:
                if task_id in self._active_handles:
                    raise ValueError(f"任务ID已存在，禁止覆盖: {task_id}")
                return task_id

            while True:
                self._task_seq += 1
                generated = f"task-{self._task_seq}"
                if generated not in self._active_handles:
                    return generated

    def track(self, handle: TaskHandle[Any]) -> TaskHandle[Any]:
        """注册任务句柄，并在完成后转入历史。"""
        with self._lock:
            if handle.task_id in self._active_handles:
                raise ValueError(f"任务ID已存在，禁止覆盖: {handle.task_id}")

            self._history_handles.pop(handle.task_id, None)
            self._active_handles[handle.task_id] = handle
            self._stats.total += 1
            self._refresh_running_locked()

        handle.add_done_callback(self._on_handle_done)
        return handle

    def _on_handle_done(self, handle: TaskHandle[Any]) -> None:
        """任务完成时更新历史缓存与统计。"""
        with self._lock:
            active_handle = self._active_handles.get(handle.task_id)
            if active_handle is handle:
                self._active_handles.pop(handle.task_id, None)

            self._history_handles.pop(handle.task_id, None)
            self._history_handles[handle.task_id] = handle

            if handle.status == "done":
                self._stats.success += 1
            elif handle.status == "cancelled":
                self._stats.cancelled += 1
            else:
                self._stats.failed += 1

            self._refresh_running_locked()

            while len(self._history_handles) > self.history_limit:
                self._history_handles.popitem(last=False)

    def get_handle(self, task_id: str) -> TaskHandle[Any] | None:
        """按任务 ID 获取句柄。"""
        with self._lock:
            handle = self._active_handles.get(task_id)
            if handle is not None:
                return handle
            return self._history_handles.get(task_id)

    def get_status(self, task_id: str) -> str:
        """获取任务状态。"""
        handle = self.get_handle(task_id)
        if handle is None:
            return "not_found"
        return handle.status

    def get_all_task_ids(self) -> list[str]:
        """获取活动任务与最近历史任务 ID。"""
        with self._lock:
            active_ids = list(self._active_handles.keys())
            history_ids = [
                task_id
                for task_id in self._history_handles.keys()
                if task_id not in self._active_handles
            ]
        return active_ids + history_ids

    def cancel(self, task_id: str | None = None) -> bool | int:
        """取消指定任务；task_id 为空时取消全部活动任务。"""
        if task_id is not None:
            handle = self.get_handle(task_id)
            if handle is None:
                return False
            return handle.cancel()

        cancelled = 0
        with self._lock:
            handles = list(self._active_handles.values())

        for handle in handles:
            if handle.cancel():
                cancelled += 1

        return cancelled

    def wait_task(self, task_id: str, timeout: float | None = None) -> Any:
        """等待指定任务结束。"""
        handle = self.get_handle(task_id)
        if handle is None:
            raise ValueError(f"任务 {task_id} 不存在")
        return handle.result(timeout=timeout)

    def wait_all_tasks(self, timeout: float | None = None) -> list[Any]:
        """等待当前可见任务结束。"""
        with self._lock:
            handles = list(
                {
                    task_id: handle
                    for task_id, handle in [
                        *self._active_handles.items(),
                        *self._history_handles.items(),
                    ]
                }.values()
            )
        return [handle.result(timeout=timeout) for handle in handles]

    def get_stats(self) -> dict[str, int]:
        """返回统一统计快照。"""
        with self._lock:
            self._refresh_running_locked()
            return self._stats.snapshot()
