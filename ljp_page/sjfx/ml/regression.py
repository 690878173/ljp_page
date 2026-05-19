# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    from ljp_page._data_analysis.ml.Regression import CatBoostRegressionModel as CatBoostRegressionModel
    from ljp_page._data_analysis.ml.Regression import LightGBMRegressionModel as LightGBMRegressionModel
    from ljp_page._data_analysis.ml.Regression import LinearRegressionModel as LinearRegressionModel
    from ljp_page._data_analysis.ml.Regression import RandomForestRegressionModel as RandomForestRegressionModel
    from ljp_page._data_analysis.ml.Regression import RidgeRegressionModel as RidgeRegressionModel
    from ljp_page._data_analysis.ml.Regression import XGBoostRegressionModel as XGBoostRegressionModel
    from ljp_page._data_analysis.ml.Regression import catboost_regression_auto as catboost_regression_auto
    from ljp_page._data_analysis.ml.Regression import lightgbm_regression_auto as lightgbm_regression_auto
    from ljp_page._data_analysis.ml.Regression import linear_regression_auto as linear_regression_auto
    from ljp_page._data_analysis.ml.Regression import random_forest_regression_auto as random_forest_regression_auto
    from ljp_page._data_analysis.ml.Regression import ridge_regression_auto as ridge_regression_auto
    from ljp_page._data_analysis.ml.Regression import xgboost_regression_auto as xgboost_regression_auto

__getattr__, __all__ = proxy_module_exports(
    "ljp_page._data_analysis.ml.Regression",
    [
        "LinearRegressionModel",
        "linear_regression_auto",
        "RidgeRegressionModel",
        "ridge_regression_auto",
        "RandomForestRegressionModel",
        "random_forest_regression_auto",
        "XGBoostRegressionModel",
        "xgboost_regression_auto",
        "LightGBMRegressionModel",
        "lightgbm_regression_auto",
        "CatBoostRegressionModel",
        "catboost_regression_auto",
    ],
)
