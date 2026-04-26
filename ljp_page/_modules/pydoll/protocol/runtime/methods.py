from enum import Enum

from typing_extensions import NotRequired, TypedDict

from ljp_page._modules.pydoll.protocol.base import Command, EmptyParams, EmptyResponse, Response
from ljp_page._modules.pydoll.protocol.runtime.types import (
    CallArgument,
    ExceptionDetails,
    ExecutionContextId,
    InternalPropertyDescriptor,
    PrivatePropertyDescriptor,
    PropertyDescriptor,
    RemoteObject,
    RemoteObjectId,
    ScriptId,
    SerializationOptions,
    TimeDelta,
)


class RuntimeMethod(str, Enum):
    """运行时域方法名称。"""

    ADD_BINDING = 'Runtime.addBinding'
    AWAIT_PROMISE = 'Runtime.awaitPromise'
    CALL_FUNCTION_ON = 'Runtime.callFunctionOn'
    COMPILE_SCRIPT = 'Runtime.compileScript'
    DISABLE = 'Runtime.disable'
    DISCARD_CONSOLE_ENTRIES = 'Runtime.discardConsoleEntries'
    ENABLE = 'Runtime.enable'
    EVALUATE = 'Runtime.evaluate'
    GET_EXCEPTION_DETAILS = 'Runtime.getExceptionDetails'
    GET_HEAP_USAGE = 'Runtime.getHeapUsage'
    GET_ISOLATE_ID = 'Runtime.getIsolateId'
    GET_PROPERTIES = 'Runtime.getProperties'
    GLOBAL_LEXICAL_SCOPE_NAMES = 'Runtime.globalLexicalScopeNames'
    QUERY_OBJECTS = 'Runtime.queryObjects'
    RELEASE_OBJECT = 'Runtime.releaseObject'
    RELEASE_OBJECT_GROUP = 'Runtime.releaseObjectGroup'
    REMOVE_BINDING = 'Runtime.removeBinding'
    RUN_IF_WAITING_FOR_DEBUGGER = 'Runtime.runIfWaitingForDebugger'
    RUN_SCRIPT = 'Runtime.runScript'
    SET_ASYNC_CALL_STACK_DEPTH = 'Runtime.setAsyncCallStackDepth'
    SET_CUSTOM_OBJECT_FORMATTER_ENABLED = 'Runtime.setCustomObjectFormatterEnabled'
    SET_MAX_CALL_STACK_SIZE_TO_CAPTURE = 'Runtime.setMaxCallStackSizeToCapture'
    TERMINATE_EXECUTION = 'Runtime.terminateExecution'


#参数类型
class AddBindingParams(TypedDict):
    """addBinding 命令的参数。"""

    name: str
    executionContextId: NotRequired[ExecutionContextId]
    executionContextName: NotRequired[str]


class AwaitPromiseParams(TypedDict):
    """waitPromise 命令的参数。"""

    promiseObjectId: RemoteObjectId
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]


class CallFunctionOnParams(TypedDict):
    """callFunctionOn 命令的参数。"""

    functionDeclaration: str
    objectId: NotRequired[RemoteObjectId]
    arguments: NotRequired[list[CallArgument]]
    silent: NotRequired[bool]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    userGesture: NotRequired[bool]
    awaitPromise: NotRequired[bool]
    executionContextId: NotRequired[ExecutionContextId]
    objectGroup: NotRequired[str]
    throwOnSideEffect: NotRequired[bool]
    uniqueContextId: NotRequired[str]
    serializationOptions: NotRequired[SerializationOptions]


class CompileScriptParams(TypedDict):
    """compileScript 命令的参数。"""

    expression: str
    sourceURL: str
    persistScript: bool
    executionContextId: NotRequired[ExecutionContextId]


class EvaluateParams(TypedDict):
    """评估命令的参数。"""

    expression: str
    objectGroup: NotRequired[str]
    includeCommandLineAPI: NotRequired[bool]
    silent: NotRequired[bool]
    contextId: NotRequired[ExecutionContextId]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    userGesture: NotRequired[bool]
    awaitPromise: NotRequired[bool]
    throwOnSideEffect: NotRequired[bool]
    timeout: NotRequired[TimeDelta]
    disableBreaks: NotRequired[bool]
    replMode: NotRequired[bool]
    allowUnsafeEvalBlockedByCSP: NotRequired[bool]
    uniqueContextId: NotRequired[str]
    serializationOptions: NotRequired[SerializationOptions]


class GetExceptionDetailsParams(TypedDict):
    """getExceptionDetails 命令的参数。"""

    errorObjectId: RemoteObjectId


class GetPropertiesParams(TypedDict):
    """getProperties 命令的参数。"""

    objectId: RemoteObjectId
    ownProperties: NotRequired[bool]
    accessorPropertiesOnly: NotRequired[bool]
    generatePreview: NotRequired[bool]
    nonIndexedPropertiesOnly: NotRequired[bool]


class GlobalLexicalScopeNamesParams(TypedDict, total=False):
    """globalLexicalScopeNames 命令的参数。"""

    executionContextId: ExecutionContextId


class QueryObjectsParams(TypedDict):
    """queryObjects 命令的参数。"""

    prototypeObjectId: RemoteObjectId
    objectGroup: NotRequired[str]


class ReleaseObjectParams(TypedDict):
    """releaseObject 命令的参数。"""

    objectId: RemoteObjectId


class ReleaseObjectGroupParams(TypedDict):
    """releaseObjectGroup 命令的参数。"""

    objectGroup: str


class RemoveBindingParams(TypedDict):
    """removeBinding 命令的参数。"""

    name: str


