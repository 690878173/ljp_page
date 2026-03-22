"""XGBoost 回归模型封装。"""

from __future__ import annotations

from typing import Mapping, Optional, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from ..base import BaseModel, ModelType


class XGBoostRegressionModel(BaseModel):
    """XGBoost 回归器封装。"""

    def __init__(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[np.ndarray, pd.Series],
        random_state: int = 42,
    ):
        super().__init__(X, ModelType.REGRESSION, random_state)
        self.y = self._convert_data(y).ravel()
        if self.y.shape[0] != self.data.shape[0]:
            raise ValueError(
                f"样本数不一致：X 有 {self.data.shape[0]} 行，y 有 {self.y.shape[0]} 行"
            )

        self.scaler_X = StandardScaler()
        self.scaled_X: Optional[np.ndarray] = None
        self._is_scaled = False

    def preprocess(self, scale: bool = False) -> "XGBoostRegressionModel":
        """特征预处理。"""
        self._is_scaled = bool(scale)
        if self._is_scaled:
            self.scaled_X = self.scaler_X.fit_transform(self.data)
        else:
            self.scaled_X = self.data.copy()
        return self

    def fit(self, scale: bool = False, **kwargs) -> "XGBoostRegressionModel":
        """训练 XGBoost 回归模型。"""
        if self.scaled_X is None or self._is_scaled != bool(scale):
            self.preprocess(scale=scale)

        params = {
            "random_state": self.random_state,
            "objective": "reg:squarederror",
            "n_estimators": 400,
            "learning_rate": 0.05,
            "max_depth": 6,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
        }
        params.update(kwargs)
        self.model = XGBRegressor(**params)
        self.model.fit(self.scaled_X, self.y)
        self._mark_fitted(True)
        return self

    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """预测回归值。"""
        self._check_is_fitted()
        features = self._convert_data(new_data, ensure_2d=True)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )
        if self._is_scaled:
            features = self.scaler_X.transform(features)
        return self.model.predict(features)

    def get_feature_importance(self) -> pd.DataFrame:
        """获取特征重要性。"""
        self._check_is_fitted()
        importance = np.asarray(self.model.feature_importances_)
        df = pd.DataFrame({"特征索引": np.arange(len(importance)), "重要性": importance})
        return df.sort_values("重要性", ascending=False, ignore_index=True)

    def evaluate(
        self,
        y_true: Union[np.ndarray, pd.Series],
        y_pred: Optional[Union[np.ndarray, pd.Series]] = None,
    ) -> dict[str, float]:
        """回归指标评估快捷方法。"""
        y_true_arr = np.asarray(self._convert_data(y_true)).ravel()
        y_pred_arr = (
            self.predict(self.data)
            if y_pred is None
            else np.asarray(self._convert_data(y_pred)).ravel()
        )
        return self.get_all_metrics(y_true=y_true_arr, y_pred=y_pred_arr)

    def _get_serializable_state(self) -> dict[str, object]:
        return {
            "y": self.y,
            "scaler_X": self.scaler_X,
            "scaled_X": self.scaled_X,
            "_is_scaled": self._is_scaled,
        }

    def _load_serializable_state(self, state: Mapping[str, object]) -> None:
        self.y = np.asarray(state.get("y", self.y)).ravel()
        scaler = state.get("scaler_X")
        self.scaler_X = scaler if scaler is not None else StandardScaler()
        self.scaled_X = state.get("scaled_X")
        self._is_scaled = bool(state.get("_is_scaled", False))


def xgboost_regression_auto(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    scale: bool = False,
    **kwargs,
) -> tuple[XGBoostRegressionModel, np.ndarray]:
    """自动训练 XGBoost 回归并返回训练集预测值。"""
    model = XGBoostRegressionModel(X, y)
    model.fit(scale=scale, **kwargs)
    predictions = model.predict(X)
    return model, predictions


__all__ = ["XGBoostRegressionModel", "xgboost_regression_auto"]
