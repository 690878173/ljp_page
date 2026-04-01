# 03-31-20-21-05
from dataclasses import dataclass, field


@dataclass
class LogConfig:
    """日志等级与输出策略配置。"""

    default_level: int = 5
    enabled_levels: list[int] = field(default_factory=lambda: list(range(1, 20)))
    level_names: dict[int, str] | None = None
    aliases: dict[str, int] | None = None
    log_file_path: str | None = None
    output_console: bool = True
    output_file: bool = True
