from __future__ import annotations

import asyncio
import json

from contextlib import suppress
from typing import TYPE_CHECKING, cast

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.protocol import State

from ljp_page._module.request.brower.pydoll.connection.managers import CommandsManager, EventsManager
from ljp_page._module.request.brower.pydoll.exceptions import (
    CommandExecutionTimeout,
    WebSocketConnectionClosed,
)
from base import CDPEvent, Response
from ljp_page._module.request.brower.pydoll.utils import get_browser_ws_address

__all__ = ['ConnectionHandler']

if TYPE_CHECKING:
    from typing import Any, AsyncGenerator, Awaitable, Callable, Coroutine, Optional, Union

    from websockets.asyncio.client import connect as Connect

    from base import Command, T_CommandParams, T_CommandResponse

from ljp_page.logger import logger


class ConnectionHandler:
    """Chrome DevTools 协议端点的 WebSocket 连接管理器。

    处理连接生命周期、命令执行和事件订阅
    对于浏览器级和页面级 CDP 端点。"""

    def __init__(
        self,
        connection_port: Optional[int] = None,
        page_id: Optional[str] = None,
        ws_address_resolver: Callable[[int], Coroutine[Any, Any, str]] = get_browser_ws_address,
        ws_connector: type[Connect] = websockets.connect,
        ws_address: Optional[str] = None,
    ):
        """初始化连接处理程序。

        参数：
            connection_port：浏览器的调试服务器端口。
            page_id：目标页面ID。如果无，则连接到浏览器级端点。
            ws_address_resolver：从端口解析 WebSocket URL 的函数。
            ws_connector：WebSocket连接工厂（主要用于测试）。
            ws_address：WebSocket 地址。它优先于connection_port 和page_id。"""
        self._connection_port = connection_port
        self._page_id = page_id
        self._ws_address_resolver = ws_address_resolver
        self._ws_connector = ws_connector
        self._ws_address = ws_address
        self._ws_connection: Optional[ClientConnection] = None
        self._command_manager = CommandsManager()
        self._events_handler = EventsManager()
        self._receive_task: Optional[asyncio.Task] = None
        logger.debug('ConnectionHandler initialized.')
        logger.debug(
            f'Init params: port={self._connection_port}, page_id={self._page_id}, '
            f'ws_address_set={bool(self._ws_address)}'
        )

    @property
    def network_logs(self):
        """访问捕获的网络请求和响应日志。"""
        return self._events_handler.network_logs

    @property
    def dialog(self):
        """访问当前活动的 JavaScript 对话框信息。"""
        return self._events_handler.dialog

    async def ping(self) -> bool:
        """测试 WebSocket 连接是否处于活动状态且响应良好。"""
        with suppress(Exception):
            logger.debug('Pinging WebSocket connection')
            await self._ensure_active_connection()
            await cast(ClientConnection, self._ws_connection).ping()
            logger.debug('Ping OK')
            return True
        return False

    async def execute_command(
        self, command: Command[T_CommandParams, T_CommandResponse], timeout: int = 60
    ) -> T_CommandResponse:
        """发送 CDP 命令并等待响应。

        参数：
            命令：要发送的 CDP 命令。
            timeout：等待响应的最大秒数。

        返回：
            解析的响应对象与命令的预期类型匹配。

        加薪：
            CommandExecutionTimeout：如果浏览器在超时内没有响应。
            WebSocketConnectionClosed：如果连接在执行期间关闭。"""
        await self._ensure_active_connection()
        future = self._command_manager.create_command_future(command)
        command_str = json.dumps(command)

        try:
            ws = cast(ClientConnection, self._ws_connection)
            logger.debug(
                f'Sending command: id={command.get("id")}, method={command.get("method")}, '
                f'timeout={timeout}s'
            )
            start = asyncio.get_event_loop().time()
            await ws.send(command_str)
            response: str = await asyncio.wait_for(future, timeout)
            elapsed = asyncio.get_event_loop().time() - start
            logger.debug(f'Command completed: id={command.get("id")} in {elapsed:.3f}s')
            return json.loads(response)
        except asyncio.TimeoutError:
            self._command_manager.remove_pending_command(command['id'])
            logger.error(
                f'Command timeout: id={command.get("id")}, method={command.get("method")}, '
                f'timeout={timeout}s'
            )
            raise CommandExecutionTimeout()
        except websockets.ConnectionClosed:
            await self._handle_connection_loss()
            logger.warning(f'WebSocket connection closed during command: id={command.get("id")}')
            raise WebSocketConnectionClosed()

    async def register_callback(
        self,
        event_name: str,
        callback: Callable[[dict], Awaitable[None]],
        temporary: bool = False,
    ) -> int:
        """注册 CDP 事件的事件侦听器。

        参数：
            event_name：CDP 事件名称（例如“Page.loadEventFired”）。
            回调：事件发生时调用的异步函数。
            临时：如果为真，则回调在第一次触发后删除。

        返回：
            供以后删除的回调 ID。

        注意：
            在事件触发之前必须启用相应的 CDP 域。"""
        callback_id = self._events_handler.register_callback(event_name, callback, temporary)
        logger.debug(
            f'Registered callback: id={callback_id}, event={event_name}, temporary={temporary}'
        )
        return callback_id

    async def remove_callback(self, callback_id: int) -> bool:
        """通过 ID 删除已注册的事件回调。"""
        removed = self._events_handler.remove_callback(callback_id)
        logger.debug(f'Removed callback: id={callback_id}, removed={removed}')
        return removed

    async def clear_callbacks(self):
        """删除所有已注册的事件回调。"""
        logger.debug('Clearing all callbacks')
        self._events_handler.clear_callbacks()

    async def close(self):
        """关闭WebSocket连接并释放资源。"""
        await self.clear_callbacks()
        if self._ws_connection is None:
            logger.debug('Close called but no active WebSocket connection')
            return

        with suppress(websockets.ConnectionClosed):
            await self._ws_connection.close()
        logger.info('WebSocket connection closed.')

    async def _ensure_active_connection(self):
        """确保存在活动连接，并根据需要建立新连接。"""
        if self._ws_connection is None or self._ws_connection.state is State.CLOSED:
            logger.debug('No active WebSocket connection; establishing new one')
            await self._establish_new_connection()

    async def _establish_new_connection(self):
        """创建新的 WebSocket 连接并开始事件侦听。"""
        ws_address = await self._resolve_ws_address()
        logger.info(f'Connecting to {ws_address}')
        self._ws_connection = await self._ws_connector(
            ws_address,
            max_size=1024 * 1024 * 10,  # 限制为 10MB
        )
        self._receive_task = asyncio.create_task(self._receive_events())
        logger.debug('WebSocket connection established')

    async def _resolve_ws_address(self):
        """根据页面ID确定正确的WebSocket地址。"""
        if self._ws_address:
            logger.debug('Using provided WebSocket address')
            return self._ws_address
        if not self._page_id:
            resolved = await self._ws_address_resolver(self._connection_port)
            logger.debug(f'Resolved browser-level WebSocket address: {resolved}')
            return resolved
        address = f'ws://localhost:{self._connection_port}/devtools/page/{self._page_id}'
        logger.debug(f'Resolved page-level WebSocket address: {address}')
        return address

    async def _handle_connection_loss(self):
        """连接丢失后清理资源。"""
        if self._ws_connection and self._ws_connection.state is not State.CLOSED:
            await self._ws_connection.close()
        self._ws_connection = None

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        logger.info('Connection resources cleaned up')

    async def _receive_events(self):
        """用于接收和处理 WebSocket 消息的主循环。"""
        try:
            async for raw_message in self._incoming_messages():
                await self._process_single_message(raw_message)
        except websockets.ConnectionClosed as e:
            logger.info(f'Connection closed gracefully: {e}')
        except Exception as e:
            logger.error(f'Unexpected error in event loop: {e}')
            raise

    async def _incoming_messages(self) -> AsyncGenerator[Union[str, bytes], None]:
        """生成器从 WebSocket 连接生成原始消息。"""
        ws = cast(ClientConnection, self._ws_connection)

        while ws.state is not State.CLOSED:
            yield await ws.recv()

    async def _process_single_message(self, raw_message: str):
        """处理单个原始 WebSocket 消息。"""
        message = self._parse_message(raw_message)
        if not message:
            return

        if self._is_command_response(message):
            message = cast(Response, message)
            await self._handle_command_message(message)
        else:
            message = cast(CDPEvent, message)
            await self._handle_event_message(message)

    @staticmethod
    def _parse_message(raw_message: str) -> Union[CDPEvent, Response, None]:
        """将原始消息字符串解析为 JSON 对象。"""
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning(f'Failed to parse message: {raw_message[:200]}...')
            return None

    @staticmethod
    def _is_command_response(message: Union[CDPEvent, Response]) -> bool:
        """确定消息是命令响应还是事件通知。"""
        return 'id' in message and isinstance(message.get('id'), int)

    async def _handle_command_message(self, message: Response):
        """处理命令响应消息。"""
        logger.debug(f'Processing command response: {message.get("id")}')
        self._command_manager.resolve_command(message['id'], json.dumps(message))

    async def _handle_event_message(self, message: CDPEvent):
        """处理事件通知消息。"""
        event_type = message.get('method', 'unknown-event')
        logger.debug(f'Processing {event_type} event')
        await self._events_handler.process_event(message)

    def __repr__(self):
        """用于调试的字符串表示形式。"""
        return f'ConnectionHandler(port={self._connection_port})'

    def __str__(self):
        """用户友好的字符串表示。"""
        return f'ConnectionHandler(port={self._connection_port})'

    async def __aenter__(self):
        """异步上下文管理器条目。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出并进行清理。"""
        await self.close()
