import asyncio
import os
import threading
import time
from collections import OrderedDict
from typing import Optional, Any, Dict, List

import aiofiles

from ljp_page._core.base.Ljp_base_class import Ljp_BaseClass


class _FileHandleBase(Ljp_BaseClass):
    """
    文件句柄管理器基类 - 内部实现

    职责：
    - 维护打开的文件对象缓存
    - 实现LRU策略
    - 异步文件操作
    - 资源管理（锁、计数器等）
    """

    def __init__(self, max_open_files: int = 100, logger: Optional[Any] = None):
        """
        初始化文件句柄管理器基类

        参数:
            max_open_files: 最大同时打开文件数量
            logger: 日志记录器
        """
        super().__init__(logger)
        self._max_open_files = max_open_files
        self._file_dict: OrderedDict[str, Any] = OrderedDict()
        self._access_time: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._closed = False

    def _get_max_open_files(self) -> int:
        """获取最大打开文件数"""
        return self._max_open_files

    def _set_max_open_files(self, max_open_files: int) -> None:
        """设置最大打开文件数"""
        self._max_open_files = max_open_files

    def _get_file_count(self) -> int:
        """获取当前打开文件数量"""
        return len(self._file_dict)

    def _is_closed(self) -> bool:
        """检查管理器是否已关闭"""
        return self._closed

    async def _get_file_handle(
        self,
        file_path: str,
        mode: str = 'w',
        encoding: str = 'utf-8'
    ) -> Optional[Any]:
        """
        获取文件句柄（内部实现）

        参数:
            file_path: 文件路径
            mode: 打开模式
            encoding: 编码格式

        返回:
            异步文件对象或None
        """
        if self._closed:
            self.warning(f"[{self.__class__.__name__}] 管理器已关闭，无法获取文件句柄", self._get_file_handle.__name__)
            return None

        file_path = os.path.normpath(file_path)

        if file_path in self._file_dict:
            existing_file = self._file_dict[file_path]
            if existing_file.mode == mode and existing_file.encoding == encoding:
                self._access_time[file_path] = time.time()
                self._file_dict.move_to_end(file_path)
                return existing_file

        async with self._lock:
            if self._closed:
                return None

            if file_path in self._file_dict:
                existing_file = self._file_dict[file_path]
                if existing_file.mode == mode and existing_file.encoding == encoding:
                    self._access_time[file_path] = time.time()
                    self._file_dict.move_to_end(file_path)
                    return existing_file
                await self._close_file(file_path)

            if len(self._file_dict) >= self._max_open_files:
                oldest_key = next(iter(self._file_dict))
                await self._close_file(oldest_key)

            try:
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                open_kwargs = {'mode': mode}
                if 'b' not in mode:
                    open_kwargs['encoding'] = encoding

                file_obj = await aiofiles.open(file_path, **open_kwargs)
                self._file_dict[file_path] = file_obj
                self._access_time[file_path] = time.time()
                return file_obj

            except Exception as e:
                self.error(f"[{self.__class__.__name__}] 打开文件失败 {file_path}：{str(e)}", self._get_file_handle.__name__)
                return None

    async def _close_file(self, file_path: str) -> None:
        """
        关闭单个文件句柄（内部实现）

        参数:
            file_path: 文件路径
        """
        file_path = os.path.normpath(file_path)
        if file_path not in self._file_dict:
            return

        try:
            file_obj = self._file_dict.pop(file_path)
            if file_obj.closed:
                return

            if any(m in file_obj.mode for m in ['w', 'a', '+']):
                await file_obj.flush()
            await file_obj.close()

            if file_path in self._access_time:
                del self._access_time[file_path]

            self.debug(f"[{self.__class__.__name__}] 关闭文件：{file_path}", self._close_file.__name__)

        except Exception as e:
            self.error(f"[{self.__class__.__name__}] 关闭文件失败 {file_path}：{str(e)}", self._close_file.__name__)

    async def _close_all(self) -> None:
        """关闭所有文件句柄（内部实现）"""
        async with self._lock:
            self._closed = True
            for file_path in list(self._file_dict.keys()):
                await self._close_file(file_path)

        self.info(f"[{self.__class__.__name__}] 所有文件句柄已关闭", self._close_all.__name__)


