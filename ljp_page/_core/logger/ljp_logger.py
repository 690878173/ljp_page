from __future__ import annotations
import sys
from threading import RLock


from loguru import logger as loguru_logger
from ljp_page._core.model import LogConfig



class Logger:
    def __init__(self, config: LogConfig | None = None):
        self._lock = RLock()
        self.config = config if config else LogConfig()
        loguru_logger.remove()
        self.logger = loguru_logger.bind(service='ljp_logger')
        self.logger.remove()


        self._zc_level()

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        with self._lock:
            self.logger.remove()
            if self.config.output_console:self.logger.add(
            sys.stdout,
            filter=self.level_filter,
            format=self.my_formatter,
            level=self.config.default_level,
            colorize=True,
            backtrace=False,  # 不打印内部错误堆栈
            diagnose=False,  # 不解析内部错误
        )

            if self.config.output_file:
                self.logger.add(
                    self.config.log_file_path / "app_{time:YYYY-MM-DD}.log",
                    level=0,
                    format=self.my_formatter,
                    filter=self.level_filter,
                    rotation="1 day",  # 每天轮转
                    retention="7 days",  # 保留7天
                    encoding="utf-8"

                )

    def _zc_level(self):
        for no, name in self.config.level_map.items():
            try:
                self.logger.level(name, color=self._get_level_color(no))
            except ValueError:
                try:
                    self.logger.level(name, no=no, color=self._get_level_color(no))
                except (ValueError, TypeError):
                    # 双重保险
                    pass

    def level_filter(self,record):
        return record["level"].no in self.config.enabled_levels

    @staticmethod
    def _get_level_color(level_num: int) -> str:
        if level_num <= 3:
            return "<cyan>"
        elif level_num <= 6:
            return "<green>"
        elif level_num <= 10:
            return "<yellow>"
        elif level_num <= 15:
            return "<red>"
        else:
            return "<bold><red>"

    @staticmethod
    def my_formatter(record):
        # 1. 时间用原生更快（但这里为了演示）
        time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S")
        level_num = record["level"].no
        level_name = record["level"].name  # 直接用原生名字
        message = record["message"]
        extra = record.get("extra", {})
        extra = {k: v for k, v in extra.items() if k != "service"}

        ctx_str = ""
        if extra:
            # ✅ 转义花括号：将 { 替换为 {{，} 替换为 }}
            escaped_parts = []
            for k, v in extra.items():
                v_str = str(v).replace('{', '{{').replace('}', '}}')
                escaped_parts.append(f"{k}={v_str}")
            ctx_str = " | " + " ".join(escaped_parts)


        return_str =  (
            f"<level>{time_str} | L{level_num:02d}({level_name}) | {message}{ctx_str}</level>\n"
        )

        return return_str

    def use_debug(self):
        self.config.output_console = True
        self.config.output_file = True
        self.config.default_level = 1
        self.config.enabled_levels = set(range(1, 20))  # 启用所有自定义级别
        self._setup_handlers()  # 重新加载 Handler


    def __getattr__(self, name):
        """当访问的属性不存在时，尝试从 _logger 上找"""
        return getattr(self.logger, name)

    def info(self, message: str, **kwargs):
        """使用自定义级别 info（编号 5）"""
        self.logger.log("info", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """使用自定义级别 debug（编号 1）"""
        self.logger.log("debug", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.log("error", message, **kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.log("critical", message, **kwargs)

logger = Logger()

__all__ = ["Logger", 'logger', 'LogConfig']
