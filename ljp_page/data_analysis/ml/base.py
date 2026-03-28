"""机器学习模型通用基类。"""

from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Union

import numpy as np
import pandas as pd


class ModelType(Enum):
    """模型类型枚举。"""

    CLUSTER = "cluster"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"

    @classmethod
    def from_value(cls, value: Union["ModelType", str]) -> "ModelType":
        """兼容字符串与枚举对象的统一转换。"""
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            raise ValueError(f"未知的模型类型: {value}") from exc


class MetricNames:
    """评估指标名称常量。"""

    SILHOUETTE_SCORE = "silhouette_score"
    INERTIA = "inertia"
    R2_SCORE = "r2_score"
    MSE = "mse"
    MAE = "mae"
    RMSE = "rmse"
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    EXPLAINED_VARIANCE = "explained_variance"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        """返回所有内置指标名称。"""
        return (
            cls.SILHOUETTE_SCORE,
            cls.INERTIA,
            cls.R2_SCORE,
            cls.MSE,
            cls.MAE,
            cls.RMSE,
            cls.ACCURACY,
            cls.PRECISION,
            cls.RECALL,
            cls.F1_SCORE,
            cls.EXPLAINED_VARIANCE,
        )


_METRIC_MODEL_MAPPING: dict[str, ModelType] = {
    MetricNames.SILHOUETTE_SCORE: ModelType.CLUSTER,
    MetricNames.INERTIA: ModelType.CLUSTER,
    MetricNames.R2_SCORE: ModelType.REGRESSION,
    MetricNames.MSE: ModelType.REGRESSION,
    MetricNames.MAE: ModelType.REGRESSION,
    MetricNames.RMSE: ModelType.REGRESSION,
    MetricNames.ACCURACY: ModelType.CLASSIFICATION,
    MetricNames.PRECISION: ModelType.CLASSIFICATION,
    MetricNames.RECALL: ModelType.CLASSIFICATION,
    MetricNames.F1_SCORE: ModelType.CLASSIFICATION,
    MetricNames.EXPLAINED_VARIANCE: ModelType.DIMENSIONALITY_REDUCTION,
}

_SUPPORTED_METRICS_BY_MODEL: dict[ModelType, list[str]] = {
    ModelType.CLUSTER: [MetricNames.SILHOUETTE_SCORE, MetricNames.INERTIA],
    ModelType.REGRESSION: [
        MetricNames.R2_SCORE,
        MetricNames.MSE,
        MetricNames.MAE,
        MetricNames.RMSE,
    ],
    ModelType.CLASSIFICATION: [
        MetricNames.ACCURACY,
        MetricNames.PRECISION,
        MetricNames.RECALL,
        MetricNames.F1_SCORE,
    ],
    ModelType.DIMENSIONALITY_REDUCTION: [MetricNames.EXPLAINED_VARIANCE],
}


