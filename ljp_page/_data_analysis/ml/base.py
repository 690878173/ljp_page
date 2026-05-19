# 生成时间：04-08-16-20-59
"""机器学习模型通用基类。"""

from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler


class ModelType(str, Enum):
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

_SUPPORTED_METRICS_BY_MODEL: dict[ModelType, tuple[str, ...]] = {
    ModelType.CLUSTER: (MetricNames.SILHOUETTE_SCORE, MetricNames.INERTIA),
    ModelType.REGRESSION: (
        MetricNames.R2_SCORE,
        MetricNames.MSE,
        MetricNames.MAE,
        MetricNames.RMSE,
    ),
    ModelType.CLASSIFICATION: (
        MetricNames.ACCURACY,
        MetricNames.PRECISION,
        MetricNames.RECALL,
        MetricNames.F1_SCORE,
    ),
    ModelType.DIMENSIONALITY_REDUCTION: (MetricNames.EXPLAINED_VARIANCE,),
}

_SCALER_MAPPING = {
    "standard": StandardScaler,
    "minmax": MinMaxScaler,
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
        model_type: Union[ModelType, str],
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
        """清空指标缓存。"""
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
        data: Union[np.ndarray, pd.DataFrame, pd.Series, list, tuple],
        *,
        ensure_2d: bool = False,
    ) -> np.ndarray:
        """
        将输入数据统一转换为 numpy 数组。

        规则：
        - DataFrame/Series 转为 `.to_numpy()`；
        - 标量数据不允许；
        - `ensure_2d=True` 时，1 维数据自动升维为 `(-1, 1)`。
        """
        if isinstance(data, (pd.DataFrame, pd.Series)):
            array = data.to_numpy()
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

    def _prepare_target_arrays(
        self,
        y_true: Union[np.ndarray, pd.Series, list],
        y_pred: Union[np.ndarray, pd.Series, list],
    ) -> tuple[np.ndarray, np.ndarray]:
        """统一处理监督学习指标的输入。"""
        y_true_arr = self._convert_data(y_true).ravel()
        y_pred_arr = self._convert_data(y_pred).ravel()
        self._check_target_shape(y_true_arr, y_pred_arr)
        return y_true_arr, y_pred_arr

    def _compute_supervised_metric(
        self,
        metric_name: str,
        scorer: Callable[..., float],
        y_true: Union[np.ndarray, pd.Series, list],
        y_pred: Union[np.ndarray, pd.Series, list],
        **kwargs: Any,
    ) -> float:
        """复用监督学习指标的公共校验与计算流程。"""
        self._check_is_fitted()
        self._check_metric_support(metric_name)
        y_true_arr, y_pred_arr = self._prepare_target_arrays(y_true, y_pred)
        return float(scorer(y_true_arr, y_pred_arr, **kwargs))

    def _get_cached_metric(
        self,
        metric_name: str,
        use_cache: bool,
        calculator: Callable[[], float],
    ) -> float:
        """统一处理训练态指标缓存。"""
        if use_cache and metric_name in self._metrics_cache:
            return self._metrics_cache[metric_name]

        value = float(calculator())
        if use_cache:
            self._metrics_cache[metric_name] = value
        return value

    def get_silhouette_score(
        self,
        data: Optional[Union[np.ndarray, pd.DataFrame]] = None,
        labels: Optional[Union[np.ndarray, list[int]]] = None,
    ) -> float:
        """
        计算轮廓系数。

        注意：
        - 如果未传 `labels`，默认使用 `predict(data)` 生成；
        - 当只计算训练集指标时会使用缓存。
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.SILHOUETTE_SCORE)
        use_cache = data is None and labels is None

        def calculate() -> float:
            eval_data = self._convert_data(
                self.data if data is None else data,
                ensure_2d=True,
            )
            eval_labels = (
                np.asarray(self.predict(eval_data)).ravel()
                if labels is None
                else np.asarray(labels).ravel()
            )
            if eval_data.shape[0] != eval_labels.shape[0]:
                raise ValueError(
                    f"样本数与标签数不一致: {eval_data.shape[0]} != {eval_labels.shape[0]}"
                )

            if np.unique(eval_labels).size < 2:
                raise ValueError("聚类簇数量小于 2，无法计算 silhouette_score")
            return float(silhouette_score(eval_data, eval_labels))

        return self._get_cached_metric(
            MetricNames.SILHOUETTE_SCORE,
            use_cache=use_cache,
            calculator=calculate,
        )

    def get_inertia(self) -> float:
        """获取 inertia。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.INERTIA)
        if hasattr(self.model, "inertia_"):
            return float(self.model.inertia_)
        raise NotImplementedError("当前模型不支持 inertia 指标")

    def get_r2_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取 R2 分数。"""
        return self._compute_supervised_metric(
            MetricNames.R2_SCORE,
            r2_score,
            y_true,
            y_pred,
        )

    def get_mse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取均方误差。"""
        return self._compute_supervised_metric(
            MetricNames.MSE,
            mean_squared_error,
            y_true,
            y_pred,
        )

    def get_mae(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取平均绝对误差。"""
        return self._compute_supervised_metric(
            MetricNames.MAE,
            mean_absolute_error,
            y_true,
            y_pred,
        )

    def get_rmse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取均方根误差。"""
        return float(np.sqrt(self.get_mse(y_true, y_pred)))

    def get_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """获取准确率。"""
        return self._compute_supervised_metric(
            MetricNames.ACCURACY,
            accuracy_score,
            y_true,
            y_pred,
        )

    def get_precision(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "binary",
        zero_division: Union[int, float, str] = 0,
    ) -> float:
        """获取精确率。"""
        return self._compute_supervised_metric(
            MetricNames.PRECISION,
            precision_score,
            y_true,
            y_pred,
            average=average,
            zero_division=zero_division,
        )

    def get_recall(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "binary",
        zero_division: Union[int, float, str] = 0,
    ) -> float:
        """获取召回率。"""
        return self._compute_supervised_metric(
            MetricNames.RECALL,
            recall_score,
            y_true,
            y_pred,
            average=average,
            zero_division=zero_division,
        )

    def get_f1_score(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "binary",
        zero_division: Union[int, float, str] = 0,
    ) -> float:
        """获取 F1 分数。"""
        return self._compute_supervised_metric(
            MetricNames.F1_SCORE,
            f1_score,
            y_true,
            y_pred,
            average=average,
            zero_division=zero_division,
        )

    def get_explained_variance(self) -> float:
        """获取解释方差占比。"""
        self._check_is_fitted()
        self._check_metric_support(MetricNames.EXPLAINED_VARIANCE)
        if hasattr(self.model, "explained_variance_ratio_"):
            return float(np.asarray(self.model.explained_variance_ratio_).sum())
        raise NotImplementedError("当前模型不支持 explained_variance 指标")

    def get_all_metrics(self, **kwargs: Any) -> dict[str, float]:
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
            for metric_name, getter in (
                (
                    MetricNames.SILHOUETTE_SCORE,
                    lambda: self.get_silhouette_score(
                        data=kwargs.get("data"),
                        labels=kwargs.get("labels"),
                    ),
                ),
                (MetricNames.INERTIA, self.get_inertia),
            ):
                try:
                    metrics[metric_name] = getter()
                except (ValueError, NotImplementedError):
                    continue

        elif self.model_type == ModelType.REGRESSION and y_true is not None and y_pred is not None:
            metrics[MetricNames.R2_SCORE] = self.get_r2_score(y_true, y_pred)
            metrics[MetricNames.MSE] = self.get_mse(y_true, y_pred)
            metrics[MetricNames.MAE] = self.get_mae(y_true, y_pred)
            metrics[MetricNames.RMSE] = self.get_rmse(y_true, y_pred)

        elif self.model_type == ModelType.CLASSIFICATION and y_true is not None and y_pred is not None:
            metrics[MetricNames.ACCURACY] = self.get_accuracy(y_true, y_pred)
            metrics[MetricNames.PRECISION] = self.get_precision(
                y_true,
                y_pred,
                average=average,
                zero_division=zero_division,
            )
            metrics[MetricNames.RECALL] = self.get_recall(
                y_true,
                y_pred,
                average=average,
                zero_division=zero_division,
            )
            metrics[MetricNames.F1_SCORE] = self.get_f1_score(
                y_true,
                y_pred,
                average=average,
                zero_division=zero_division,
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

        子类可重写该方法，返回可 pickle 的状态字典。
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
        with path.open("wb") as file:
            pickle.dump(payload, file)

    def load_model(self, filepath: Union[str, Path]) -> "BaseModel":
        """从文件加载模型。"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")

        with path.open("rb") as file:
            payload = pickle.load(file)

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
        return list(_SUPPORTED_METRICS_BY_MODEL.get(self.model_type, ()))

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


class TabularData:
    """
    通用表格数据容器类。

    适用于分类、回归、多模态、关联分析、建模等结构化数据场景。
    """

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        filepath: Optional[Union[str, Path]] = None,
    ):
        self.df: Optional[pd.DataFrame] = None
        self.filepath: Optional[Path] = None

        self.X: Optional[np.ndarray] = None
        self.y: Optional[np.ndarray] = None
        self.feature_names: list[str] = []

        self.X_train: Optional[np.ndarray] = None
        self.X_val: Optional[np.ndarray] = None
        self.X_test: Optional[np.ndarray] = None
        self.y_train: Optional[np.ndarray] = None
        self.y_val: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None

        self.scaler: Optional[Union[StandardScaler, MinMaxScaler]] = None
        self.X_train_scaled: Optional[np.ndarray] = None
        self.X_val_scaled: Optional[np.ndarray] = None
        self.X_test_scaled: Optional[np.ndarray] = None

        if df is not None:
            self.df = df.copy()
        elif filepath is not None:
            self.load(filepath)

    def _require_dataframe(self) -> pd.DataFrame:
        """确保原始数据已经加载。"""
        if self.df is None:
            raise ValueError("尚未加载数据，请先传入 df 或调用 load()")
        return self.df

    def _require_features(self) -> None:
        """确保已经指定特征。"""
        if self.X is None:
            raise ValueError("尚未指定特征列，请先调用 set_Xy()")

    def _require_split(self) -> None:
        """确保已经完成数据切分。"""
        if self.X_train is None:
            raise ValueError("尚未完成数据切分，请先调用 split()")

    def _reset_split_cache(self) -> None:
        """当原始特征变化时，清空旧的切分和缩放结果。"""
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        self._reset_scaled_cache()

    def _reset_scaled_cache(self) -> None:
        """清空缩放器与缩放结果。"""
        self.scaler = None
        self.X_train_scaled = None
        self.X_val_scaled = None
        self.X_test_scaled = None

    @staticmethod
    def _normalize_feature_names(X_cols: Union[str, Sequence[str]]) -> list[str]:
        """统一特征列参数格式。"""
        if isinstance(X_cols, str):
            return [X_cols]
        return list(X_cols)

    @staticmethod
    def _resolve_stratify_labels(
        y: Optional[np.ndarray],
        stratify: bool,
    ) -> Optional[np.ndarray]:
        """
        解析是否启用分层抽样。

        对连续型目标值自动回退为普通随机划分，避免回归场景误用分层采样。
        """
        if y is None or stratify is False:
            return None

        labels = np.asarray(y).ravel()
        unique_labels, counts = np.unique(labels, return_counts=True)
        if unique_labels.size <= 1 or counts.min() < 2:
            return None

        is_float = np.issubdtype(labels.dtype, np.floating)
        if is_float and unique_labels.size > min(labels.size // 5 + 1, 20):
            return None

        return labels

    def load(self, filepath: Union[str, Path]) -> "TabularData":
        """自动加载 csv 或 Excel。"""
        path = Path(filepath)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            self.df = pd.read_csv(path)
        elif suffix in {".xlsx", ".xls"}:
            self.df = pd.read_excel(path)
        else:
            raise ValueError(f"暂不支持的文件格式: {suffix}")

        self.filepath = path
        self.X = None
        self.y = None
        self.feature_names = []
        self._reset_split_cache()
        return self

    def set_Xy(
        self,
        X_cols: Union[str, Sequence[str]],
        y_col: Optional[str] = None,
    ) -> "TabularData":
        """手动指定特征列和标签列。"""
        df = self._require_dataframe()
        self.feature_names = self._normalize_feature_names(X_cols)
        self.X = df.loc[:, self.feature_names].to_numpy()
        self.y = None if y_col is None else df.loc[:, y_col].to_numpy()
        self._reset_split_cache()
        return self

    def split(
        self,
        test_size: float = 0.2,
        val_size: float = 0.1,
        random_state: int = 42,
        stratify: bool = True,
    ) -> "TabularData":
        """划分训练集、验证集、测试集。"""
        self._require_features()
        if not 0 < test_size < 1:
            raise ValueError("test_size 必须在 0 到 1 之间")
        if not 0 <= val_size < 1:
            raise ValueError("val_size 必须在 0 到 1 之间")
        if test_size + val_size >= 1:
            raise ValueError("test_size 与 val_size 之和必须小于 1")

        stratify_labels = self._resolve_stratify_labels(self.y, stratify)
        train_val_ratio = val_size / (1 - test_size) if val_size > 0 else 0.0

        if self.y is None:
            X_train_val, X_test = train_test_split(
                self.X,
                test_size=test_size,
                random_state=random_state,
            )
            if val_size > 0:
                X_train, X_val = train_test_split(
                    X_train_val,
                    test_size=train_val_ratio,
                    random_state=random_state,
                )
            else:
                X_train, X_val = X_train_val, None

            self.X_train, self.X_val, self.X_test = X_train, X_val, X_test
            self.y_train, self.y_val, self.y_test = None, None, None
            self._reset_scaled_cache()
            return self

        X_train_val, X_test, y_train_val, y_test = train_test_split(
            self.X,
            self.y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_labels,
        )

        if val_size > 0:
            val_stratify = (
                self._resolve_stratify_labels(y_train_val, True)
                if stratify_labels is not None
                else None
            )
            X_train, X_val, y_train, y_val = train_test_split(
                X_train_val,
                y_train_val,
                test_size=train_val_ratio,
                random_state=random_state,
                stratify=val_stratify,
            )
        else:
            X_train, X_val = X_train_val, None
            y_train, y_val = y_train_val, None

        self.X_train, self.X_val, self.X_test = X_train, X_val, X_test
        self.y_train, self.y_val, self.y_test = y_train, y_val, y_test
        self._reset_scaled_cache()
        return self

    def scale(self, method: str = "standard") -> "TabularData":
        """对切分后的特征执行标准化或归一化。"""
        self._require_split()
        if method not in _SCALER_MAPPING:
            raise ValueError("method 仅支持 'standard' 或 'minmax'")

        self.scaler = _SCALER_MAPPING[method]()
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_val_scaled = (
            None if self.X_val is None else self.scaler.transform(self.X_val)
        )
        self.X_test_scaled = self.scaler.transform(self.X_test)
        return self

    def get_train(self, scaled: bool = True) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """获取训练集。"""
        features = self.X_train_scaled if scaled and self.X_train_scaled is not None else self.X_train
        return features, self.y_train

    def get_val(self, scaled: bool = True) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """获取验证集。"""
        features = self.X_val_scaled if scaled and self.X_val_scaled is not None else self.X_val
        return features, self.y_val

    def get_test(self, scaled: bool = True) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """获取测试集。"""
        features = self.X_test_scaled if scaled and self.X_test_scaled is not None else self.X_test
        return features, self.y_test

    def __len__(self) -> int:
        return 0 if self.df is None else len(self.df)


__all__ = ["BaseModel", "MetricNames", "ModelType", "TabularData"]
