"""Ridge 回归模型封装。"""

from __future__ import annotations

from typing import Mapping, Union

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from ..base import BaseModel, ModelType


class RidgeRegressionModel(BaseModel):
    """L2 正则化线性回归。"""

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
        self.scaled_X: Union[np.ndarray, None] = None
        self._is_scaled = True

    def preprocess(self, scale: bool = True) -> "RidgeRegressionModel":
        """特征预处理。"""
        self._is_scaled = bool(scale)
        if self._is_scaled:
            self.scaled_X = self.scaler_X.fit_transform(self.data)
        else:
            self.scaled_X = self.data.copy()
        return self

    def fit(self, scale: bool = True, **kwargs) -> "RidgeRegressionModel":
        """训练 Ridge 回归模型。"""
        if self.scaled_X is None or self._is_scaled != bool(scale):
            self.preprocess(scale=scale)

        params = {"random_state": self.random_state}
        params.update(kwargs)
        self.model = Ridge(**params)
        self.model.fit(self.scaled_X, self.y)
        self._mark_fitted(True)
        return self

    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """预测新样本。"""
        self._check_is_fitted()
        features = self._convert_data(new_data, ensure_2d=True)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )
        if self._is_scaled:
            features = self.scaler_X.transform(features)
        return self.model.predict(features)

    def get_coefficients(self) -> np.ndarray:
        """获取回归系数。"""
        self._check_is_fitted()
        return np.asarray(self.model.coef_)

    def get_intercept(self) -> float:
        """获取截距。"""
        self._check_is_fitted()
        return float(self.model.intercept_)

    def get_feature_importance(self) -> pd.DataFrame:
        """获取特征重要性（基于系数绝对值）。"""
        self._check_is_fitted()
        coefs = np.asarray(self.model.coef_)
        df = pd.DataFrame(
            {
                "特征索引": np.arange(len(coefs)),
                "回归系数": coefs,
                "绝对值系数": np.abs(coefs),
            }
        )
        return df.sort_values("绝对值系数", ascending=False, ignore_index=True)

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
        self._is_scaled = bool(state.get("_is_scaled", True))


def ridge_regression_auto(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    scale: bool = True,
    **kwargs,
) -> tuple[RidgeRegressionModel, np.ndarray]:
    """自动训练 Ridge 并返回训练集预测值。"""
    model = RidgeRegressionModel(X, y)
    model.fit(scale=scale, **kwargs)
    predictions = model.predict(X)
    return model, predictions


__all__ = ["RidgeRegressionModel", "ridge_regression_auto"]