class FileHandle(_FileHandleBase):
    """
    文件句柄管理器 - 对外接口

    功能：
    - 异步获取文件句柄
    - LRU缓存管理
    - 自动资源清理
    - 支持上下文管理器

    使用示例:
        async with FileHandle(max_open_files=100) as fh:
            file_obj = await fh.get('test.txt', mode='w')
            await file_obj.write('Hello')
    """

    def __init__(self, max_open_files: int = 100, logger: Optional[Any] = None):
        """
        初始化文件句柄管理器

        参数:
            max_open_files: 最大同时打开文件数量，默认100
            logger: 日志记录器
        """
        super().__init__(max_open_files, logger)

    def change_max_open_files(self, max_open_files: int) -> None:
        """
        修改最大打开文件数量

        参数:
            max_open_files: 新的最大打开文件数量
        """
        self._set_max_open_files(max_open_files)

    async def get(
        self,
        file_path: str,
        mode: str = 'w',
        encoding: str = 'utf-8'
    ) -> Optional[Any]:
        """
        获取文件句柄

        参数:
            file_path: 文件路径
            mode: 打开模式（同aiofiles.open），默认'w'
            encoding: 编码格式，默认'utf-8'

        返回:
            异步文件对象或None（失败时）
        """
        return await self._get_file_handle(file_path, mode, encoding)

    async def close(self, file_path: str) -> None:
        """
        关闭指定文件句柄

        参数:
            file_path: 文件路径
        """
        await self._close_file(file_path)

    async def close_all(self) -> None:
        """关闭所有文件句柄"""
        await self._close_all()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        返回:
            包含统计信息的字典
        """
        return {
            'max_open_files': self._get_max_open_files(),
            'current_open_files': self._get_file_count(),
            'closed': self._is_closed()
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """异步上下文管理器出口"""
        await self.close_all()


class _DirectoryBase(Ljp_BaseClass):
    """
    目录管理器基类 - 内部实现

    职责：
    - 维护目录轮换逻辑
    - 文件计数和缓存
    - 线程安全保证
    - 模式1和模式2的实现
    """

    def __init__(
        self,
        directory_path: str,
        directory_num: int = 100,
        mode: str = 'mode1',
        logger: Optional[Any] = None
    ):
        """
        初始化目录管理器基类

        参数:
            directory_path: 根目录路径
            directory_num: 每个子目录最大文件数
            mode: 目录模式（'mode1'或'mode2'）
            logger: 日志记录器
        """
        super().__init__(logger)
        self._directory_path = directory_path
        self._directory_num = directory_num
        self._mode = mode
        self._current_dir: Optional[str] = None
        self._file_counter = 0
        self._lock = threading.Lock()
        self._file_count_cache: Dict[str, int] = {}
        self._init_directory()

    def _get_directory_path(self) -> str:
        """获取根目录路径"""
        return self._directory_path

    def _get_current_dir(self) -> Optional[str]:
        """获取当前目录"""
        return self._current_dir

    def _get_file_counter(self) -> int:
        """获取文件计数器"""
        return self._file_counter

    def _get_file_count_cache(self) -> Dict[str, int]:
        """获取文件计数缓存"""
        return self._file_count_cache.copy()

    def _init_directory(self) -> None:
        """初始化目录结构"""
        os.makedirs(self._directory_path, exist_ok=True)
        if self._mode == 'mode1':
            self._rotate_directory_mode1()
        elif self._mode == 'mode2':
            self._rotate_directory_mode2()

    def _get_file_count(self, dir_path: str) -> int:
        """
        统计目录下的文件数量

        参数:
            dir_path: 目录路径

        返回:
            文件数量
        """
        if dir_path in self._file_count_cache:
            return self._file_count_cache[dir_path]

        try:
            count = len([
                f for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))
            ])
            self._file_count_cache[dir_path] = count
            return count
        except Exception as e:
            self.error(f'获取目录{dir_path}下文件数量失败: {e}', self._get_file_count.__name__)
            return 0

    def _rotate_directory_mode1(self) -> None:
        """模式1：数字递增子目录"""
        dirs = []
        if os.path.exists(self._directory_path):
            for d in os.listdir(self._directory_path):
                d_path = os.path.join(self._directory_path, d)
                if os.path.isdir(d_path) and d.isdigit():
                    dirs.append(int(d))
        dirs.sort()

        if not dirs:
            first_dir = os.path.join(self._directory_path, '1')
            os.makedirs(first_dir, exist_ok=True)
            self._current_dir = first_dir
            self._file_counter = 0
            return

        last_dir_num = dirs[-1]
        last_dir_path = os.path.join(self._directory_path, str(last_dir_num))

        if self._get_file_count(last_dir_path) >= self._directory_num:
            new_dir_num = last_dir_num + 1
            new_dir_path = os.path.join(self._directory_path, str(new_dir_num))
            os.makedirs(new_dir_path, exist_ok=True)
            self._current_dir = new_dir_path
            self._file_counter = 0
        else:
            self._current_dir = last_dir_path
            self._file_counter = self._get_file_count(last_dir_path)

    def _rotate_directory_mode2(self) -> None:
        """模式2：按日期分目录"""
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        today_dir = os.path.join(self._directory_path, today)
        os.makedirs(today_dir, exist_ok=True)
        self._current_dir = today_dir
        self._file_counter = 0

    def _get_file_path(self, file_name: str) -> str:
        """
        获取文件完整路径（内部实现）

        参数:
            file_name: 文件名

        返回:
            文件完整路径
        """
        with self._lock:
            if self._mode == 'mode1':
                if self._file_counter >= self._directory_num:
                    self._rotate_directory_mode1()
                self._file_counter += 1
                if self._current_dir in self._file_count_cache:
                    self._file_count_cache[self._current_dir] = self._file_counter
            elif self._mode == 'mode2':
                self._rotate_directory_mode2()

        return os.path.join(self._current_dir, file_name)

    def _list_all_files(self, recursive: bool = True) -> List[str]:
        """
        列出所有文件路径（内部实现）

        参数:
            recursive: 是否递归遍历子目录

        返回:
            文件路径列表
        """
        with self._lock:
            file_list = []
            for root, dirs, files in os.walk(self._directory_path):
                for file in files:
                    file_list.append(os.path.join(root, file))
                if not recursive:
                    break
            return file_list


class Directory(_DirectoryBase):
    """
    目录管理器 - 对外接口

    功能：
    - 自动管理文件分目录存储
    - 支持两种模式：数字递增和按日期分目录
    - 自动轮换目录
    - 文件数量统计

    使用示例:
        # 模式1：数字递增
        dir_mgr = Directory('/path/to/root', directory_num=100, mode='mode1')
        file_path = dir_mgr.get_file_path('test.txt')

        # 模式2：按日期分目录
        dir_mgr = Directory('/path/to/root', mode='mode2')
        file_path = dir_mgr.get_file_path('test.txt')
    """

    def __init__(
        self,
        directory_path: str,
        directory_num: int = 100,
        mode: str = 'mode1',
        logger: Optional[Any] = None
    ):
        """
        初始化目录管理器

        参数:
            directory_path: 根目录路径
            directory_num: 每个子目录最大文件数，默认100
            mode: 目录模式
                  'mode1': 数字递增子目录 (1, 2, 3...)
                  'mode2': 按日期分目录 (YYYY-MM-DD)
            logger: 日志记录器
        """
        super().__init__(directory_path, directory_num, mode, logger)

    def get_file_path(self, file_name: str) -> str:
        """
        获取文件完整路径

        参数:
            file_name: 文件名

        返回:
            文件完整路径
        """
        return self._get_file_path(file_name)

    def list_all_files(self, recursive: bool = True) -> List[str]:
        """
        列出所有文件路径

        参数:
            recursive: 是否递归遍历子目录，默认True

        返回:
            文件路径列表
        """
        return self._list_all_files(recursive)

    def get_current_dir(self) -> Optional[str]:
        """
        获取当前目录

        返回:
            当前目录路径
        """
        return self._get_current_dir()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        返回:
            包含统计信息的字典
        """
        return {
            'directory_path': self._get_directory_path(),
            'current_dir': self._get_current_dir(),
            'file_counter': self._get_file_counter(),
            'mode': self._mode,
            'directory_num': self._directory_num
        }


