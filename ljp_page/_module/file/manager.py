import asyncio
import datetime
import threading
import queue
import time
import atexit
from pathlib import Path
from typing import Any, Optional, Tuple, TYPE_CHECKING
from ljp_page.logger import loguru_logger

from ljp_page._module.file.model import SyncFile, AioFile
from ljp_page._core.utils.double_linked_list import ListNode, DoubleLinkedList


class SyncFileWriter:
    def __init__(self, max_queue_size: int = 8000, max_open_files=64, idle_timeout: float = 30.0):
        self._queue: queue.Queue[Optional[tuple[str, str]]] = queue.Queue(maxsize=max_queue_size)
        self._file_map: dict[str, tuple[SyncFile, ListNode[str]]] = {}
        self._lru_list = DoubleLinkedList[str]()
        self._thread: Optional[threading.Thread] = None
        self._running = False

        # NOTE LRU淘汰机制，避免长时间持有文件对象
        self.max_open_files = max_open_files
        self.idle_timeout = idle_timeout

        atexit.register(self._atexit_cleanup)

    def _atexit_cleanup(self):
        if self._running:
            loguru_logger.warning("FileWriteThread:检测到未手动stop，atexit兜底执行关闭，建议业务主动调用stop()")
            self.stop(join=True)

    def start(self):
        """启动后台写线程"""
        if self._running:
            loguru_logger.warning("FileWriteThread 已经处于运行状态，无需重复启动")
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        loguru_logger.info("FileWriteThread 写线程已启动")

    def submit(self, path: Path | str, data: str):
        """业务线程调用：提交写入任务，线程安全"""
        p = Path(path).expanduser().resolve()
        abs_path = str(p)
        try:
            # put会阻塞，如果队列满
            self._queue.put((abs_path, data))
        except Exception as e:
            loguru_logger.error(f"提交写任务失败 path={abs_path} {e}")
            raise

    def stop(self, join: bool = True):
        """优雅关闭：发送哨兵，等待消费完成，关闭所有文件"""
        if not self._running:
            loguru_logger.warning("FileWriteThread 未运行，无需停止")
            return
        loguru_logger.info("开始停止 FileWriteThread，等待队列任务处理完毕")
        self._running = False
        # 放入哨兵None
        self._queue.put(None)
        if join and self._thread is not None:
            self._thread.join()
            loguru_logger.info("FileWriteThread 线程已退出")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(join=True)

    def _try_evict(self):
        now = time.time()
        if len(self._file_map) <= self.max_open_files:
            return
        need_evict = len(self._file_map) - self.max_open_files

        evicted = 0
        while evicted < need_evict:
            tail_node = self._lru_list.pop_back()
            if tail_node is None:
                break
            path_key = tail_node.data
            f, _ = self._file_map[path_key]
            idle = now - f.last_write_ts
            if idle >= self.idle_timeout:
                # 满足超时，真正淘汰
                try:
                    f.close()
                    del self._file_map[path_key]
                    loguru_logger.debug(f"LRU淘汰 path={path_key}")
                except Exception as e:
                    loguru_logger.error(f"LRU关闭失败 {path_key} {e}")
                evicted += 1
            else:
                # 这个还没超时，放回去，终止本轮淘汰
                self._lru_list.push_front(tail_node)
                break

    def _worker_loop(self):
        """仅在写线程内部运行"""
        loguru_logger.debug("FileWriteThread worker 循环开始")
        while True:
            item = self._queue.get()
            try:
                # 收到哨兵，退出循环
                if item is None:
                    loguru_logger.debug("FileWriteThread 收到停止哨兵，准备退出")
                    break
                abs_path_str, content = item
                # 没有就新建SyncFile
                if abs_path_str not in self._file_map:
                    loguru_logger.debug(f"新建文件实例 path={abs_path_str}")
                    f = SyncFile(abs_path_str)
                    node = ListNode(abs_path_str)
                    self._lru_list.push_front(node)
                    self._file_map[abs_path_str] = (f, node)
                f, node = self._file_map[abs_path_str]
                f.write(content)
                self._lru_list.push_front(node)
                self._try_evict()  # 写完执行LRU淘汰
            except OSError as e:
                abs_path_str = item[0] if item else ""
                loguru_logger.error(f"文件写入IO异常 path={abs_path_str} {e}")
            except Exception as e:
                loguru_logger.error(f"写线程处理任务异常 item={item} {e}")
            finally:
                self._queue.task_done()

        # 退出前：关闭全部打开文件
        loguru_logger.debug(f"关闭全部打开文件，打开文件数量:{len(self._file_map)}")
        for file_path, (f, _node) in list(self._file_map.items()):
            try:
                f.close()
            except Exception as e:
                loguru_logger.error(f"关闭文件失败 path={file_path} {e}")
        self._file_map.clear()
        self._lru_list.clear()
        loguru_logger.debug("FileWriteThread worker 循环结束")

