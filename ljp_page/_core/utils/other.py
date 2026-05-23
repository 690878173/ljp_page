import warnings
from functools import wraps


def deprecated_class(msg: str):
    def decorator(cls):
        orig_init = cls.__init__
        @wraps(orig_init)
        def new_init(self, *args, **kwargs):
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            orig_init(self, *args, **kwargs)
        cls.__init__ = new_init
        return cls
    return decorator

def f_mark(desc:str = None):
    """
    继承标记装饰器
    仅做代码标注，**无任何实际业务逻辑**
    不修改原类/原方法任何行为
    """
    def wrapper(target):
        return target
    return wrapper

