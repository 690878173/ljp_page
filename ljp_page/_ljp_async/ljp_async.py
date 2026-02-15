import asyncio
import threading
from typing import Optional, Callable, Any, Coroutine, List, Dict, Tuple, Union, Awaitable
from concurrent.futures import Future
from .._ljp_coro.base_class import Ljp_BaseClass
from .._ljp_coro.exceptions import No


class _AsyncBase(Ljp_BaseClass):
    """异步管理器基类

    提供事件循环管理、并发控制、任务追踪等底层实现
    """

    def __init__(self, mode: int = 1, max_concurrent: int = 20, max_inner_concurrent: int = 100, logger=None):
        super().__init__()
        self.mode = mode
        self.max_concurrent = max_concurrent
        self.max_inner_concurrent = max_inner_concurrent
        self.logger = logger

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.inner_semaphore: Optional[asyncio.Semaphore] = None
        self._loop_started = threading.Event()

        self._tasks: Dict[str, Future] = {}
        self._task_lock = threading.Lock()
        self._task_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cancelled': 0
        }
        self._stats_lock = threading.Lock()

        self._start_loop()

    def _run_loop(self):
        """运行事件循环"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.semaphore = asyncio.Semaphore(self.max_concurrent)
            self.inner_semaphore = asyncio.Semaphore(self.max_inner_concurrent)
            self._loop_started.set()
            self.info(f"事件循环已启动，最大并发: {self.max_concurrent}")
            self.loop.run_forever()
        except Exception as e:
            self.error(f"事件循环异常: {str(e)}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
                self.info("事件循环已关闭")

    def _start_loop(self):
        """启动事件循环线程"""
        if self.loop_thread and self.loop_thread.is_alive():
            return

        self._loop_started.clear()
        self.loop_thread = threading.Thread(
            target=self._run_loop,
            daemon=self.mode == 0,
            name="Async-Loop-Thread"
        )
        self.loop_thread.start()

        if not self._loop_started.wait(timeout=5):
            raise RuntimeError("事件循环启动超时")

    def start(self):
        """启动事件循环"""
        self._start_loop()

    def stop(self, timeout: float = 5.0):
        """停止事件循环"""
        if not self.is_running():
            return

        self.info("正在停止事件循环...")

        cancelled_count = self._cancel_all_tasks()
        if cancelled_count > 0:
            self.info(f"已取消 {cancelled_count} 个未完成任务")

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)  # ignore

        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=timeout)
            if self.loop_thread.is_alive():
                self.warning("事件循环线程停止超时")

    def is_running(self) -> bool:
        """检查事件循环是否运行中"""
        return self.loop is not None and self.loop.is_running()

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """获取事件循环"""
        if not self.loop or self.loop.is_closed():
            self.start()
        return self.loop

    async def _wrapped_outer_coro(self, coro: Coroutine) -> Any:
        """应用外层并发控制的协程包装"""
        async with self.semaphore:
            return await coro

    async def _wrapped_inner_coro(self, coro: Coroutine) -> Any:
        """应用内层并发控制的协程包装"""
        async with self.inner_semaphore:
            return await coro

    def _register_task(self, task_id: str, future: Future) -> None:
        """注册任务"""
        with self._task_lock:
            self._tasks[task_id] = future
        with self._stats_lock:
            self._task_stats['total'] += 1

    def _update_stats(self, status: str) -> None:
        """更新统计信息"""
        with self._stats_lock:
            if status in self._task_stats:
                self._task_stats[status] += 1

    def _cancel_all_tasks(self) -> int:
        """取消所有任务"""
        cancelled_count = 0
        with self._task_lock:
            task_ids = list(self._tasks.keys())

        for task_id in task_ids:
            if self._cancel_task(task_id):
                cancelled_count += 1

        return cancelled_count

    def _cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        with self._task_lock:
            future = self._tasks.get(task_id)

        if future and not future.done():
            cancelled = future.cancel()
            if cancelled:
                self.info(f"任务 {task_id} 已取消")
                self._update_stats('cancelled')
            return cancelled
        return False


class Async(_AsyncBase):
    """异步任务管理器

    提供简洁高效的异步任务执行接口

    Args:
        mode: 线程模式，0为守护线程，1为非守护线程
        max_concurrent: 最大并发数
        max_inner_concurrent: 内层最大并发数
        logger: 日志记录器
    """

    def submit(self,
               coro: Coroutine,
               callback: Optional[Callable] = None,
               timeout: Optional[float] = None,
               task_id: Optional[str] = None,
               return_exceptions: bool = False,
               await_result: bool = False) -> Union[Future, Any]:
        """提交单个协程任务

        Args:
            coro: 要执行的协程
            callback: 任务完成后的回调函数
            timeout: 超时时间（秒）
            task_id: 任务ID
            return_exceptions: 是否返回异常而非抛出
            await_result: 是否等待结果返回

        Returns:
            如果await_result为True，返回任务结果，否则返回Future对象
        """
        if timeout:
            coro = asyncio.wait_for(coro, timeout=timeout)

        future = asyncio.run_coroutine_threadsafe(
            self._wrapped_outer_coro(coro),
            self.loop
        )

        task_id = task_id or str(id(future))
        self._register_task(task_id, future)

        if callback:
            self._attach_callback(future, task_id, callback, return_exceptions)

        if await_result:
            return self._await_result(future, task_id)
        return future

    def submit_s(self,
                 async_ls: List[Union[Coroutine, Tuple[Coroutine, Optional[Callable]]]],
                 timeout: Optional[float] = None,
                 return_exceptions: bool = False,
                 await_result: bool = False) -> Union[List[Future], List[Any]]:
        """批量提交协程任务

        Args:
            async_ls: 协程列表或元组列表（元组格式：(coro, callback)）
            timeout: 超时时间（秒）
            return_exceptions: 是否返回异常而非抛出
            await_result: 是否等待所有结果返回

        Returns:
            如果await_result为True，返回结果列表，否则返回Future对象列表
        """
        futures = []
        for item in async_ls:
            if isinstance(item, tuple) and len(item) == 2:
                coro, callback = item
            else:
                coro = item
                callback = None

            future = self.submit(
                coro,
                callback=callback,
                timeout=timeout,
                return_exceptions=return_exceptions
            )
            futures.append(future)

        if await_result:
            return [f.result() for f in futures]
        return futures

    async def submit_inside(self, coro: Coroutine) -> Any:
        """在协程内部提交单个子任务（使用内层并发控制）

        Args:
            coro: 要执行的协程

        Returns:
            协程执行结果
        """
        async with self.inner_semaphore:
            return await coro

    async def submit_inside_s(self, coros: List[Coroutine], return_exceptions: bool = False) -> List[Any]:
        """在协程内部批量提交子任务（使用内层并发控制）

        Args:
            coros: 协程列表
            return_exceptions: 是否返回异常而非抛出

        Returns:
            结果列表
        """
        try:
            wrapped_coros = [self.submit_inside(coro) for coro in coros]
            results = await asyncio.gather(*wrapped_coros, return_exceptions=return_exceptions)
        except Exception as e:
            self.error(f"批量子任务执行失败: {e}")
            raise No('批量子任务执行失败', f=self.submit_inside_s, e=e)
        return results

    async def submit_async(self, coro: Coroutine) -> Awaitable[Any]:
        """在协程内部提交任务并返回可等待对象

        Args:
            coro: 要执行的协程

        Returns:
            可等待对象
        """
        future = asyncio.run_coroutine_threadsafe(self._wrapped_outer_coro(coro), self.loop)
        return asyncio.wrap_future(future)

    def cancel(self, task_id: Optional[str] = None) -> Union[bool, int]:
        """取消任务

        Args:
            task_id: 任务ID，如果为None则取消所有任务

        Returns:
            如果指定task_id，返回是否成功取消
            如果task_id为None，返回取消的任务数量
        """
        if task_id:
            return self._cancel_task(task_id)
        return self._cancel_all_tasks()

    def get_stats(self) -> Dict[str, int]:
        """获取任务统计信息

        Returns:
            统计字典：total, success, failed, cancelled, running
        """
        stats = self._task_stats.copy()
        with self._task_lock:
            stats['running'] = len([f for f in self._tasks.values() if not f.done()])
        return stats

    def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态：'running', 'done', 'cancelled', 'not_found'
        """
        with self._task_lock:
            future = self._tasks.get(task_id)

        if not future:
            return 'not_found'
        if future.cancelled():
            return 'cancelled'
        elif future.done():
            return 'done'
        else:
            return 'running'

    def get_all_task_ids(self) -> List[str]:
        """获取所有任务ID

        Returns:
            任务ID列表
        """
        with self._task_lock:
            return list(self._tasks.keys())

    def wait_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待指定任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            任务结果
        """
        with self._task_lock:
            future = self._tasks.get(task_id)

        if not future:
            raise ValueError(f"任务 {task_id} 不存在")

        return future.result(timeout=timeout)

    def wait_all_tasks(self, timeout: Optional[float] = None) -> List[Any]:
        """等待所有任务完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            结果列表
        """
        with self._task_lock:
            futures = list(self._tasks.values())

        return [f.result(timeout=timeout) for f in futures]

    def _attach_callback(self, future: Future, task_id: str,
                         callback: Callable, return_exceptions: bool) -> None:
        """绑定任务回调"""

        def wrap_callback(fut: Future):
            try:
                result = fut.result() if not return_exceptions else fut.exception() or fut.result()
                callback(result)

                if fut.exception():
                    self._update_stats('failed')
                elif fut.cancelled():
                    self._update_stats('cancelled')
                else:
                    self._update_stats('success')
            except Exception as e:
                if return_exceptions:
                    callback(e)
                else:
                    self.error(f"任务回调出错: {e}")
                    self._update_stats('failed')
            finally:
                with self._task_lock:
                    self._tasks.pop(task_id, None)

        future.add_done_callback(wrap_callback)

    def _await_result(self, future: Future, task_id: str) -> Any:
        """等待任务结果"""
        try:
            result = future.result()
            self._update_stats('success')
            return result
        except Exception as e:
            self.error(f"任务执行失败: {e}")
            self._update_stats('failed')
            raise
        finally:
            with self._task_lock:
                self._tasks.pop(task_id, None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