class _YsDirectoryBase(Ljp_BaseClass):
    """
    压缩目录管理器基类 - 内部实现

    职责：
    - 创建目录路径
    - 线程安全保证
    """

    def __init__(self, directory_path: str, logger: Optional[Any] = None):
        """
        初始化压缩目录管理器基类

        参数:
            directory_path: 根目录路径
            logger: 日志记录器
        """
        super().__init__(logger)
        self._directory_path = directory_path
        self._lock = threading.Lock()

    def _get_directory_path(self) -> str:
        """获取根目录路径"""
        return self._directory_path

    def _get_dir_path(self, dir_name: str, *args: str) -> str:
        """
        获取目录路径（内部实现）

        参数:
            dir_name: 目录名称
            *args: 额外的子路径

        返回:
            目录完整路径
        """
        dir_path = os.path.join(self._directory_path, dir_name, *args)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path


class YsDirectory(_YsDirectoryBase):
    """
    压缩目录管理器 - 对外接口

    功能：
    - 快速创建目录路径
    - 自动创建不存在的目录
    - 支持多级路径

    使用示例:
        ys_dir = YsDirectory('/path/to/root')
        dir_path = ys_dir.get_dir_path('data', '2024', '01')
        # 创建 /path/to/root/data/2024/01
    """

    def __init__(self, directory_path: str, logger: Optional[Any] = None):
        """
        初始化压缩目录管理器

        参数:
            directory_path: 根目录路径
            logger: 日志记录器
        """
        super().__init__(directory_path, logger)

    def get_dir_path(self, dir_name: str, *args: str) -> str:
        """
        获取目录路径

        参数:
            dir_name: 目录名称
            *args: 额外的子路径（可选）

        返回:
            目录完整路径

        示例:
            ys_dir.get_dir_path('data', '2024', '01')
            # 返回: /root/data/2024/01
        """
        return self._get_dir_path(dir_name, *args)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        返回:
            包含统计信息的字典
        """
        return {
            'directory_path': self._get_directory_path()
        }
