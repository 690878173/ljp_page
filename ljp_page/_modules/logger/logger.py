
from __future__ import annotations

from .config import DEFAULT_LEVEL_ALIASES, DEFAULT_LEVEL_NAMES
from .config import LogConfig
import sys
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Iterable, Dict, Any
from loguru import logger as loguru_logger

class Logger:
    """基于 loguru 实现的支持 1-20 数字级别与别名映射的日志器。"""

    def __init__(self, config: LogConfig | None = None):
        super().__init__()
        self._lock = RLock()
        self.config = config if config else LogConfig()

        # 1. 初始化级别映射和别名
        self.level_names: Dict[int, str] = dict(DEFAULT_LEVEL_NAMES)
        if self.config.level_names:
            self.level_names.update({int(k): str(v) for k, v in self.config.level_names.items()})

        self.aliases: Dict[str, int] = dict(DEFAULT_LEVEL_ALIASES)
        if self.config.aliases:
            self.aliases.update({str(k).lower(): int(v) for k, v in self.config.aliases.items()})

        # 2. 处理默认级别和启用级别
        self.default_level = self._normalize_level(self.config.default_level, fallback=5)
        self.enabled_levels: set[int] = set()
        self._update_enabled_levels(self.config.enabled_levels)

        # 3. 处理输出路径
        self.log_file_path = self._resolve_log_file_path(self.config.log_file_path)

        # 4. 初始化 loguru：先移除默认 handler
        loguru_logger.remove()

        # 5. 注册所有自定义级别到 loguru
        self._register_all_levels_to_loguru()

        # 6. 根据配置添加 handler
        self._setup_handlers()

        # 兼容原来的 self.logger 调用
        self.logger = self

    @staticmethod
    def _resolve_log_file_path(log_file_path: str | None) -> Path:
        """解析日志文件路径，默认在当前脚本目录下生成 log.log"""
        if log_file_path:
            return Path(log_file_path)
        current_dir = Path(sys.argv[0]).resolve().parent
        return current_dir / "log.log"

    def _normalize_level(self, level: int | str, fallback: int = 5) -> int:
        """将级别（数字或别名）标准化为 1-20 的整数"""
        if isinstance(level, int):
            return min(20, max(1, level))
        level_key = str(level).strip().lower()
        return min(20, max(1, self.aliases.get(level_key, fallback)))

    def _update_enabled_levels(self, levels: Iterable[int | str] | None) -> None:
        """更新启用的日志级别集合"""
        if levels is None:
            self.enabled_levels = set(range(1, 20))
        else:
            self.enabled_levels = {
                self._normalize_level(level, fallback=5) for level in levels
            }

    def _register_all_levels_to_loguru(self) -> None:
        """将所有自定义级别注册到 loguru（全局生效）"""
        for level_num, level_name in self.level_names.items():
            try:
                loguru_logger.level(level_name, no=level_num)
            except TypeError:
                # loguru 不允许重复注册同名级别，跳过即可
                pass

    def _loguru_filter(self, record: Dict[str, Any]) -> bool:
        """loguru 过滤器：控制哪些级别的日志输出"""
        level_num = record["level"].no
        if level_num == 20:
            return False
        return level_num in self.enabled_levels

    def _loguru_formatter(self, record: Dict[str, Any]) -> str:
        """loguru 格式化器：匹配原有的日志输出格式"""
        now_str = datetime.fromtimestamp(record["time"].timestamp()).strftime("%Y-%m-%d %H:%M:%S")
        level_num = record["level"].no
        level_name = self.level_names.get(level_num, f"L{level_num}")
        message = record["message"]
        return f"{now_str} | L{level_num:02d}({level_name}) | {message}\n"

    def _setup_handlers(self) -> None:
        """（重新）设置 loguru 的 handler（控制台 + 文件）"""
        with self._lock:
            # 先移除所有现有 handler
            loguru_logger.remove()

            # 添加控制台 handler
            if self.config.output_console:
                loguru_logger.add(
                    sys.stdout,
                    filter=self._loguru_filter,
                    format=self._loguru_formatter,
                    level=self.default_level
                )

            # 添加文件 handler
            if self.config.output_file:
                self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
                loguru_logger.add(
                    str(self.log_file_path),
                    filter=self._loguru_filter,
                    format=self._loguru_formatter,
                    level=self.default_level,
                    encoding="utf-8"
                )

    def set_enabled_levels(self, levels: Iterable[int | str]) -> None:
        """动态设置启用的日志级别"""
        with self._lock:
            self._update_enabled_levels(levels)
            self._setup_handlers()

    def set_default_level(self, level: int | str) -> None:
        """动态设置默认日志级别"""
        with self._lock:
            self.default_level = self._normalize_level(level, fallback=5)
            self._setup_handlers()

    def register_level(self, level: int, name: str, alias: str | None = None) -> None:
        """动态注册新的日志级别"""
        safe_level = self._normalize_level(level, fallback=5)
        with self._lock:
            # 更新本地映射
            self.level_names[safe_level] = name
            if alias:
                self.aliases[alias.lower()] = safe_level
            # 注册到 loguru
            try:
                loguru_logger.level(name, no=safe_level)
            except TypeError:
                pass
            # 重新应用 handler
            self._setup_handlers()

    def log(self, level: int | str, message: str) -> None:
        """通用日志输出方法"""
        normalized_level = self._normalize_level(level)
        level_name = self.level_names.get(normalized_level, f"L{normalized_level}")
        loguru_logger.log(level_name, message)

    # 快捷日志方法（可根据你的 DEFAULT_LEVEL_ALIASES 调整对应数值）
    def debug(self, message: str) -> None:
        self.log(DEFAULT_LEVEL_ALIASES['debug'], message)

    def info(self, message: str) -> None:
        self.log(DEFAULT_LEVEL_ALIASES['info'], message)

    def warning(self, message: str) -> None:
        self.log(DEFAULT_LEVEL_ALIASES['warning'], message)

    def error(self, message: str) -> None:
        self.log(DEFAULT_LEVEL_ALIASES['error'], message)

    def critical(self, message: str) -> None:
        self.log(DEFAULT_LEVEL_ALIASES['critical'], message)



__all__ = ["Logger"]
