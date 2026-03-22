"""逻辑回归分类模型封装。"""

from __future__ import annotations

from typing import Mapping, Optional, Union

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ..base import BaseModel, ModelType


class LogisticRegressionModel(BaseModel):
    """
    逻辑回归分类模型。

    设计目标：
    1. 保持与 `LinearRegressionModel` 一致的使用体验；
    2. 充分复用 `BaseModel` 的指标与序列化能力；
    3. 作为后续新增分类模型的标准模板。
    """

    def __init__(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[np.ndarray, pd.Series],
        random_state: int = 42,
    ):
        super().__init__(X, ModelType.CLASSIFICATION, random_state)
        self.y = self._convert_data(y).ravel()
        if self.y.shape[0] != self.data.shape[0]:
            raise ValueError(
                f"样本数不一致：X 有 {self.data.shape[0]} 行，y 有 {self.y.shape[0]} 行"
            )

        self.scaler_X = StandardScaler()
        self.scaled_X: Optional[np.ndarray] = None
        self._is_scaled = True

    def preprocess(self, scale: bool = True) -> "LogisticRegressionModel":
        """特征预处理。"""
        self._is_scaled = bool(scale)
        if self._is_scaled:
            self.scaled_X = self.scaler_X.fit_transform(self.data)
        else:
            self.scaled_X = self.data.copy()
        return self

    def fit(
        self,
        scale: bool = True,
        **kwargs,
    ) -> "LogisticRegressionModel":
        """
        训练逻辑回归分类模型。

        `kwargs` 会透传给 `sklearn.linear_model.LogisticRegression`。
        常用参数示例：
        - `solver="lbfgs"` / `liblinear` / `saga`
        - `max_iter=1000`
        - `class_weight="balanced"`
        - `multi_class="auto"`
        """
        if self.scaled_X is None or self._is_scaled != bool(scale):
            self.preprocess(scale=scale)

        params = {"random_state": self.random_state}
        params.update(kwargs)
        self.model = LogisticRegression(**params)
        self.model.fit(self.scaled_X, self.y)
        self._mark_fitted(True)
        return self

    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """预测新样本类别。"""
        self._check_is_fitted()
        features = self._convert_data(new_data, ensure_2d=True)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )
        if self._is_scaled:
            features = self.scaler_X.transform(features)
        return self.model.predict(features)

    def predict_proba(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """预测类别概率。"""
        self._check_is_fitted()
        if not hasattr(self.model, "predict_proba"):
            raise NotImplementedError("当前 LogisticRegression 配置不支持 predict_proba")
        features = self._convert_data(new_data, ensure_2d=True)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )
        if self._is_scaled:
            features = self.scaler_X.transform(features)
        return self.model.predict_proba(features)

    def get_classes(self) -> np.ndarray:
        """返回类别标签顺序。"""
        self._check_is_fitted()
        return np.asarray(self.model.classes_)

    def get_coefficients(self) -> np.ndarray:
        """返回模型系数矩阵。"""
        self._check_is_fitted()
        return np.asarray(self.model.coef_)

    def get_intercept(self) -> np.ndarray:
        """返回模型截距。"""
        self._check_is_fitted()
        return np.asarray(self.model.intercept_)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        返回特征重要性。

        定义：
        - 多分类：各类别系数绝对值的均值；
        - 二分类：等价于单个类别绝对值系数。
        """
        self._check_is_fitted()
        coefs = np.asarray(self.model.coef_)
        importance = np.mean(np.abs(coefs), axis=0)
        df = pd.DataFrame(
            {
                "特征索引": np.arange(len(importance)),
                "重要性": importance,
            }
        )
        return df.sort_values("重要性", ascending=False, ignore_index=True)

    def evaluate(
        self,
        y_true: Union[np.ndarray, pd.Series],
        y_pred: Optional[Union[np.ndarray, pd.Series]] = None,
        average: str = "weighted",
        zero_division: Union[int, float, str] = 0,
    ) -> dict[str, float]:
        """
        分类评估快捷方法。

        - 若 `y_pred` 为空，则默认使用训练集预测；
        - 内部复用 `BaseModel.get_all_metrics`。
        """
        y_true_arr = np.asarray(self._convert_data(y_true)).ravel()
        y_pred_arr = (
            self.predict(self.data)
            if y_pred is None
            else np.asarray(self._convert_data(y_pred)).ravel()
        )
        return self.get_all_metrics(
            y_true=y_true_arr,
            y_pred=y_pred_arr,
            average=average,
            zero_division=zero_division,
        )

    def _get_serializable_state(self) -> dict[str, object]:
        """保存子类状态。"""
        return {
            "y": self.y,
            "scaler_X": self.scaler_X,
            "scaled_X": self.scaled_X,
            "_is_scaled": self._is_scaled,
        }

    def _load_serializable_state(self, state: Mapping[str, object]) -> None:
        """恢复子类状态。"""
        self.y = np.asarray(state.get("y", self.y)).ravel()
        scaler = state.get("scaler_X")
        self.scaler_X = scaler if scaler is not None else StandardScaler()
        self.scaled_X = state.get("scaled_X")
        self._is_scaled = bool(state.get("_is_scaled", True))


def logistic_regression_auto(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    scale: bool = True,
    **kwargs,
) -> tuple[LogisticRegressionModel, np.ndarray]:
    """
    自动训练逻辑回归并返回训练集预测标签。

    返回 `(model, predictions)`。
    """
    model = LogisticRegressionModel(X, y)
    model.fit(scale=scale, **kwargs)
    predictions = model.predict(X)
    return model, predictions


__all__ = ["LogisticRegressionModel", "logistic_regression_auto"]
