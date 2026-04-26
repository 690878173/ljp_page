from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING, cast

from ljp_page._modules.pydoll.protocol.page.events import (
    JavascriptDialogOpeningEvent,
    JavascriptDialogOpeningEventParams,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    from ljp_page._modules.pydoll.protocol.base import CDPEvent
    from ljp_page._modules.pydoll.protocol.network.events import RequestWillBeSentEvent

from ljp_page.logger import logger


class EventsManager:
    """管理事件回调、处理和网络日志。

    处理事件回调注册、触发和维护状态
    用于网络日志和对话信息。"""

    def __init__(self) -> None:
        """将事件管理器初始化为空状态。"""
        self._event_callbacks: dict[int, dict] = {}
        self._callback_id = 0
        self.network_logs: list[RequestWillBeSentEvent] = []
        self.dialog = JavascriptDialogOpeningEvent()  #类型：忽略
        logger.info('EventsManager initialized')
        logger.debug('Initial state: callbacks=0, logs=0, dialog=empty')

    def register_callback(
        self, event_name: str, callback: Callable[[dict], Any], temporary: bool = False
    ) -> int:
        """注册特定事件类型的回调。

        参数：
            event_name：要监听的事件名称。
            回调：事件发生时调用的函数。
            临时：如果为真，则回调在第一次触发后删除。

        返回：
            供以后删除的回调 ID。"""
        self._callback_id += 1
        self._event_callbacks[self._callback_id] = {
            'event': event_name,
            'callback': callback,
            'temporary': temporary,
        }
        logger.info(f"Registered callback '{event_name}' with ID {self._callback_id}")
        logger.debug(
            f'Callback details: temporary={temporary}, total_callbacks={len(self._event_callbacks)}'
        )
        return self._callback_id

    def remove_callback(self, callback_id: int) -> bool:
        """通过 ID 删除回调。"""
        if callback_id not in self._event_callbacks:
            logger.warning(f'Callback ID {callback_id} not found')
            return False

        del self._event_callbacks[callback_id]
        logger.info(f'Removed callback ID {callback_id}')
        logger.debug(f'Remaining callbacks: {len(self._event_callbacks)}')
        return True

    def clear_callbacks(self):
        """删除所有已注册的回调。"""
        self._event_callbacks.clear()
        logger.info('All callbacks cleared')
        logger.debug('Callbacks store is now empty')

    async def process_event(self, event_data: CDPEvent):
        """处理接收到的事件并触发回调。

        处理特殊事件（网络请求、对话框）和更新
        触发注册回调之前的内部状态。"""
        event_name = event_data['method']
        logger.debug(f'Processing event: {event_name}')

        if 'Network.requestWillBeSent' in event_name:
            self._update_network_logs(event_data)

        if 'Page.javascriptDialogOpening' in event_name:
            self.dialog = JavascriptDialogOpeningEvent(
                method=event_data['method'],
                params=cast(JavascriptDialogOpeningEventParams, event_data['params']),
            )

        if 'Page.javascriptDialogClosed' in event_name:
            self.dialog = JavascriptDialogOpeningEvent()  #类型：忽略

        await self._trigger_callbacks(event_name, event_data)

    def _update_network_logs(self, event_data: RequestWillBeSentEvent):
        """将网络事件添加到日志（保留最后 10000 个条目）。"""
        self.network_logs.append(event_data)
        self.network_logs = self.network_logs[-10000:]  #仅保留最后 10000 条日志

    async def _trigger_callbacks(self, event_name: str, event_data: CDPEvent):
        """触发事件的所有已注册回调，删除临时回调。"""
        callbacks_to_remove = []

        for cb_id, cb_data in list(self._event_callbacks.items()):
            if cb_data['event'] == event_name:
                try:
                    if asyncio.iscoroutinefunction(cb_data['callback']):
                        await cb_data['callback'](event_data)
                    else:
                        cb_data['callback'](event_data)
                except Exception as e:
                    logger.error(f'Error in callback {cb_id}: {str(e)}')

                if cb_data['temporary']:
                    callbacks_to_remove.append(cb_id)

        for cb_id in callbacks_to_remove:
            self.remove_callback(cb_id)
        logger.debug(
            f"Triggered callbacks for '{event_name}'. Removed temporaries: {callbacks_to_remove}"
        )
