# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    from ljp_page._data_analysis.ml.Classification.logistic_regression import LogisticRegressionModel as LogisticRegressionModel
    from ljp_page._data_analysis.ml.Classification.logistic_regression import logistic_regression_auto as logistic_regression_auto

__getattr__, __all__ = proxy_module_exports(
    "ljp_page._data_analysis.ml.Classification.logistic_regression",
    ["LogisticRegressionModel", "logistic_regression_auto"],
)
