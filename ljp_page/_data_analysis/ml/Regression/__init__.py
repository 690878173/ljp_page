# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .catboost_regression import *  # noqa: F403
    from .lightgbm_regression import *  # noqa: F403
    from .linear_regression import *  # noqa: F403
    from .random_forest_regression import *  # noqa: F403
    from .ridge_regression import *  # noqa: F403
    from .xgboost_regression import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