# NOTE start启动后使用subnit提交路径与内容，自动写入，完成后提交None然后等待返回值future对象，一般提交不需要
class AsyncFileWriter:
    def __init__(
        self,
        max_queue_size: int = 10000,
        max_open_files: int = 64,
        idle_timeout: float = 30.0
    ):
        self._queue: asyncio.Queue[Optional[Tuple[str, Optional[str], asyncio.Future]]] = asyncio.Queue(maxsize=max_queue_size)
        self._file_map: dict[str, tuple[AioFile, ListNode[str]]] = {}
        self._lru_list = DoubleLinkedList[str]()
        self._task: Optional[asyncio.Task] = None
        self._running = False

        self.max_open_files = max_open_files
        self.idle_timeout = idle_timeout

    def start(self):
        if self._running:
            loguru_logger.warning("AsyncFileWriter 已经运行，无需重复启动")
            return
        self._running = True
        self._task = asyncio.create_task(self._worker_loop())
        loguru_logger.info("AsyncFileWriter worker协程已启动")

    async def submit(self, path: Path | str, data: Optional[str]) -> asyncio.Future:
        """
        提交任务
        :param path: 文件路径
        :param data: 字符串为写入内容；None代表关闭该文件
        :return: Future，可await等待任务完成；普通写入可丢弃，关闭建议await
        """
        if not self._running:
            raise RuntimeError("AsyncFileWriter 未start")
        fut = asyncio.Future()
        p = Path(path).expanduser().resolve()
        abs_path = str(p)
        try:
            await self._queue.put((abs_path, data, fut))
        except Exception as e:
            loguru_logger.error(f"提交写任务失败 path={abs_path} {e}")
            raise
        return fut

    async def stop(self, join: bool = True):
        if not self._running:
            loguru_logger.warning("AsyncFileWriter 未运行，无需停止")
            return
        loguru_logger.info("开始停止 AsyncFileWriter，等待队列任务处理完毕")
        self._running = False
        await self._queue.put(None)
        if join and self._task is not None:
            await self._task
            loguru_logger.info("AsyncFileWriter worker协程已退出")

    def _try_evict(self) -> list[Tuple[str, AioFile]]:
        evict_list: list[Tuple[str, AioFile]] = []
        now = time.time()
        current_size = len(self._file_map)
        if current_size <= self.max_open_files:
            return evict_list
        need_evict = current_size - self.max_open_files

        evicted = 0
        while evicted < need_evict:
            tail_node = self._lru_list.pop_back()
            if tail_node is None:
                break
            path_key = tail_node.data
            if path_key not in self._file_map:
                continue
            f, _ = self._file_map[path_key]
            idle = now - f.last_write_ts
            if idle >= self.idle_timeout:
                evict_list.append((path_key, f))
                evicted += 1
            else:
                self._lru_list.push_front(tail_node)
                break
        return evict_list

    async def _worker_loop(self):
        loguru_logger.debug("AsyncFileWriter worker 协程启动")
        while True:
            item = await self._queue.get()
            fut: Optional[asyncio.Future] = None
            try:
                if item is None:
                    loguru_logger.debug("AsyncFileWriter 收到哨兵，准备退出")
                    break
                abs_path_str, content, fut = item

                if abs_path_str not in self._file_map:
                    loguru_logger.debug(f"新建AioFile实例 path={abs_path_str}")
                    f = AioFile(abs_path_str)
                    node = ListNode(abs_path_str)
                    self._lru_list.push_front(node)
                    self._file_map[abs_path_str] = (f, node)

                f, node = self._file_map[abs_path_str]

                if content is None:
                    # 关闭任务
                    await f.close()
                    del self._file_map[abs_path_str]
                    self._lru_list.remove(node)
                    loguru_logger.debug(f"AsyncFileWriter 主动关闭 path={abs_path_str}")
                else:
                    await f.write(content)
                    self._lru_list.push_front(node)

                # LRU淘汰
                evict_list = self._try_evict()
                for path_key, f_evict in evict_list:
                    try:
                        await f_evict.close()
                        del self._file_map[path_key]
                        loguru_logger.debug(f"AsyncFileWriter LRU淘汰 path={path_key}")
                    except Exception as e:
                        loguru_logger.error(f"AsyncFileWriter LRU关闭失败 {path_key} {e}")

                if fut is not None and not fut.done():
                    fut.set_result(None)

            except OSError as e:
                if fut is not None and not fut.done():
                    fut.set_exception(e)
                abs_path_str = item[0] if (item and isinstance(item,tuple)) else ""
                loguru_logger.error(f"异步写入IO异常 path={abs_path_str} {e}")
            except Exception as e:
                if fut is not None and not fut.done():
                    fut.set_exception(e)
                loguru_logger.error(f"AsyncFileWriter处理任务异常 item={item} {e}")
            finally:
                self._queue.task_done()

        loguru_logger.debug(f"AsyncFileWriter 关闭全部文件，count={len(self._file_map)}")
        for file_path, (f, _node) in list(self._file_map.items()):
            try:
                await f.close()
            except Exception as e:
                loguru_logger.error(f"AsyncFileWriter关闭文件失败 path={file_path} {e}")
        self._file_map.clear()
        self._lru_list.clear()
        loguru_logger.debug("AsyncFileWriter worker协程结束")


