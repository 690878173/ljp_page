"""pandas 侧的数据工具模块。"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler


class PandasTools:
    """统一管理与 DataFrame 处理相关、但不直接属于 accessor 的工具方法。"""

    @staticmethod
    def normalize_matrix(
        data: pd.DataFrame | np.ndarray | Sequence[Sequence[Any]],
    ) -> np.ndarray:
        """将输入统一转换为二维矩阵。"""
        if isinstance(data, pd.DataFrame):
            array = data.to_numpy()
        else:
            array = np.asarray(data)

        if array.ndim != 2:
            raise ValueError(f"输入数据必须是二维矩阵，当前维度为 {array.ndim}")
        return array

    @staticmethod
    def reduce_to_2d(
        data: pd.DataFrame | np.ndarray | Sequence[Sequence[Any]],
        *,
        method: str = "pca",
        scale: bool = True,
        random_state: int = 42,
        **kwargs: Any,
    ) -> np.ndarray:
        """
        将高维数据降到二维，便于散点图等可视化场景使用。

        当前支持:
        - `pca`
        - `tsne`
        """
        matrix = PandasTools.normalize_matrix(data).astype(float)
        if matrix.shape[1] < 2:
            raise ValueError("特征维度不足 2，无法执行二维降维")

        working_matrix = matrix
        if scale:
            working_matrix = StandardScaler().fit_transform(working_matrix)

        method_name = method.lower()
        if method_name == "pca":
            model = PCA(n_components=2, random_state=random_state, **kwargs)
            return model.fit_transform(working_matrix)

        if method_name == "tsne":
            params = {"n_components": 2, "random_state": random_state}
            params.update(kwargs)
            model = TSNE(**params)
            return model.fit_transform(working_matrix)

        raise ValueError(f"不支持的降维方法：{method}")


__all__ = ["PandasTools"]
