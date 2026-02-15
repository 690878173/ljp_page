"""
线性回归模型
生成时间: 02-02-11-05-30
"""

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from typing import Union
import numpy as np
import pandas as pd
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from ..base import BaseModel, ModelType


class LinearRegressionModel(BaseModel):
    """
    线性回归模型类
    继承自 BaseModel，支持回归相关的评估指标
    """
    
    def __init__(self, X: Union[np.ndarray, pd.DataFrame], 
                 y: Union[np.ndarray, pd.Series], 
                 random_state: int = 42):
        """
        初始化线性回归模型
        :param X: 特征数据，可以是 numpy 数组或 DataFrame
        :param y: 目标变量，可以是 numpy 数组或 Series
        :param random_state: 随机种子，保证结果可复现
        """
        super().__init__(X, ModelType.REGRESSION, random_state)
        self.y = y.values if isinstance(y, (pd.DataFrame, pd.Series)) else y
        self.scaler_X = StandardScaler()
        self.scaled_X = None
        
    def preprocess(self, scale: bool = True) -> 'LinearRegressionModel':
        """
        特征预处理
        :param scale: 是否标准化特征
        :return: self
        """
        if scale:
            self.scaled_X = self.scaler_X.fit_transform(self.data)
        else:
            self.scaled_X = self.data.copy()
        return self
    
    def fit(self, scale: bool = True, **kwargs) -> 'LinearRegressionModel':
        """
        训练线性回归模型
        :param scale: 是否标准化特征
        :param kwargs: 其他参数（兼容 fit_intercept 等 sklearn 参数）
        :return: self
        """
        if self.scaled_X is None:
            self.preprocess(scale)
            
        self.model = LinearRegression(**kwargs)
        self.model.fit(self.scaled_X, self.y)
        self.is_fitted = True
        return self
    
    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        预测新数据的目标值
        :param new_data: 新特征数据
        :return: 预测的目标值
        """
        self._check_is_fitted()
        
        new_data_array = self._convert_data(new_data)
        scaled_new_data = self.scaler_X.transform(new_data_array)
        return self.model.predict(scaled_new_data)
    
    def get_coefficients(self) -> np.ndarray:
        """
        获取回归系数
        :return: 回归系数数组
        """
        self._check_is_fitted()
        return self.model.coef_
    
    def get_intercept(self) -> float:
        """
        获取截距
        :return: 截距值
        """
        self._check_is_fitted()
        return self.model.intercept_
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        获取特征重要性（基于回归系数的绝对值）
        :return: 包含特征名称和重要性的 DataFrame
        """
        self._check_is_fitted()
        
        importance = pd.DataFrame({
            '特征索引': range(len(self.model.coef_)),
            '回归系数': self.model.coef_,
            '绝对值系数': np.abs(self.model.coef_)
        }).sort_values('绝对值系数', ascending=False)
        
        return importance


def linear_regression_auto(X: Union[np.ndarray, pd.DataFrame], 
                          y: Union[np.ndarray, pd.Series],
                          scale: bool = True,
                          **kwargs) -> tuple:
    """
    自动线性回归的便捷函数
    :param X: 特征数据
    :param y: 目标变量
    :param scale: 是否标准化特征
    :param kwargs: 其他模型参数
    :return: (模型对象, 预测值)
    """
    model = LinearRegressionModel(X, y)
    model.fit(scale=scale, **kwargs)
    predictions = model.predict(X)
    return model, predictions
