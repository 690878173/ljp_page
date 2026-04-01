"""03-28-15-07-30 数字等级日志系统。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Iterable, Mapping

from ...config.request_config import DEFAULT_LEVEL_ALIASES, DEFAULT_LEVEL_NAMES
from ljp_page.core.base.Ljp_base_class import Ljp_BaseClass


class Logger(Ljp_BaseClass):
    """支持 1-20 数字等级、等级别名与等级白名单控制。"""

    def __init__(
        self,
        log_file_path: str | None = None,
        log_level: int | str = 5,
        enabled_levels: Iterable[int] | None = None,
        level_names: Mapping[int, str] | None = None,
        aliases: Mapping[str, int] | None = None,
        output_console: bool = True,
        output_file: bool = True,
    ) -> None:
        super().__init__()
        self._lock = RLock()

        self.level_names: dict[int, str] = dict(DEFAULT_LEVEL_NAMES)
        if level_names:
            self.level_names.update({int(k): str(v) for k, v in level_names.items()})

        self.aliases: dict[str, int] = dict(DEFAULT_LEVEL_ALIASES)
        if aliases:
            self.aliases.update({str(k).lower(): int(v) for k, v in aliases.items()})

        self.default_level = self._normalize_level(log_level, fallback=5)
        if enabled_levels is None:
            self.enabled_levels = set(range(1, 20))
        else:
            self.enabled_levels = {
                self._normalize_level(level, fallback=5) for level in enabled_levels
            }

        self.output_console = bool(output_console)
        self.output_file = bool(output_file)
        self.log_file_path = self._resolve_log_file_path(log_file_path)

        # 兼容旧属性访问：外部若访问 logger.logger，返回当前实例。
        self.logger = self

    @staticmethod
    def _resolve_log_file_path(log_file_path: str | None) -> Path:
        if log_file_path:
            return Path(log_file_path)
        current_dir = Path(sys.argv[0]).resolve().parent
        return current_dir / "log.log"

    def _normalize_level(self, level: int | str, fallback: int = 5) -> int:
        if isinstance(level, int):
            return min(20, max(1, level))
        level_key = str(level).strip().lower()
        return min(20, max(1, self.aliases.get(level_key, fallback)))

    def set_enabled_levels(self, levels: Iterable[int]) -> None:
        """设置可输出日志等级白名单。"""

        with self._lock:
            self.enabled_levels = {
                self._normalize_level(level, fallback=5) for level in levels
            }

    def set_default_level(self, level: int | str) -> None:
        """设置默认日志等级。"""

        with self._lock:
            self.default_level = self._normalize_level(level, fallback=5)

    def register_level(self, level: int, name: str, alias: str | None = None) -> None:
        """注册或更新自定义等级名称。"""

        safe_level = self._normalize_level(level, fallback=5)
        with self._lock:
            self.level_names[safe_level] = name
            if alias:
                self.aliases[alias.lower()] = safe_level

    def _should_emit(self, level: int) -> bool:
        if level == 20:
            return False
        return level in self.enabled_levels

    def _format_line(self, level: int, message: str) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_name = self.level_names.get(level, f"L{level}")
        return f"{now_str} | L{level:02d}({level_name}) | {message}"

    def _emit(self, line: str) -> None:
        if self.output_console:
            print(line)
        if self.output_file:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file_path.open("a", encoding="utf-8") as file_handle:
                file_handle.write(f"{line}\n")
