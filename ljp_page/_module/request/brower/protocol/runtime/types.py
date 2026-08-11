from enum import Enum
from typing import Any

from typing_extensions import NotRequired, TypedDict

ScriptId = str
RemoteObjectId = str
UnserializableValue = str
ExecutionContextId = int
Timestamp = float
TimeDelta = float
UniqueDebuggerId = str


class SerializationType(str, Enum):
    """序列化类型。"""

    DEEP = 'deep'
    JSON = 'json'
    ID_ONLY = 'idOnly'


class DeepSerializedValueType(str, Enum):
    """深度序列化值类型。"""

    UNDEFINED = 'undefined'
    NULL = 'null'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    BIGINT = 'bigint'
    REGEXP = 'regexp'
    DATE = 'date'
    SYMBOL = 'symbol'
    ARRAY = 'array'
    OBJECT = 'object'
    FUNCTION = 'function'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    NODE = 'node'
    WINDOW = 'window'
    GENERATOR = 'generator'


class RemoteObjectType(str, Enum):
    """远程对象类型。"""

    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    BIGINT = 'bigint'


class RemoteObjectSubtype(str, Enum):
    """远程对象子类型。"""

    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEBASSEMBLYMEMORY = 'webassemblymemory'
    WASMVALUE = 'wasmvalue'


class ObjectPreviewType(str, Enum):
    """对象预览类型。"""

    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    BIGINT = 'bigint'


class ObjectPreviewSubtype(str, Enum):
    """对象预览子类型。"""

    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEBASSEMBLYMEMORY = 'webassemblymemory'
    WASMVALUE = 'wasmvalue'


class PropertyPreviewType(str, Enum):
    """属性预览类型。"""

    OBJECT = 'object'
    FUNCTION = 'function'
    UNDEFINED = 'undefined'
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    SYMBOL = 'symbol'
    ACCESSOR = 'accessor'
    BIGINT = 'bigint'


class PropertyPreviewSubtype(str, Enum):
    """属性预览子类型。"""

    ARRAY = 'array'
    NULL = 'null'
    NODE = 'node'
    REGEXP = 'regexp'
    DATE = 'date'
    MAP = 'map'
    SET = 'set'
    WEAKMAP = 'weakmap'
    WEAKSET = 'weakset'
    ITERATOR = 'iterator'
    GENERATOR = 'generator'
    ERROR = 'error'
    PROXY = 'proxy'
    PROMISE = 'promise'
    TYPEDARRAY = 'typedarray'
    ARRAYBUFFER = 'arraybuffer'
    DATAVIEW = 'dataview'
    WEBASSEMBLYMEMORY = 'webassemblymemory'
    WASMVALUE = 'wasmvalue'


class SerializationOptions(TypedDict):
    """表示序列化的选项。"""

    serialization: SerializationType
    maxDepth: NotRequired[int]
    additionalParameters: NotRequired[dict[str, Any]]


class DeepSerializedValue(TypedDict):
    """代表深度序列化的价值。"""

    type: DeepSerializedValueType
    value: NotRequired[Any]
    objectId: NotRequired[str]
    weakLocalObjectReference: NotRequired[int]


class CustomPreview(TypedDict):
    """对象的自定义预览。"""

    header: str
    bodyGetterId: NotRequired[RemoteObjectId]


class PropertyPreview(TypedDict):
    """对象的属性预览。"""

    name: str
    type: PropertyPreviewType
    value: NotRequired[str]
    valuePreview: NotRequired['ObjectPreview']
    subtype: NotRequired[PropertyPreviewSubtype]


class EntryPreview(TypedDict):
    """集合的条目预览。"""

    value: 'ObjectPreview'
    key: NotRequired['ObjectPreview']


class ObjectPreview(TypedDict):
    """包含缩写远程对象值的对象。"""

    type: ObjectPreviewType
    overflow: bool
    properties: list[PropertyPreview]
    subtype: NotRequired[ObjectPreviewSubtype]
    description: NotRequired[str]
    entries: NotRequired[list[EntryPreview]]


class RemoteObject(TypedDict):
    """引用原始 JavaScript 对象的镜像对象。"""

    type: RemoteObjectType
    subtype: NotRequired[RemoteObjectSubtype]
    className: NotRequired[str]
    value: NotRequired[Any]
    unserializableValue: NotRequired[UnserializableValue]
    description: NotRequired[str]
    deepSerializedValue: NotRequired[DeepSerializedValue]
    objectId: NotRequired[RemoteObjectId]
    preview: NotRequired[ObjectPreview]
    customPreview: NotRequired[CustomPreview]


class PropertyDescriptor(TypedDict):
    """对象属性描述符。"""

    name: str
    configurable: bool
    enumerable: bool
    value: NotRequired[RemoteObject]
    writable: NotRequired[bool]
    get: NotRequired[RemoteObject]
    set: NotRequired[RemoteObject]
    wasThrown: NotRequired[bool]
    isOwn: NotRequired[bool]
    symbol: NotRequired[RemoteObject]


class InternalPropertyDescriptor(TypedDict):
    """对象内部属性描述符。"""

    name: str
    value: NotRequired[RemoteObject]


class PrivatePropertyDescriptor(TypedDict):
    """对象私有字段描述符。"""

    name: str
    value: NotRequired[RemoteObject]
    get: NotRequired[RemoteObject]
    set: NotRequired[RemoteObject]


class CallArgument(TypedDict, total=False):
    """代表函数调用参数。"""

    value: Any
    unserializableValue: UnserializableValue
    objectId: RemoteObjectId


class ExecutionContextDescription(TypedDict):
    """描述一个与世隔绝的世界。"""

    id: ExecutionContextId
    origin: str
    name: str
    uniqueId: str
    auxData: NotRequired[dict[str, Any]]


class ExceptionDetails(TypedDict):
    """有关异常的详细信息。"""

    exceptionId: int
    text: str
    lineNumber: int
    columnNumber: int
    scriptId: NotRequired[ScriptId]
    url: NotRequired[str]
    stackTrace: NotRequired['StackTrace']
    exception: NotRequired[RemoteObject]
    executionContextId: NotRequired[ExecutionContextId]
    exceptionMetaData: NotRequired[dict[str, Any]]


class CallFrame(TypedDict):
    """运行时错误和断言的堆栈条目。"""

    functionName: str
    scriptId: ScriptId
    url: str
    lineNumber: int
    columnNumber: int


class StackTraceId(TypedDict):
    """堆栈跟踪标识符。"""

    id: str
    debuggerId: NotRequired[UniqueDebuggerId]


class StackTrace(TypedDict):
    """断言或错误消息的调用帧。"""

    callFrames: list[CallFrame]
    description: NotRequired[str]
    parent: NotRequired['StackTrace']
    parentId: NotRequired[StackTraceId]
