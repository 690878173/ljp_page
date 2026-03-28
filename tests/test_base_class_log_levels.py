# 03-28-17-10-00
from __future__ import annotations

from ljp_page.core.base.base_class import Ljp_BaseClass


class _CaptureNumericLogger:
    def __init__(self) -> None:
        self.records: list[tuple[int, str]] = []

    def log(self, level: int, message: str) -> None:
        self.records.append((level, message))


class _CaptureMethodLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    def debug(self, message: str) -> None:
        self.records.append(("debug", message))

    def info(self, message: str) -> None:
        self.records.append(("info", message))

    def warning(self, message: str) -> None:
        self.records.append(("warning", message))

    def error(self, message: str) -> None:
        self.records.append(("error", message))

    def critical(self, message: str) -> None:
        self.records.append(("critical", message))


class _DemoBase(Ljp_BaseClass):
    pass


def test_base_class_supports_numeric_levels_and_legacy_order() -> None:
    logger = _CaptureNumericLogger()
    demo = _DemoBase(logger=logger)

    demo.log(10, "warrior")
    demo.log("error", "err")
    demo.log("msg-info", "info")  # 兼容旧风格：message, level
    demo.warning("warn")
    demo.critical("critical")
    demo.log(20, "off")  # OFF 等级不输出

    assert logger.records[0][0] == 10
    assert logger.records[1][0] == 15
    assert logger.records[2][0] == 5
    assert logger.records[3][0] == 10
    assert logger.records[4][0] == 19
    assert len(logger.records) == 5


def test_base_class_falls_back_to_level_methods() -> None:
    logger = _CaptureMethodLogger()
    demo = _DemoBase(logger=logger)

    demo.log(1, "d")
    demo.log(6, "i")
    demo.log(10, "w")
    demo.log(15, "e")
    demo.log(19, "c")

    assert [item[0] for item in logger.records] == [
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ]
