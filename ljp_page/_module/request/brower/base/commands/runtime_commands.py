from __future__ import annotations
__all__ = ['RuntimeCommands']

from typing import TYPE_CHECKING, Optional

from ljp_page._module.request.brower.base.protocol.base import Command
from ljp_page._module.request.brower.base.protocol.runtime.methods import (
    AddBindingParams,
    AwaitPromiseParams,
    CallFunctionOnParams,
    CompileScriptParams,
    EvaluateParams,
    GetPropertiesParams,
    GlobalLexicalScopeNamesParams,
    QueryObjectsParams,
    ReleaseObjectGroupParams,
    ReleaseObjectParams,
    RemoveBindingParams,
    RunScriptParams,
    RuntimeMethod,
    SetAsyncCallStackDepthParams,
    SetCustomObjectFormatterEnabledParams,
    SetMaxCallStackSizeToCaptureParams,
)

if TYPE_CHECKING:
    from ljp_page._module.request.brower.base.protocol.runtime.methods import (
        AddBindingCommand,
        AwaitPromiseCommand,
        CallArgument,
        CallFunctionOnCommand,
        CompileScriptCommand,
        DisableCommand,
        EnableCommand,
        EvaluateCommand,
        GetPropertiesCommand,
        GlobalLexicalScopeNamesCommand,
        QueryObjectsCommand,
        ReleaseObjectCommand,
        ReleaseObjectGroupCommand,
        RemoveBindingCommand,
        RunScriptCommand,
        SerializationOptions,
        SetAsyncCallStackDepthCommand,
        SetCustomObjectFormatterEnabledCommand,
        SetMaxCallStackSizeToCaptureCommand,
    )


