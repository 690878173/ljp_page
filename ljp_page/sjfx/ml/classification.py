# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    from ljp_page._data_analysis.ml.Classification import CatBoostClassifierModel as CatBoostClassifierModel
    from ljp_page._data_analysis.ml.Classification import LightGBMClassifierModel as LightGBMClassifierModel
    from ljp_page._data_analysis.ml.Classification import LogisticRegressionModel as LogisticRegressionModel
    from ljp_page._data_analysis.ml.Classification import RandomForestClassifierModel as RandomForestClassifierModel
    from ljp_page._data_analysis.ml.Classification import SVMClassifierModel as SVMClassifierModel
    from ljp_page._data_analysis.ml.Classification import XGBoostClassifierModel as XGBoostClassifierModel
    from ljp_page._data_analysis.ml.Classification import catboost_classifier_auto as catboost_classifier_auto
    from ljp_page._data_analysis.ml.Classification import lightgbm_classifier_auto as lightgbm_classifier_auto
    from ljp_page._data_analysis.ml.Classification import logistic_regression_auto as logistic_regression_auto
    from ljp_page._data_analysis.ml.Classification import random_forest_classifier_auto as random_forest_classifier_auto
    from ljp_page._data_analysis.ml.Classification import svm_classifier_auto as svm_classifier_auto
    from ljp_page._data_analysis.ml.Classification import xgboost_classifier_auto as xgboost_classifier_auto

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