class BaseModel(ABC):
    """
    机器学习模型通用基类。

    提供能力：
    1. 统一数据格式与基础校验；
    2. 模型训练状态管理；
    3. 常见评估指标；
    4. 模型持久化与扩展状态持久化钩子。
    """

    def __init__(
        self,
        data: Union[np.ndarray, pd.DataFrame, pd.Series],
        model_type: ModelType,
        random_state: int = 42,
    ):
        self.data = self._convert_data(data, ensure_2d=True)
        self.model_type = ModelType.from_value(model_type)
        self.random_state = int(random_state)
        self.model: Any = None
        self.is_fitted: bool = False
        self._metrics_cache: dict[str, float] = {}

    @abstractmethod
    def fit(self, **kwargs) -> "BaseModel":
        """训练模型。"""

    @abstractmethod
    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> Any:
        """预测结果。"""

    def _check_metric_support(self, metric_name: str) -> None:
        """检查当前模型类型是否支持目标指标。"""
        if metric_name not in _METRIC_MODEL_MAPPING:
            raise ValueError(f"未知的评估指标: {metric_name}")

        expected_type = _METRIC_MODEL_MAPPING[metric_name]
        if expected_type != self.model_type:
            raise TypeError(
                f"{metric_name} 仅支持 {expected_type.value} 模型，"
                f"当前模型类型为 {self.model_type.value}"
            )

    def _invalidate_metrics_cache(self) -> None:
        """清空指标缓存（模型重训后建议调用）。"""
        self._metrics_cache.clear()

    def _mark_fitted(self, fitted: bool = True) -> None:
        """更新模型训练状态。"""
        self.is_fitted = bool(fitted)
        self._invalidate_metrics_cache()

    def _check_is_fitted(self) -> None:
        """检查模型是否已完成训练。"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练，请先调用 fit() 方法")

    def _convert_data(
        self,
        data: Union[np.ndarray, pd.DataFrame, pd.Series, list],
        *,
        ensure_2d: bool = False,
    ) -> np.ndarray:
        """
        将输入数据统一转换为 numpy 数组。

        规则：
        - DataFrame/Series 取 `.values`；
        - 标量数据不允许；
        - `ensure_2d=True` 时，1 维数据自动升维为 `(-1, 1)`。
        """
        if isinstance(data, (pd.DataFrame, pd.Series)):
            array = data.values
        else:
            array = np.asarray(data)

        if array.ndim == 0:
            raise ValueError("输入数据不能是标量")

        if ensure_2d:
            if array.ndim == 1:
                array = array.reshape(-1, 1)
            elif array.ndim != 2:
                raise ValueError(f"输入数据必须是二维矩阵，当前维度: {array.ndim}")
        return array

    def _check_array_finite(self, data: np.ndarray, *, allow_nan: bool = False) -> None:
        """检查数组是否包含非法值。"""
        if not allow_nan and np.isnan(data).any():
            raise ValueError("输入数据包含 NaN，请先处理缺失值")
        if np.isinf(data).any():
            raise ValueError("输入数据包含无穷值，请先清洗数据")

    @staticmethod
    def _check_target_shape(y_true: np.ndarray, y_pred: np.ndarray) -> None:
        """校验真实值与预测值长度是否一致。"""
        if y_true.shape[0] != y_pred.shape[0]:
            raise ValueError(
                f"y_true 与 y_pred 长度不一致: {y_true.shape[0]} != {y_pred.shape[0]}"
            )

    def get_silhouette_score(
        self,
        data: Optional[Union[np.ndarray, pd.DataFrame]] = None,
        labels: Optional[Union[np.ndarray, list[int]]] = None,
    ) -> float:
        """
        计算轮廓系数（聚类模型专用）。

        注意：
        - 如果未传 `labels`，默认使用 `predict(data)` 生成；
        - 当只计算训练集指标时会使用缓存。
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.SILHOUETTE_SCORE)

        use_cache = data is None and labels is None
        cache_key = MetricNames.SILHOUETTE_SCORE
        if use_cache and cache_key in self._metrics_cache:
            return self._metrics_cache[cache_key]

        eval_data = self._convert_data(self.data if data is None else data, ensure_2d=True)
        eval_labels = (
            np.asarray(self.predict(eval_data)).ravel()
            if labels is None
            else np.asarray(labels).ravel()
        )
        if eval_data.shape[0] != eval_labels.shape[0]:
            raise ValueError(
                f"样本数与标签数不一致: {eval_data.shape[0]} != {eval_labels.shape[0]}"
            )

        unique_labels = np.unique(eval_labels)
        if unique_labels.size < 2:
            raise ValueError("聚类簇数量小于 2，无法计算 silhouette_score")

        from sklearn.metrics import silhouette_score

        score = float(silhouette_score(eval_data, eval_labels))
        if use_cache:
            self._metrics_cache[cache_key] = score
        return score

    def get_inertia(self) -> float:
        """获取 inertia（聚类模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.INERTIA)
        if hasattr(self.model, "inertia_"):
            return float(self.model.inertia_)
        raise NotImplementedError("当前模型不支持 inertia 指标")

    def get_r2_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取 R2 分数（回归模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.R2_SCORE)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import r2_score

        return float(r2_score(y_true, y_pred))

    def get_mse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取均方误差（回归模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.MSE)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import mean_squared_error

        return float(mean_squared_error(y_true, y_pred))

    def get_mae(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取平均绝对误差（回归模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.MAE)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import mean_absolute_error

        return float(mean_absolute_error(y_true, y_pred))

    def get_rmse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取均方根误差（回归模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.RMSE)
        return float(np.sqrt(self.get_mse(y_true, y_pred)))

    def get_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取准确率（分类模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.ACCURACY)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import accuracy_score

        return float(accuracy_score(y_true, y_pred))

    def get_precision(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "binary",
        zero_division: Union[int, float, str] = 0,
    ) -> float:
        """获取精确率（分类模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.PRECISION)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import precision_score

        return float(
            precision_score(y_true, y_pred, average=average, zero_division=zero_division)
        )

    def get_recall(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "binary",
        zero_division: Union[int, float, str] = 0,
    ) -> float:
        """获取召回率（分类模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.RECALL)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import recall_score

        return float(
            recall_score(y_true, y_pred, average=average, zero_division=zero_division)
        )

    def get_f1_score(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "binary",
        zero_division: Union[int, float, str] = 0,
    ) -> float:
        """获取 F1 分数（分类模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.F1_SCORE)
        y_true = np.asarray(y_true).ravel()
        y_pred = np.asarray(y_pred).ravel()
        self._check_target_shape(y_true, y_pred)

        from sklearn.metrics import f1_score

        return float(f1_score(y_true, y_pred, average=average, zero_division=zero_division))

    def get_explained_variance(self) -> float:
        """获取解释方差占比（降维模型专用）。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.EXPLAINED_VARIANCE)
        if hasattr(self.model, "explained_variance_ratio_"):
            return float(np.asarray(self.model.explained_variance_ratio_).sum())
        raise NotImplementedError("当前模型不支持 explained_variance 指标")

    def get_all_metrics(self, **kwargs) -> dict[str, float]:
        """
        批量获取当前模型支持的指标。

        参数约定：
        - 聚类：可选 `data`、`labels`；
        - 回归/分类：传入 `y_true`、`y_pred`；
        - 分类可选 `average`、`zero_division`。
        """
        self._check_is_fitted()
        metrics: dict[str, float] = {}

        y_true = kwargs.get("y_true")
        y_pred = kwargs.get("y_pred")
        average = kwargs.get("average", "binary")
        zero_division = kwargs.get("zero_division", 0)

        if self.model_type == ModelType.CLUSTER:
            try:
                metrics[MetricNames.SILHOUETTE_SCORE] = self.get_silhouette_score(
                    data=kwargs.get("data"),
                    labels=kwargs.get("labels"),
                )
            except (ValueError, NotImplementedError):
                pass
            try:
                metrics[MetricNames.INERTIA] = self.get_inertia()
            except (ValueError, NotImplementedError):
                pass

        elif self.model_type == ModelType.REGRESSION:
            if y_true is not None and y_pred is not None:
                metrics[MetricNames.R2_SCORE] = self.get_r2_score(y_true, y_pred)
                metrics[MetricNames.MSE] = self.get_mse(y_true, y_pred)
                metrics[MetricNames.MAE] = self.get_mae(y_true, y_pred)
                metrics[MetricNames.RMSE] = self.get_rmse(y_true, y_pred)

        elif self.model_type == ModelType.CLASSIFICATION:
            if y_true is not None and y_pred is not None:
                metrics[MetricNames.ACCURACY] = self.get_accuracy(y_true, y_pred)
                metrics[MetricNames.PRECISION] = self.get_precision(
                    y_true, y_pred, average=average, zero_division=zero_division
                )
                metrics[MetricNames.RECALL] = self.get_recall(
                    y_true, y_pred, average=average, zero_division=zero_division
                )
                metrics[MetricNames.F1_SCORE] = self.get_f1_score(
                    y_true, y_pred, average=average, zero_division=zero_division
                )

        elif self.model_type == ModelType.DIMENSIONALITY_REDUCTION:
            try:
                metrics[MetricNames.EXPLAINED_VARIANCE] = self.get_explained_variance()
            except (ValueError, NotImplementedError):
                pass

        return metrics

    def _get_serializable_state(self) -> dict[str, Any]:
        """
        获取子类扩展状态。

        子类可重写该方法，返回可 picklable 的状态字典。
        """
        return {}

    def _load_serializable_state(self, state: Mapping[str, Any]) -> None:
        """
        恢复子类扩展状态。

        子类可重写该方法，处理 `_get_serializable_state` 对应内容。
        """

    def save_model(self, filepath: Union[str, Path]) -> None:
        """保存模型到文件。"""
        self._check_is_fitted()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "_version": 2,
            "class_name": self.__class__.__name__,
            "model": self.model,
            "random_state": self.random_state,
            "is_fitted": self.is_fitted,
            "model_type": self.model_type.value,
            "extra_state": self._get_serializable_state(),
        }
        with path.open("wb") as f:
            pickle.dump(payload, f)

    def load_model(self, filepath: Union[str, Path]) -> "BaseModel":
        """从文件加载模型。"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")

        with path.open("rb") as f:
            payload = pickle.load(f)

        self.model = payload.get("model")
        self.random_state = int(payload.get("random_state", self.random_state))
        self.is_fitted = bool(payload.get("is_fitted", False))
        self.model_type = ModelType.from_value(payload.get("model_type", self.model_type))

        extra_state = payload.get("extra_state")
        if isinstance(extra_state, Mapping):
            self._load_serializable_state(extra_state)

        self._invalidate_metrics_cache()
        return self

    def _get_supported_metrics(self) -> list[str]:
        """返回当前模型支持的指标列表。"""
        return list(_SUPPORTED_METRICS_BY_MODEL.get(self.model_type, []))

    def get_model_info(self) -> dict[str, Any]:
        """获取模型概览信息。"""
        info: dict[str, Any] = {
            "model_class": self.__class__.__name__,
            "model_type": self.model_type.value,
            "random_state": self.random_state,
            "is_fitted": self.is_fitted,
            "data_shape": tuple(self.data.shape) if self.data is not None else None,
            "supported_metrics": self._get_supported_metrics(),
        }
        if self.model is not None:
            info["underlying_model"] = type(self.model).__name__
        return info

    def __repr__(self) -> str:
        info = self.get_model_info()
        return (
            f"{info['model_class']}("
            f"type={info['model_type']}, "
            f"is_fitted={info['is_fitted']}, "
            f"data_shape={info['data_shape']})"
        )


__all__ = ["BaseModel", "MetricNames", "ModelType"]
