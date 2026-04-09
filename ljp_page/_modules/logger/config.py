from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

DEFAULT_LEVEL_NAMES: dict[int, str] = {
    1: "debug",
    2: "trace",
    3: "verbose",
    4: "notice",
    5: "info",
    6: "step",
    7: "event",
    8: "check",
    9: "risk",
    10: "warning",
    11: "warn_plus",
    12: "alert",
    13: "issue",
    14: "error_minor",
    15: "error",
    16: "fatal",
    17: "panic",
    18: "security",
    19: "critical",
    20: "off",
}

DEFAULT_LEVEL_ALIASES: dict[str, int] = {
    "debug": 1,
    "trace": 2,
    "verbose": 3,
    "notice": 4,
    "info": 5,
    "step": 6,
    "event": 7,
    "check": 8,
    "risk": 9,
    "warning": 10,
    "warn": 10,
    "warrior": 10,
    "alert": 12,
    "issue": 13,
    "error": 15,
    "fatal": 16,
    "panic": 17,
    "security": 18,
    "critical": 19,
    "off": 20,
}




@dataclass
class LogConfig:
    """日志策略配置。"""
    default_level: int = 5
    enabled_levels: list[int] = field(default_factory=lambda: list(range(1, 20)))
    level_names :Mapping[int, str] | None = None
    aliases: dict[str, int] | None = None
    log_file_path: str | None = None
    output_console: bool = True
    output_file: bool = True
