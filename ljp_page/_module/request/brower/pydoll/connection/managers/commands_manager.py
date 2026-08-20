from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

__all__ = ['CommandsManager']

if TYPE_CHECKING:
    from base import Command

from ljp_page.logger import loguru_logger


class CommandsManager:
    """管理 CDP 命令的命令生命周期和 ID 分配。

    处理命令未来创建、ID 生成和响应解析
    用于异步命令执行。"""

    def __init__(self) -> None:
        """将命令管理器初始化为空状态。"""
        self._pending_commands: dict[int, asyncio.Future] = {}
        self._id = 1
        loguru_logger.debug('CommandsManager initialized')

    def create_command_future(self, command: Command) -> asyncio.Future:
        """为命令创建未来并分配唯一 ID。

        参数：
            command：准备执行的命令。

        返回：
            命令完成时解决的未来。"""
        command['id'] = self._id
        future = asyncio.Future()  #类型：忽略
        self._pending_commands[self._id] = future
        self._id += 1
        loguru_logger.debug(
            f'Created future for command id={command["id"]} method={command.get("method")}'
        )
        return future

    def resolve_command(self, response_id: int, result: str):
        """解决挂起的命令及其结果。"""
        if response_id in self._pending_commands:
            self._pending_commands[response_id].set_result(result)
            del self._pending_commands[response_id]
            loguru_logger.debug(f'Resolved command future id={response_id}')

    def remove_pending_command(self, command_id: int):
        """删除挂起的命令而不解决（针对超时/取消）。"""
        if command_id in self._pending_commands:
            del self._pending_commands[command_id]
            loguru_logger.debug(f'Removed pending command id={command_id}')
