"""生命周期控制器 —— 管理暂停、恢复、停止信号。"""

from __future__ import annotations

import asyncio
import threading


class LifecycleController:
    """统一的暂停 / 恢复 / 停止信号管理。

    使用方式:
        controller = LifecycleController()
        await controller.wait_if_paused()   # 阻塞直到恢复或停止
        controller.pause()                  # 暂停
        controller.resume()                 # 恢复
        controller.stop()                   # 停止
    """

    def __init__(self) -> None:
        self._stop_flag = False
        self._pause_flag = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._stop_lock = threading.RLock()
        self._stopped = False

    # ---- 只读属性 ----

    @property
    def stopped(self) -> bool:
        return self._stop_flag

    @property
    def paused(self) -> bool:
        return self._pause_flag

    # ---- 协程端接口 ----

    async def wait_if_paused(self) -> None:
        """阻塞当前协程，直到恢复或停止。"""
        await self._pause_event.wait()

    # ---- 控制端接口 ----

    def stop(self) -> None:
        """发送停止信号并解除所有等待。"""
        self._stop_flag = True
        self._pause_event.set()

    def pause(self) -> None:
        """进入暂停状态。"""
        self._pause_flag = True
        self._pause_event.clear()

    def resume(self) -> None:
        """退出暂停状态。"""
        self._pause_flag = False
        self._pause_event.set()

    def mark_stopped(self) -> str | None:
        """标记已停止（幂等），返回 None 表示首次标记，返回 'already' 表示已标记过。"""
        with self._stop_lock:
            if self._stopped:
                return "already"
            self._stopped = True
            return None

    @property
    def is_stopped(self) -> bool:
        return self._stopped