class Directory:
    """目录管理器，负责根据模式生成文件保存路径。

    支持两种目录分片模式:
        mode1: 根目录下按 1、2、3... 创建子目录，每个子目录最多 N 个文件。
        mode2: 按日期创建子目录 (YYYY-MM-DD)。
    """

    def __init__(
        self,
        directory_path: str | Path,
        directory_num: int = 100,
        mode: str = "mode1",
    ):
        self._directory_path = Path(directory_path).expanduser().resolve()
        self._directory_num = max(1, int(directory_num))
        self._mode = mode
        self._current_dir: Path | None = None
        self._file_counter = 0
        self._lock = threading.Lock()
        self._file_count_cache: dict[Path, int] = {}
        self._mode_handlers = {
            "mode1": self._get_mode1_directory,
            "mode2": self._get_mode2_directory,
        }
        self._init_directory()

    def _init_directory(self) -> None:
        self._directory_path.mkdir(parents=True, exist_ok=True)
        if self._mode not in self._mode_handlers:
            raise ValueError(f"不支持的目录模式: {self._mode}")
        self._current_dir = self._mode_handlers[self._mode]()

    def _get_file_count(self, dir_path: Path) -> int:
        if dir_path in self._file_count_cache:
            return self._file_count_cache[dir_path]
        if not dir_path.exists():
            self._file_count_cache[dir_path] = 0
            return 0
        count = sum(1 for item in dir_path.iterdir() if item.is_file())
        self._file_count_cache[dir_path] = count
        return count

    def _get_mode1_directory(self) -> Path:
        """mode1：根目录下按 1、2、3... 创建子目录，每个最多 directory_num 个文件。"""
        numeric_dirs = [
            int(item.name)
            for item in self._directory_path.iterdir()
            if item.is_dir() and item.name.isdigit()
        ]
        current_number = max(numeric_dirs, default=1)
        current_dir = self._directory_path / str(current_number)
        current_dir.mkdir(parents=True, exist_ok=True)

        if self._get_file_count(current_dir) >= self._directory_num:
            current_dir = self._directory_path / str(current_number + 1)
            current_dir.mkdir(parents=True, exist_ok=True)

        self._file_counter = self._get_file_count(current_dir)
        return current_dir

    def _get_mode2_directory(self) -> Path:
        """mode2：按日期创建子目录。"""
        current_dir = self._directory_path / datetime.date.today().strftime("%Y-%m-%d")
        current_dir.mkdir(parents=True, exist_ok=True)
        self._file_counter = self._get_file_count(current_dir)
        return current_dir

    def _next_directory(self) -> Path:
        if self._mode == "mode2":
            return self._get_mode2_directory()
        if self._current_dir is None:
            return self._get_mode1_directory()
        if self._file_counter >= self._directory_num:
            next_number = int(self._current_dir.name) + 1
            self._current_dir = self._directory_path / str(next_number)
            self._current_dir.mkdir(parents=True, exist_ok=True)
            self._file_counter = self._get_file_count(self._current_dir)
        return self._current_dir

    def _list_all_files(self, recursive: bool = True) -> list[Path]:
        if recursive:
            return [item for item in self._directory_path.rglob("*") if item.is_file()]
        return [item for item in self._directory_path.iterdir() if item.is_file()]

    # ---- 对外方法 ----

    def get_file_path(self, file_name: str | Path) -> Path:
        """根据分片策略获取文件写入路径。"""
        with self._lock:
            directory = self._next_directory()
            file_path = directory / Path(file_name).name
            if self._mode == "mode1" and not file_path.exists():
                self._file_counter += 1
                self._file_count_cache[directory] = self._file_counter
            return file_path

    def list_all_files(self, recursive: bool = True) -> list[Path]:
        return self._list_all_files(recursive)

    def find_file_path(self, file_name: str | Path, recursive: bool = True) -> Path | None:
        """在目录中查找文件，返回最新修改时间的匹配文件路径。"""
        target_name = Path(file_name).name
        files = self._list_all_files(recursive)
        matched_files = [item for item in files if item.name == target_name]
        if not matched_files:
            return None
        return max(matched_files, key=lambda item: item.stat().st_mtime)

    def get_current_dir(self) -> Path | None:
        return self._current_dir

    def get_stats(self) -> dict[str, Any]:
        return {
            "directory_path": self._directory_path,
            "current_dir": self._current_dir,
            "file_counter": self._file_counter,
            "directory_num": self._directory_num,
            "mode": self._mode,
        }


__all__ = ['SyncFileWriter', 'AsyncFileWriter', 'Directory']