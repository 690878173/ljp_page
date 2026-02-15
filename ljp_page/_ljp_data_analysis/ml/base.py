"""
通用模型基类
生成时间: 02-02-11-10-00
"""

from abc import ABC, abstractmethod
from typing import Union, Optional, Any, Literal
from enum import Enum
import numpy as np
import pandas as pd
import pickle
from pathlib import Path


class ModelType(Enum):
    """模型类型枚举"""
    CLUSTER = 'cluster'
    REGRESSION = 'regression'
    CLASSIFICATION = 'classification'
    DIMENSIONALITY_REDUCTION = 'dimensionality_reduction'

class MetricNames:
    """评估指标名称常量类"""
    SILHOUETTE_SCORE = 'silhouette_score'
    INERTIA = 'inertia'
    R2_SCORE = 'r2_score'
    MSE = 'mse'
    MAE = 'mae'
    RMSE = 'rmse'
    ACCURACY = 'accuracy'
    PRECISION = 'precision'
    RECALL = 'recall'
    F1_SCORE = 'f1_score'
    EXPLAINED_VARIANCE = 'explained_variance'


class BaseModel(ABC):
    """
    机器学习模型通用基类
    提供数据管理、模型保存/加载、评估指标等通用功能
    """
    
    def __init__(self, data: Union[np.ndarray, pd.DataFrame], 
                 model_type: ModelType,
                 random_state: int = 42):
        """
        初始化基类
        :param data: 输入数据，支持 numpy 数组或 DataFrame
        :param model_type: 模型类型，用于确定支持的评估指标
        :param random_state: 随机种子，保证结果可复现
        """
        self.data = data.values if isinstance(data, pd.DataFrame) else data
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.is_fitted = False
        self._metrics_cache = {}
        
    @abstractmethod
    def fit(self, **kwargs) -> 'BaseModel':
        """
        训练模型的抽象方法，子类必须实现
        :param kwargs: 模型特定的参数
        :return: self
        """
        pass
    
    @abstractmethod
    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> Any:
        """
        预测的抽象方法，子类必须实现
        :param new_data: 新数据
        :return: 预测结果
        """
        pass
    
    def _check_metric_support(self, metric_name: str) -> None:
        """
        检查当前模型类型是否支持指定的评估指标
        :param metric_name: 评估指标名称
        """
        metric_mapping = {
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
        
        if metric_name not in metric_mapping:
            raise ValueError(f'未知的评估指标: {metric_name}')
        
        if metric_mapping[metric_name] != self.model_type:
            raise TypeError(
                f'{metric_name} 指标仅支持 {metric_mapping[metric_name].value} 模型，'
                f'当前模型类型为 {self.model_type.value}'
            )
    
    def get_silhouette_score(self) -> float:
        """
        获取轮廓系数（聚类模型专用）
        :return: 轮廓系数，范围 [-1, 1]，越接近 1 表示聚类效果越好
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.SILHOUETTE_SCORE)
        
        if MetricNames.SILHOUETTE_SCORE in self._metrics_cache:
            return self._metrics_cache[MetricNames.SILHOUETTE_SCORE]
        
        from sklearn.metrics import silhouette_score
        score = silhouette_score(self.data, self.predict(self.data))
        self._metrics_cache[MetricNames.SILHOUETTE_SCORE] = score
        return score
    
    def get_inertia(self) -> float:
        """
        获取惯性值（聚类模型专用）
        :return: 惯性值（样本到最近聚类中心的平方距离之和）
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.INERTIA)
        
        if hasattr(self.model, 'inertia_'):
            return self.model.inertia_
        raise NotImplementedError('当前模型不支持 inertia 指标')
    
    def get_r2_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        获取 R² 决定系数（回归模型专用）
        :param y_true: 真实值
        :param y_pred: 预测值
        :return: R² 分数，范围 (-∞, 1]，越接近 1 表示拟合越好
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.R2_SCORE)
        
        from sklearn.metrics import r2_score
        return r2_score(y_true, y_pred)
    
    def get_mse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        获取均方误差（回归模型专用）
        :param y_true: 真实值
        :param y_pred: 预测值
        :return: 均方误差
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.MSE)
        
        from sklearn.metrics import mean_squared_error
        return mean_squared_error(y_true, y_pred)
    
    def get_mae(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        获取平均绝对误差（回归模型专用）
        :param y_true: 真实值
        :param y_pred: 预测值
        :return: 平均绝对误差
        """
        self._check_is_fitted()
        self._check_metric_support('mae')
        
        from sklearn.metrics import mean_absolute_error
        return mean_absolute_error(y_true, y_pred)
    
    def get_rmse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        获取均方根误差（回归模型专用）
        :param y_true: 真实值
        :param y_pred: 预测值
        :return: 均方根误差
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.RMSE)
        
        return np.sqrt(self.get_mse(y_true, y_pred))
    
    def get_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        获取准确率（分类模型专用）
        :param y_true: 真实标签
        :param y_pred: 预测标签
        :return: 准确率，范围 [0, 1]
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.ACCURACY)
        
        from sklearn.metrics import accuracy_score
        return accuracy_score(y_true, y_pred)
    
    def get_precision(self, y_true: np.ndarray, y_pred: np.ndarray, average: str = 'binary') -> float:
        """
        获取精确率（分类模型专用）
        :param y_true: 真实标签
        :param y_pred: 预测标签
        :param average: 多分类时的平均方式
        :return: 精确率
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.PRECISION)
        
        from sklearn.metrics import precision_score
        return precision_score(y_true, y_pred, average=average)
    
    def get_recall(self, y_true: np.ndarray, y_pred: np.ndarray, average: str = 'binary') -> float:
        """
        获取召回率（分类模型专用）
        :param y_true: 真实标签
        :param y_pred: 预测标签
        :param average: 多分类时的平均方式
        :return: 召回率
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.RECALL)
        
        from sklearn.metrics import recall_score
        return recall_score(y_true, y_pred, average=average)
    
    def get_f1_score(self, y_true: np.ndarray, y_pred: np.ndarray, average: str = 'binary') -> float:
        """
        获取 F1 分数（分类模型专用）
        :param y_true: 真实标签
        :param y_pred: 预测标签
        :param average: 多分类时的平均方式
        :return: F1 分数
        """
        self._check_is_fitted()
        self._check_metric_support('f1_score')
        
        from sklearn.metrics import f1_score
        return f1_score(y_true, y_pred, average=average)
    
    def get_explained_variance(self) -> float:
        """
        获取解释方差比（降维模型专用）
        :return: 解释方差比
        """
        self._check_is_fitted()
        self._check_metric_support(MetricNames.EXPLAINED_VARIANCE)
        
        if hasattr(self.model, 'explained_variance_ratio_'):
            return self.model.explained_variance_ratio_.sum()
        raise NotImplementedError('当前模型不支持 explained_variance 指标')
    
    def get_all_metrics(self, **kwargs) -> dict:
        """
        获取当前模型类型支持的所有评估指标
        :param kwargs: 需要真实值和预测值的指标，传入 y_true 和 y_pred
        :return: 包含所有可用指标的字典
        """
        self._check_is_fitted()
        
        metrics = {}
        y_true = 'y_true'
        y_pred = 'y_pred'
        if self.model_type == ModelType.CLUSTER:
            try:
                metrics[MetricNames.SILHOUETTE_SCORE] = self.get_silhouette_score()
            except (ValueError, NotImplementedError):
                pass
            try:
                metrics[MetricNames.INERTIA] = self.get_inertia()
            except (ValueError, NotImplementedError):
                pass
        
        elif self.model_type == ModelType.REGRESSION:
            if y_true in kwargs and y_pred in kwargs:
                metrics[MetricNames.R2_SCORE] = self.get_r2_score(kwargs[y_true], kwargs[y_pred])
                metrics[MetricNames.MSE] = self.get_mse(kwargs[y_true], kwargs[y_pred])
                metrics[MetricNames.MAE] = self.get_mae(kwargs[y_true], kwargs[y_pred])
                metrics[MetricNames.RMSE] = self.get_rmse(kwargs[y_true], kwargs[y_pred])
        
        elif self.model_type == ModelType.CLASSIFICATION:
            if y_true in kwargs and y_pred in kwargs:
                metrics[MetricNames.ACCURACY] = self.get_accuracy(kwargs[y_true], kwargs[y_pred])
                try:
                    metrics[MetricNames.PRECISION] = self.get_precision(kwargs[y_true], kwargs[y_pred])
                    metrics[MetricNames.RECALL] = self.get_recall(kwargs[y_true], kwargs[y_pred])
                    metrics[MetricNames.F1_SCORE] = self.get_f1_score(kwargs[y_true], kwargs[y_pred])
                except (ValueError, NotImplementedError):
                    pass
        
        elif self.model_type == ModelType.DIMENSIONALITY_REDUCTION:
            try:
                metrics[MetricNames.EXPLAINED_VARIANCE] = self.get_explained_variance()
            except (ValueError, NotImplementedError):
                pass
        
        return metrics
    
    def _check_is_fitted(self) -> None:
        """
        检查模型是否已训练
        """
        if not self.is_fitted:
            raise ValueError('模型尚未训练，请先调用 fit() 方法')
    
    def _convert_data(self, data: Union[np.ndarray, pd.DataFrame, pd.Series]) -> np.ndarray:
        """
        统一转换数据格式为 numpy 数组
        :param data: 输入数据
        :return: numpy 数组
        """
        if isinstance(data, (pd.DataFrame, pd.Series)):
            return data.values
        return data
    
    def save_model(self, filepath: Union[str, Path]) -> None:
        """
        保存模型到文件
        :param filepath: 保存路径
        """
        self._check_is_fitted()
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'random_state': self.random_state,
                'is_fitted': self.is_fitted,
                'model_type': self.model_type
            }, f)
    
    def load_model(self, filepath: Union[str, Path]) -> 'BaseModel':
        """
        从文件加载模型
        :param filepath: 模型文件路径
        :return: self
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f'模型文件不存在: {filepath}')
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            self.model = model_data['model']
            self.random_state = model_data.get('random_state', self.random_state)
            self.is_fitted = model_data.get('is_fitted', False)
            self.model_type = model_data.get('model_type', self.model_type)
        
        return self
    
    def get_model_info(self) -> dict:
        """
        获取模型基本信息
        :return: 包含模型信息的字典
        """
        info = {
            'model_class': self.__class__.__name__,
            'model_type': self.model_type.value,
            'random_state': self.random_state,
            'is_fitted': self.is_fitted,
            'data_shape': self.data.shape if self.data is not None else None,
            'supported_metrics': self._get_supported_metrics()
        }
        
        if self.model is not None:
            info['underlying_model'] = type(self.model).__name__
        
        return info
    
    def _get_supported_metrics(self) -> list:
        """
        获取当前模型类型支持的评估指标列表
        :return: 支持的指标名称列表
        """
        metrics_map = {
            ModelType.CLUSTER: [MetricNames.SILHOUETTE_SCORE, MetricNames.INERTIA],
            ModelType.REGRESSION: [MetricNames.R2_SCORE, MetricNames.MSE, MetricNames.MAE, MetricNames.RMSE],
            ModelType.CLASSIFICATION: [MetricNames.ACCURACY, MetricNames.PRECISION, MetricNames.RECALL, MetricNames.F1_SCORE],
            ModelType.DIMENSIONALITY_REDUCTION: [MetricNames.EXPLAINED_VARIANCE]
        }
        return metrics_map.get(self.model_type, [])
    
    def __repr__(self) -> str:
        """
        模型的字符串表示
        """
        info = self.get_model_info()
        return f"{info['model_class']}(type={info['model_type']}, is_fitted={info['is_fitted']}, data_shape={info['data_shape']})"
