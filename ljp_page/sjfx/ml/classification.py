# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core.utils._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    pass

__getattr__, __all__ = proxy_module_exports(
    "ljp_page._data_analysis.ml.Classification",
    [
        "LogisticRegressionModel",
        "logistic_regression_auto",
        "SVMClassifierModel",
        "svm_classifier_auto",
        "RandomForestClassifierModel",
        "random_forest_classifier_auto",
        "XGBoostClassifierModel",
        "xgboost_classifier_auto",
        "LightGBMClassifierModel",
        "lightgbm_classifier_auto",
        "CatBoostClassifierModel",
        "catboost_classifier_auto",
    ],
)
