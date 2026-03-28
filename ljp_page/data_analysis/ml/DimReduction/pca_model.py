"""PCA 降维模型封装。"""

from __future__ import annotations

from typing import Mapping, Optional, Union

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from ..base import BaseModel, ModelType


class PCAModel(BaseModel):
    """
    PCA 降维模型。

    对外约定：
    - `fit()` 训练模型；
    - `transform()` 对新样本降维；
    - `predict()` 作为 `transform()` 别名，保持基类接口统一。
    """

    def __init__(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        random_state: int = 42,
        scale: bool = True,
    ):
        super().__init__(X, ModelType.DIMENSIONALITY_REDUCTION, random_state)
        self.scale = bool(scale)
        self.scaler_X = StandardScaler()
        self.scaled_X: Optional[np.ndarray] = None
        self._is_scaled = self.scale
        self.transformed_data: Optional[np.ndarray] = None

    def preprocess(self, scale: Optional[bool] = None) -> "PCAModel":
        """预处理输入特征。"""
        use_scale = self.scale if scale is None else bool(scale)
        self._is_scaled = use_scale
        if use_scale:
            self.scaled_X = self.scaler_X.fit_transform(self.data)
        else:
            self.scaled_X = self.data.copy()
        return self

    def fit(
        self,
        n_components: Optional[Union[int, float, str]] = None,
        scale: Optional[bool] = None,
        **kwargs,
    ) -> "PCAModel":
        """训练 PCA 模型。"""
        if self.scaled_X is None or (scale is not None and self._is_scaled != bool(scale)):
            self.preprocess(scale=scale)

        params = {"random_state": self.random_state}
        if n_components is not None:
            params["n_components"] = n_components
        params.update(kwargs)

        self.model = PCA(**params)
        self.transformed_data = self.model.fit_transform(self.scaled_X)
        self._mark_fitted(True)
        return self

    def transform(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """对新样本执行降维。"""
        self._check_is_fitted()
        features = self._convert_data(new_data, ensure_2d=True)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )
        if self._is_scaled:
            features = self.scaler_X.transform(features)
        return self.model.transform(features)

    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """`transform` 别名。"""
        return self.transform(new_data)

    def fit_transform(
        self,
        n_components: Optional[Union[int, float, str]] = None,
        scale: Optional[bool] = None,
        **kwargs,
    ) -> np.ndarray:
        """训练并返回降维结果。"""
        self.fit(n_components=n_components, scale=scale, **kwargs)
        if self.transformed_data is None:
            raise RuntimeError("PCA 训练后未得到降维结果")
        return self.transformed_data

    def inverse_transform(self, reduced_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """将降维结果反变换回原特征空间。"""
        self._check_is_fitted()
        reduced = self._convert_data(reduced_data, ensure_2d=True)
        restored = self.model.inverse_transform(reduced)
        if self._is_scaled:
            restored = self.scaler_X.inverse_transform(restored)
        return restored

    def get_components(self) -> np.ndarray:
        """获取主成分矩阵。"""
        self._check_is_fitted()
        return np.asarray(self.model.components_)

    def get_explained_variance_ratio(self) -> np.ndarray:
        """获取各主成分解释方差比。"""
        self._check_is_fitted()
        return np.asarray(self.model.explained_variance_ratio_)

    def get_component_loadings(self) -> pd.DataFrame:
        """获取主成分载荷矩阵。"""
        self._check_is_fitted()
        components = self.get_components()
        n_components = components.shape[0]
        columns = [f"PC{i + 1}" for i in range(n_components)]
        return pd.DataFrame(components.T, columns=columns)

    def _get_serializable_state(self) -> dict[str, object]:
        return {
            "scale": self.scale,
            "scaler_X": self.scaler_X,
            "scaled_X": self.scaled_X,
            "_is_scaled": self._is_scaled,
            "transformed_data": self.transformed_data,
        }

    def _load_serializable_state(self, state: Mapping[str, object]) -> None:
        self.scale = bool(state.get("scale", self.scale))
        scaler = state.get("scaler_X")
        self.scaler_X = scaler if scaler is not None else StandardScaler()
        self.scaled_X = state.get("scaled_X")
        self._is_scaled = bool(state.get("_is_scaled", self.scale))
        self.transformed_data = state.get("transformed_data")


def pca_auto(
    X: Union[np.ndarray, pd.DataFrame],
    n_components: Optional[Union[int, float, str]] = None,
    scale: bool = True,
    **kwargs,
) -> tuple[PCAModel, np.ndarray]:
    """自动训练 PCA 并返回降维结果。"""
    model = PCAModel(X, scale=scale)
    transformed = model.fit_transform(n_components=n_components, scale=scale, **kwargs)
    return model, transformed


__all__ = ["PCAModel", "pca_auto"]
