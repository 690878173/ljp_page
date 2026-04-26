from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ljp_page._modules.pydoll.protocol.base import CDPEvent
from ljp_page._modules.pydoll.protocol.target.types import SessionID, TargetID, TargetInfo


class TargetEvent(str, Enum):
    """来自 Chrome DevTools 协议目标域的事件。

    此枚举包含与 Target 相关的事件的名称，这些事件可以是
    从 Chrome DevTools 协议收到。这些事件提供了信息
    关于目标创建、销毁以及目标之间的通信。"""

    RECEIVED_MESSAGE_FROM_TARGET = 'Target.receivedMessageFromTarget'
    """
    Notifies about a new protocol message received from the session
    (as reported in attachedToTarget event).

    Args:
        sessionId (SessionID): Identifier of a session which sends a message.
        message (str): The message content.
        targetId (TargetID): Deprecated.
    """

    TARGET_CRASHED = 'Target.targetCrashed'
    """
    Issued when a target has crashed.

    Args:
        targetId (TargetID): Identifier of the crashed target.
        status (str): Termination status type.
        errorCode (int): Termination error code.
    """

    TARGET_CREATED = 'Target.targetCreated'
    """
    Issued when a possible inspection target is created.

    Args:
        targetInfo (TargetInfo): Information about the created target.
    """

    TARGET_DESTROYED = 'Target.targetDestroyed'
    """
    Issued when a target is destroyed.

    Args:
        targetId (TargetID): Identifier of the destroyed target.
    """

    TARGET_INFO_CHANGED = 'Target.targetInfoChanged'
    """
    Issued when some information about a target has changed.
    This only happens between targetCreated and targetDestroyed.

    Args:
        targetInfo (TargetInfo): Updated information about the target.
    """

    ATTACHED_TO_TARGET = 'Target.attachedToTarget'
    """
    Issued when attached to target because of auto-attach or attachToTarget command.

    Args:
        sessionId (SessionID): Identifier assigned to the session used to send/receive messages.
        targetInfo (TargetInfo): Information about the target.
        waitingForDebugger (bool): Whether the target is waiting for debugger to attach.
    """

    DETACHED_FROM_TARGET = 'Target.detachedFromTarget'
    """
    Issued when detached from target for any reason (including detachFromTarget command).
    Can be issued multiple times per target if multiple sessions have been attached to it.

    Args:
        sessionId (SessionID): Detached session identifier.
        targetId (TargetID): Deprecated.
    """


class AttachedToTargetParams(TypedDict):
    """`attachedToTarget` 事件的参数。"""

    sessionId: SessionID
    targetInfo: TargetInfo
    waitingForDebugger: bool


class DetachedFromTargetParams(TypedDict):
    """`detachedFromTarget` 事件的参数。"""

    sessionId: SessionID
    targetId: NotRequired[TargetID]


class ReceivedMessageFromTargetParams(TypedDict):
    """“receivedMessageFromTarget”事件的参数。"""

    sessionId: SessionID
    message: str
    targetId: NotRequired[TargetID]


class TargetCreatedParams(TypedDict):
    """`targetCreated` 事件的参数。"""

    targetInfo: TargetInfo


class TargetDestroyedParams(TypedDict):
    """`targetDestroyed` 事件的参数。"""

    targetId: TargetID


class TargetCrashedParams(TypedDict):
    """`targetCrashed` 事件的参数。"""

    targetId: TargetID
    status: str
    errorCode: int


class TargetInfoChangedParams(TypedDict):
    """`targetInfoChanged` 事件的参数。"""

    targetInfo: TargetInfo


AttachedToTargetEvent = CDPEvent[AttachedToTargetParams]
DetachedFromTargetEvent = CDPEvent[DetachedFromTargetParams]
ReceivedMessageFromTargetEvent = CDPEvent[ReceivedMessageFromTargetParams]
TargetCreatedEvent = CDPEvent[TargetCreatedParams]
TargetDestroyedEvent = CDPEvent[TargetDestroyedParams]
TargetCrashedEvent = CDPEvent[TargetCrashedParams]
TargetInfoChangedEvent = CDPEvent[TargetInfoChangedParams]