class RuntimeCommands:
    """使用 Chrome 与 JavaScript 运行时交互的类
    开发工具协议。

    此类提供了创建用于评估 JavaScript 的命令的方法
    表达式、在 JavaScript 对象上调用函数以及检索
    通过 CDP 的对象属性。

    属性：
        EVALUATE_TEMPLATE (dict)：Runtime.evaluate 命令的模板。
        CALL_FUNCTION_ON_TEMPLATE (dict)：模板
            Runtime.callFunctionOn 命令。
        GET_PROPERTIES (dict)：Runtime.getProperties 命令的模板。"""

    @staticmethod
    def add_binding(name: str, execution_context_name: Optional[str] = None) -> AddBindingCommand:
        """创建一个命令来添加 JavaScript 绑定。

        参数：
            name (str)：要添加的绑定的名称。
            execution_context_name（可选[str]）：要绑定到的执行上下文的名称。

        返回：
            AddBindingCommand：添加 JavaScript 绑定的命令对象。"""
        params = AddBindingParams(name=name)
        if execution_context_name is not None:
            params['executionContextName'] = execution_context_name

        return Command(method=RuntimeMethod.ADD_BINDING, params=params)

    @staticmethod
    def await_promise(
        promise_object_id: str,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
    ) -> AwaitPromiseCommand:
        """创建一个命令来等待 JavaScript 承诺并返回其结果。

        参数：
            Promise_object_id (str)：要等待的 Promise 的 ID。
            return_by_value (Optional[bool]): 是否按值返回结果
                的参考。
            generate_preview (Optional[bool]): 是否生成结果预览。

        返回：
            AwaitPromiseCommand：等待承诺的命令对象。"""
        params = AwaitPromiseParams(promiseObjectId=promise_object_id)
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview

        return Command(method=RuntimeMethod.AWAIT_PROMISE, params=params)

    @staticmethod
    def call_function_on(
        function_declaration: str,
        object_id: Optional[str] = None,
        arguments: Optional[list[CallArgument]] = None,
        silent: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        throw_on_side_effect: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> CallFunctionOnCommand:
        """创建一个命令来调用特定对象上具有给定声明的函数。

        参数：
            function_declaration (str)：要调用的函数的声明。
            object_id（可选[str]）：调用函数的对象的ID。
            参数（可选[list[CallArgument]]）：传递给函数的参数。
            silent（可选[bool]）：是否静默异常。
            return_by_value (Optional[bool]): 是否按值返回结果
                的参考。
            generate_preview (Optional[bool]): 是否生成结果预览。
            user_gesture （可选[bool]）：是否将呼叫视为由用户手势发起。
            wait_promise (Optional[bool]): 是否等待 Promise 结果。
            execution_context_id（可选[int]）：调用的执行上下文的ID
                函数在.
            object_group（可选[str]）：结果的符号组名称。
            throw_on_side_effect (可选[bool]): 如果无法产生副作用，是否抛出
                排除。
            unique_context_id（可选[str]）：函数调用的唯一上下文ID。
            Serialization_options（可选[SerializationOptions]）：序列化选项
                结果。

        返回：
            CallFunctionOnCommand：调用对象上的函数的命令对象。"""
        params = CallFunctionOnParams(functionDeclaration=function_declaration)
        if object_id is not None:
            params['objectId'] = object_id
        if arguments is not None:
            params['arguments'] = arguments
        if silent is not None:
            params['silent'] = silent
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if user_gesture is not None:
            params['userGesture'] = user_gesture
        if await_promise is not None:
            params['awaitPromise'] = await_promise
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id
        if object_group is not None:
            params['objectGroup'] = object_group
        if throw_on_side_effect is not None:
            params['throwOnSideEffect'] = throw_on_side_effect
        if unique_context_id is not None:
            params['uniqueContextId'] = unique_context_id
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options

        return Command(method=RuntimeMethod.CALL_FUNCTION_ON, params=params)

    @staticmethod
    def compile_script(
        expression: str,
        source_url: str,
        persist_script: bool = False,
        execution_context_id: Optional[int] = None,
    ) -> CompileScriptCommand:
        """创建编译 JavaScript 表达式的命令。

        参数：
            表达式 (str)：要编译的 JavaScript 表达式。
            source_url (str)：脚本源文件的 URL。
            persist_script (bool): 是否保留编译后的脚本。
            execution_context_id（可选[int]）：要编译的执行上下文的ID
                中的脚本。

        返回：
            CompileScriptCommand：编译脚本的命令对象。"""
        params = CompileScriptParams(
            expression=expression, sourceURL=source_url, persistScript=persist_script
        )
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id

        return Command(method=RuntimeMethod.COMPILE_SCRIPT, params=params)

    @staticmethod
    def disable() -> DisableCommand:
        """禁用运行时域。

        返回：
            DisableCommand：禁用运行时域的命令对象。"""
        return Command(method=RuntimeMethod.DISABLE)

    @staticmethod
    def enable() -> EnableCommand:
        """启用运行时域。

        返回：
            EnableCommand：启用运行时域的命令对象。"""
        return Command(method=RuntimeMethod.ENABLE)

    @staticmethod
    def evaluate(  #编号：PLR0912
        expression: str,
        object_group: Optional[str] = None,
        include_command_line_api: Optional[bool] = None,
        silent: Optional[bool] = None,
        context_id: Optional[int] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        user_gesture: Optional[bool] = None,
        await_promise: Optional[bool] = None,
        throw_on_side_effect: Optional[bool] = None,
        timeout: Optional[float] = None,
        disable_breaks: Optional[bool] = None,
        repl_mode: Optional[bool] = None,
        allow_unsafe_eval_blocked_by_csp: Optional[bool] = None,
        unique_context_id: Optional[str] = None,
        serialization_options: Optional[SerializationOptions] = None,
    ) -> EvaluateCommand:
        """创建一个命令来计算全局上下文中的 JavaScript 表达式。

        参数：
            表达式 (str)：要计算的 JavaScript 表达式。
            object_group（可选[str]）：结果的符号组名称。
            include_command_line_api （可选[bool]）：是否包含命令行 API。
            silent（可选[bool]）：是否静默异常。
            context_id（可选[int]）：要在其中进行评估的执行上下文的 ID。
            return_by_value (Optional[bool]): 是否按值返回结果
                的参考。
            generate_preview (Optional[bool]): 是否生成结果预览。
            user_gesture（可选[bool]）：是否将评估视为由用户手势发起。
            wait_promise (Optional[bool]): 是否等待 Promise 结果。
            throw_on_side_effect (可选[bool]): 如果无法产生副作用，是否抛出
                排除。
            timeout （可选[float]）：超时（以毫秒为单位）。
            disable_breaks（可选[bool]）：是否在评估期间禁用断点。
            repl_mode (Optional[bool]): 是否以 REPL 模式执行。
            allow_unsafe_eval_blocked_by_csp（可选[bool]）：允许不安全的评估。
            unique_context_id（可选[str]）：用于评估的唯一上下文ID。
            Serialization_options（可选[SerializationOptions]）：序列化
                为了结果。

        返回：
            EvaluateCommand：评估 JavaScript 的命令对象。"""
        params = EvaluateParams(expression=expression)
        if object_group is not None:
            params['objectGroup'] = object_group
        if include_command_line_api is not None:
            params['includeCommandLineAPI'] = include_command_line_api
        if silent is not None:
            params['silent'] = silent
        if context_id is not None:
            params['contextId'] = context_id
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if user_gesture is not None:
            params['userGesture'] = user_gesture
        if await_promise is not None:
            params['awaitPromise'] = await_promise
        if throw_on_side_effect is not None:
            params['throwOnSideEffect'] = throw_on_side_effect
        if timeout is not None:
            params['timeout'] = timeout
        if disable_breaks is not None:
            params['disableBreaks'] = disable_breaks
        if repl_mode is not None:
            params['replMode'] = repl_mode
        if allow_unsafe_eval_blocked_by_csp is not None:
            params['allowUnsafeEvalBlockedByCSP'] = allow_unsafe_eval_blocked_by_csp
        if unique_context_id is not None:
            params['uniqueContextId'] = unique_context_id
        if serialization_options is not None:
            params['serializationOptions'] = serialization_options

        return Command(method=RuntimeMethod.EVALUATE, params=params)

    @staticmethod
    def get_properties(
        object_id: str,
        own_properties: Optional[bool] = None,
        accessor_properties_only: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        non_indexed_properties_only: Optional[bool] = None,
    ) -> GetPropertiesCommand:
        """创建一个命令来获取 JavaScript 对象的属性。

        参数：
            object_id (str)：要获取其属性的对象的 ID。
            own_properties (Optional[bool]): 是否只返回自己的属性。
            accessor_properties_only（可选[bool]）：是否仅返回访问器属性。
            generate_preview（可选[bool]）：是否生成属性值的预览。
            non_indexed_properties_only （可选[bool]）：是否仅返回非索引
                属性。

        返回：
            GetPropertiesCommand：获取对象属性的命令对象。"""
        params = GetPropertiesParams(objectId=object_id)
        if own_properties is not None:
            params['ownProperties'] = own_properties
        if accessor_properties_only is not None:
            params['accessorPropertiesOnly'] = accessor_properties_only
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if non_indexed_properties_only is not None:
            params['nonIndexedPropertiesOnly'] = non_indexed_properties_only

        return Command(method=RuntimeMethod.GET_PROPERTIES, params=params)

    @staticmethod
    def global_lexical_scope_names(
        execution_context_id: Optional[int] = None,
    ) -> GlobalLexicalScopeNamesCommand:
        """创建一个命令以从全局词法范围中检索变量名称。

        参数：
            execution_context_id（可选[int]）：要获取范围的执行上下文的ID
                名字来自.

        返回：
            GlobalLexicalScopeNamesCommand：获取全局词法的命令对象
                范围名称。"""
        params = GlobalLexicalScopeNamesParams()
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id

        return Command(method=RuntimeMethod.GLOBAL_LEXICAL_SCOPE_NAMES, params=params)

    @staticmethod
    def query_objects(
        prototype_object_id: str,
        object_group: Optional[str] = None,
    ) -> QueryObjectsCommand:
        """创建一个命令来查询具有给定原型的对象。

        参数：
            prototype_object_id (str)：原型对象的ID。
            object_group（可选[str]）：结果的符号组名称。

        返回：
            QueryObjectsCommand：查询对象的命令对象。"""
        params = QueryObjectsParams(prototypeObjectId=prototype_object_id)
        if object_group is not None:
            params['objectGroup'] = object_group

        return Command(method=RuntimeMethod.QUERY_OBJECTS, params=params)

    @staticmethod
    def release_object(
        object_id: str,
    ) -> ReleaseObjectCommand:
        """创建释放 JavaScript 对象的命令。

        参数：
            object_id (str)：要释放的对象的 ID。

        返回：
            ReleaseObjectCommand：释放对象的命令对象。"""
        params = ReleaseObjectParams(objectId=object_id)

        return Command(method=RuntimeMethod.RELEASE_OBJECT, params=params)

    @staticmethod
    def release_object_group(
        object_group: str,
    ) -> ReleaseObjectGroupCommand:
        """创建一个命令来释放组中的所有对象。

        参数：
            object_group (str)：要释放的对象组的名称。

        返回：
            ReleaseObjectGroupCommand：释放对象组的命令对象。"""
        params = ReleaseObjectGroupParams(objectGroup=object_group)
        return Command(method=RuntimeMethod.RELEASE_OBJECT_GROUP, params=params)

    @staticmethod
    def remove_binding(
        name: str,
    ) -> RemoveBindingCommand:
        """创建一个命令来删除 JavaScript 绑定。

        参数：
            name (str)：要删除的绑定的名称。

        返回：
            RemoveBindingCommand：用于删除 JavaScript 绑定的命令对象。"""
        params = RemoveBindingParams(name=name)
        return Command(method=RuntimeMethod.REMOVE_BINDING, params=params)

    @staticmethod
    def run_script(
        script_id: str,
        execution_context_id: Optional[int] = None,
        object_group: Optional[str] = None,
        silent: Optional[bool] = None,
        include_command_line_api: Optional[bool] = None,
        return_by_value: Optional[bool] = None,
        generate_preview: Optional[bool] = None,
        await_promise: Optional[bool] = None,
    ) -> RunScriptCommand:
        """创建一个命令来运行已编译的脚本。

        参数：
            script_id (str)：要运行的已编译脚本的 ID。
            execution_context_id（可选[int]）：运行脚本的执行上下文的 ID。
            object_group（可选[str]）：结果的符号组名称。
            silent（可选[bool]）：是否静默异常。
            include_command_line_api （可选[bool]）：是否包含命令行 API。
            return_by_value (Optional[bool]): 是否按值返回结果
                的参考。
            generate_preview (Optional[bool]): 是否生成结果预览。
            wait_promise (Optional[bool]): 是否等待 Promise 结果。

        返回：
            RunScriptCommand：运行脚本的命令对象。"""
        params = RunScriptParams(scriptId=script_id)
        if execution_context_id is not None:
            params['executionContextId'] = execution_context_id
        if object_group is not None:
            params['objectGroup'] = object_group
        if silent is not None:
            params['silent'] = silent
        if include_command_line_api is not None:
            params['includeCommandLineAPI'] = include_command_line_api
        if return_by_value is not None:
            params['returnByValue'] = return_by_value
        if generate_preview is not None:
            params['generatePreview'] = generate_preview
        if await_promise is not None:
            params['awaitPromise'] = await_promise

        return Command(method=RuntimeMethod.RUN_SCRIPT, params=params)

    @staticmethod
    def set_async_call_stack_depth(
        max_depth: int,
    ) -> SetAsyncCallStackDepthCommand:
        """创建一个命令来设置异步调用堆栈深度。

        参数：
            max_depth (int)：异步调用堆栈的最大深度。

        返回：
            SetAsyncCallStackDepthCommand：用于设置异步调用堆栈深度的命令对象。"""
        params = SetAsyncCallStackDepthParams(maxDepth=max_depth)
        return Command(method=RuntimeMethod.SET_ASYNC_CALL_STACK_DEPTH, params=params)

    @staticmethod
    def set_custom_object_formatter_enabled(
        enabled: bool,
    ) -> SetCustomObjectFormatterEnabledCommand:
        """创建一个命令来启用或禁用自定义对象格式化程序。

        参数：
            enabled (bool): 是否启用自定义对象格式化程序。

        返回：
            SetCustomObjectFormatterEnabledCommand：启用/禁用自定义的命令对象
                对象格式化程序。"""
        params = SetCustomObjectFormatterEnabledParams(enabled=enabled)
        return Command(method=RuntimeMethod.SET_CUSTOM_OBJECT_FORMATTER_ENABLED, params=params)

    @staticmethod
    def set_max_call_stack_size_to_capture(
        size: int,
    ) -> SetMaxCallStackSizeToCaptureCommand:
        """创建一个命令来设置要捕获的最大调用堆栈大小。

        参数：
            size (int)：要捕获的最大调用堆栈大小。

        返回：
            SetMaxCallStackSizeToCaptureCommand：用于设置最大调用堆栈大小的命令对象。"""
        params = SetMaxCallStackSizeToCaptureParams(size=size)
        return Command(method=RuntimeMethod.SET_MAX_CALL_STACK_SIZE_TO_CAPTURE, params=params)