class RunScriptParams(TypedDict):
    """runScript 命令的参数。"""

    scriptId: ScriptId
    executionContextId: NotRequired[ExecutionContextId]
    objectGroup: NotRequired[str]
    silent: NotRequired[bool]
    includeCommandLineAPI: NotRequired[bool]
    returnByValue: NotRequired[bool]
    generatePreview: NotRequired[bool]
    awaitPromise: NotRequired[bool]


class SetAsyncCallStackDepthParams(TypedDict):
    """setAsyncCallStackDepth 命令的参数。"""

    maxDepth: int


class SetCustomObjectFormatterEnabledParams(TypedDict):
    """setCustomObjectFormatterEnabled 命令的参数。"""

    enabled: bool


class SetMaxCallStackSizeToCaptureParams(TypedDict):
    """setMaxCallStackSizeToCapture 命令的参数。"""

    size: int


#结果类型
class AwaitPromiseResult(TypedDict):
    """waitPromise 命令的结果。"""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class CallFunctionOnResult(TypedDict):
    """callFunctionOn 命令的结果。"""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class CompileScriptResult(TypedDict, total=False):
    """compileScript 命令的结果。"""

    scriptId: ScriptId
    exceptionDetails: ExceptionDetails


class EvaluateResult(TypedDict):
    """评估命令的结果。"""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


class GetExceptionDetailsResult(TypedDict, total=False):
    """getExceptionDetails 命令的结果。"""

    exceptionDetails: ExceptionDetails


class GetHeapUsageResult(TypedDict):
    """getHeapUsage 命令的结果。"""

    usedSize: float
    totalSize: float
    embedderHeapUsedSize: float
    backingStorageSize: float


class GetIsolateIdResult(TypedDict):
    """getIsolateId 命令的结果。"""

    id: str


class GetPropertiesResult(TypedDict):
    """getProperties 命令的结果。"""

    result: list[PropertyDescriptor]
    internalProperties: NotRequired[list[InternalPropertyDescriptor]]
    privateProperties: NotRequired[list[PrivatePropertyDescriptor]]
    exceptionDetails: NotRequired[ExceptionDetails]


class GlobalLexicalScopeNamesResult(TypedDict):
    """globalLexicalScopeNames 命令的结果。"""

    names: list[str]


class QueryObjectsResult(TypedDict):
    """queryObjects 命令的结果。"""

    objects: RemoteObject


class RunScriptResult(TypedDict):
    """runScript 命令的结果。"""

    result: RemoteObject
    exceptionDetails: NotRequired[ExceptionDetails]


#响应类型
AwaitPromiseResponse = Response[AwaitPromiseResult]
CallFunctionOnResponse = Response[CallFunctionOnResult]
CompileScriptResponse = Response[CompileScriptResult]
EvaluateResponse = Response[EvaluateResult]
GetExceptionDetailsResponse = Response[GetExceptionDetailsResult]
GetHeapUsageResponse = Response[GetHeapUsageResult]
GetIsolateIdResponse = Response[GetIsolateIdResult]
GetPropertiesResponse = Response[GetPropertiesResult]
GlobalLexicalScopeNamesResponse = Response[GlobalLexicalScopeNamesResult]
QueryObjectsResponse = Response[QueryObjectsResult]
RunScriptResponse = Response[RunScriptResult]


#命令类型
AddBindingCommand = Command[AddBindingParams, Response[EmptyResponse]]
AwaitPromiseCommand = Command[AwaitPromiseParams, AwaitPromiseResponse]
CallFunctionOnCommand = Command[CallFunctionOnParams, CallFunctionOnResponse]
CompileScriptCommand = Command[CompileScriptParams, CompileScriptResponse]
DisableCommand = Command[EmptyParams, Response[EmptyResponse]]
DiscardConsoleEntriesCommand = Command[EmptyParams, Response[EmptyResponse]]
EnableCommand = Command[EmptyParams, Response[EmptyResponse]]
EvaluateCommand = Command[EvaluateParams, EvaluateResponse]
GetExceptionDetailsCommand = Command[GetExceptionDetailsParams, GetExceptionDetailsResponse]
GetHeapUsageCommand = Command[EmptyParams, GetHeapUsageResponse]
GetIsolateIdCommand = Command[EmptyParams, GetIsolateIdResponse]
GetPropertiesCommand = Command[GetPropertiesParams, GetPropertiesResponse]
GlobalLexicalScopeNamesCommand = Command[
    GlobalLexicalScopeNamesParams, GlobalLexicalScopeNamesResponse
]
QueryObjectsCommand = Command[QueryObjectsParams, QueryObjectsResponse]
ReleaseObjectCommand = Command[ReleaseObjectParams, Response[EmptyResponse]]
ReleaseObjectGroupCommand = Command[ReleaseObjectGroupParams, Response[EmptyResponse]]
RemoveBindingCommand = Command[RemoveBindingParams, Response[EmptyResponse]]
RunIfWaitingForDebuggerCommand = Command[EmptyParams, Response[EmptyResponse]]
RunScriptCommand = Command[RunScriptParams, RunScriptResponse]
SetAsyncCallStackDepthCommand = Command[SetAsyncCallStackDepthParams, Response[EmptyResponse]]
SetCustomObjectFormatterEnabledCommand = Command[
    SetCustomObjectFormatterEnabledParams, Response[EmptyResponse]
]
SetMaxCallStackSizeToCaptureCommand = Command[
    SetMaxCallStackSizeToCaptureParams, Response[EmptyResponse]
]
TerminateExecutionCommand = Command[EmptyParams, Response[EmptyResponse]]
