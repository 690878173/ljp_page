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
