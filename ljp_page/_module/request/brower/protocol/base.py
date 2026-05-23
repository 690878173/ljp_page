from typing import Generic, TypeVar

#TODO：typeddict 来自typing_extensions
from typing_extensions import NotRequired, TypedDict

T_CommandParams = TypeVar('T_CommandParams')
T_CommandResponse = TypeVar('T_CommandResponse')
T_EventParams = TypeVar('T_EventParams')


class EmptyParams(TypedDict):
    """命令的空参数。"""

    pass


class EmptyResponse(TypedDict):
    """命令响应为空。"""

    pass


class Command(TypedDict, Generic[T_CommandParams, T_CommandResponse]):
    """所有命令的基本结构。

    属性：
        method：命令方法名称
        params：命令的可选参数字典
        sessionId：可选的目标会话标识符（扁平化会话）"""

    id: NotRequired[int]
    method: str
    params: NotRequired[T_CommandParams]
    sessionId: NotRequired[str]


class Response(TypedDict, Generic[T_CommandResponse]):
    """所有响应的基本结构。

    属性：
        id：与命令ID匹配的ID
        result：命令的结果数据
        sessionId：可选的目标会话标识符（扁平化会话）"""

    id: int
    result: T_CommandResponse
    sessionId: NotRequired[str]


class CDPEvent(TypedDict, Generic[T_EventParams]):
    """所有事件的基础结构。"""

    method: str
    params: NotRequired[T_EventParams]
    sessionId: NotRequired[str]
