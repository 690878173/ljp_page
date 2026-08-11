"""流水线模式枚举。"""

from enum import Enum


class PipelineMode(str, Enum):
    """流水线运行模式。

    MODE1: 直接用配置的 ID 列表驱动 P2（跳过 P1）。
    MODE2: 单线程 P1 → 多线程 P2 串行流水线。
    MODE3: 多线程 P1 → 多线程 P2 并行流水线。
    """

    MODE1 = "mode1"
    MODE2 = "mode2"
    MODE3 = "mode3"
