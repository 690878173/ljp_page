import functools
from typing import Union, Iterable


def check_param_type(param_name: str, param_type: Union[type, Iterable[type]]):
    """
    参数类型检查装饰器，在函数执行前验证参数类型（支持位置参数/关键字参数、多类型校验）
    :param param_name: 要检查的参数名
    :param param_type: 期望的参数类型（单个类型或多个类型的可迭代对象，如tuple/list）
    """
    # 优化1：统一处理多类型，将单个类型转为元组，方便后续isinstance判断
    if not isinstance(param_type, Iterable) or isinstance(param_type, type):
        param_type = (param_type,)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect

            # 解析函数签名，获取参数的位置索引（支持位置参数+关键字参数）
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            param_value = None
            param_found = False

            try:
                # 场景1：关键字参数传入
                if param_name in kwargs:
                    param_value = kwargs[param_name]
                    param_found = True
                # 场景2：位置参数传入
                else:
                    param_index = params.index(param_name)
                    if len(args) > param_index:
                        param_value = args[param_index]
                        param_found = True
                # 场景3：参数未传入，使用默认值
                if not param_found:
                    param_default = sig.parameters[param_name].default
                    if param_default is not inspect.Parameter.empty:
                        param_value = param_default
                        param_found = True
            except (ValueError, IndexError):
                raise ValueError(f"函数 {func.__name__} 中未找到参数 '{param_name}'")

            # 执行类型校验（支持None兼容：若参数值为None，直接跳过）
            if param_found and param_value is not None:
                if not isinstance(param_value, param_type):
                    expected_types_str = ", ".join([t.__name__ for t in param_type])
                    actual_type_str = type(param_value).__name__
                    raise TypeError(
                        f"错误：参数 '{param_name}' 必须是 [{expected_types_str}] 类型，实际为 [{actual_type_str}] 类型"
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator