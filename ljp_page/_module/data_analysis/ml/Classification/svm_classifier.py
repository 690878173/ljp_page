"""SVM 分类模型封装。"""

from __future__ import annotations

from typing import Mapping, Optional, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from ..base import BaseModel, ModelType


class SVMClassifierModel(BaseModel):
    """支持概率输出的 SVM 分类器。"""

    def __init__(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: Union[np.ndarray, pd.Series],
        random_state: int = 42,
        probability: bool = True,
    ):
        super().__init__(X, ModelType.CLASSIFICATION, random_state)
        self.y = self._convert_data(y).ravel()
        if self.y.shape[0] != self.data.shape[0]:
            raise ValueError(
                f"样本数不一致：X 有 {self.data.shape[0]} 行，y 有 {self.y.shape[0]} 行"
            )

        self.probability = bool(probability)
        self.scaler_X = StandardScaler()
        self.scaled_X: Optional[np.ndarray] = None
        self._is_scaled = True

    def preprocess(self, scale: bool = True) -> "SVMClassifierModel":
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
        probability: Optional[bool] = None,
        **kwargs,
    ) -> "SVMClassifierModel":
        """
        训练 SVM。

        常用参数：
        - `kernel="rbf" | "linear" | "poly" | "sigmoid"`
        - `C=1.0`
        - `gamma="scale"`
        """
        if probability is not None:
            self.probability = bool(probability)

        if self.scaled_X is None or self._is_scaled != bool(scale):
            self.preprocess(scale=scale)

        params = {"random_state": self.random_state, "probability": self.probability}
        params.update(kwargs)
        self.model = SVC(**params)
        self.model.fit(self.scaled_X, self.y)
        self._mark_fitted(True)
        return self

    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """预测分类结果。"""
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
            raise NotImplementedError("当前 SVM 配置不支持 predict_proba，请设置 probability=True")
        features = self._convert_data(new_data, ensure_2d=True)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )
        if self._is_scaled:
            features = self.scaler_X.transform(features)
        return self.model.predict_proba(features)

    def get_classes(self) -> np.ndarray:
        """获取类别顺序。"""
        self._check_is_fitted()
        return np.asarray(self.model.classes_)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性（仅线性核可用）。

        对线性核：取 `coef_` 绝对值均值作为重要性。
        """
        self._check_is_fitted()
        if not hasattr(self.model, "coef_"):
            raise NotImplementedError("当前核函数不支持系数解释，请使用 kernel='linear'")

        coef = np.asarray(self.model.coef_)
        importance = np.mean(np.abs(coef), axis=0)
        df = pd.DataFrame({"特征索引": np.arange(len(importance)), "重要性": importance})
        return df.sort_values("重要性", ascending=False, ignore_index=True)

    def evaluate(
        self,
        y_true: Union[np.ndarray, pd.Series],
        y_pred: Optional[Union[np.ndarray, pd.Series]] = None,
        average: str = "weighted",
        zero_division: Union[int, float, str] = 0,
    ) -> dict[str, float]:
        """分类指标评估快捷方法。"""
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
        return {
            "y": self.y,
            "probability": self.probability,
            "scaler_X": self.scaler_X,
            "scaled_X": self.scaled_X,
            "_is_scaled": self._is_scaled,
        }

    def _load_serializable_state(self, state: Mapping[str, object]) -> None:
        self.y = np.asarray(state.get("y", self.y)).ravel()
        self.probability = bool(state.get("probability", self.probability))
        scaler = state.get("scaler_X")
        self.scaler_X = scaler if scaler is not None else StandardScaler()
        self.scaled_X = state.get("scaled_X")
        self._is_scaled = bool(state.get("_is_scaled", True))


def svm_classifier_auto(
    X: Union[np.ndarray, pd.DataFrame],
    y: Union[np.ndarray, pd.Series],
    scale: bool = True,
    **kwargs,
) -> tuple[SVMClassifierModel, np.ndarray]:
    """自动训练 SVM 并返回训练集预测结果。"""
    model = SVMClassifierModel(X, y)
    model.fit(scale=scale, **kwargs)
    predictions = model.predict(X)
    return model, predictions


__all__ = ["SVMClassifierModel", "svm_classifier_auto"]
