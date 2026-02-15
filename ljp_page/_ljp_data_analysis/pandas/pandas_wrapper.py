from tkinter import N
from typing import Literal

import numpy as np
import pandas as pd


class _BaseAccessor:
    """
    基础访问器类，提供通用方法
    """
    def __init__(self, pandas_obj):
        self._obj: pd.DataFrame = pandas_obj

    def _help(self):
        all_members = dir(self.__class__)
        public_members = [member for member in all_members if not member.startswith('_')]
        return public_members


class Info(_BaseAccessor):
    """
    信息查看模块
    """
    def __init__(self, pandas_obj):
        super().__init__(pandas_obj)

    def summary(self,map:dict=None) -> pd.DataFrame:
        """
        快速生成数据集的统计摘要，数值列显示统计信息，非数值列显示 "-"
        :return: 包含列名、数据类型、非空数量、缺失数量、缺失占比及数值统计的 DataFrame
        """
        if map is None:
            map = {}
        else:
            map = {
            '中文名称': [map.get(col, col) for col in self._obj.columns]}

        map.update({
            "数据类型": self._obj.dtypes,
            "非空数量": self._obj.count(),
            "缺失数量": self._obj.isnull().sum(),
            "缺失占比(%)": (self._obj.isnull().mean() * 100).round(4)
        })
        summary = pd.DataFrame(map)

        df_numeric = self._obj.select_dtypes(include=['number'])
        if not df_numeric.empty:
            describe_df = df_numeric.describe().T
            for col in describe_df.columns:
                summary[col] = ""
                for idx in summary.index:
                    if idx in describe_df.index:
                        summary.at[idx, col] = describe_df.at[idx, col]
                    else:
                        summary.at[idx, col] = "-"

        summary.index.name = "列名"
        return summary

    def check_duplicates(self, subset: list | None = None, return_count: bool = True) -> int | str | None:
        """
        检查 DataFrame 中是否有重复行
        :param subset: 用于检查重复的列名列表，默认 None（检查所有列）
        :param return_count: True 返回重复值数量（int），False 返回描述性字符串
        :return: 重复值数量或描述字符串（无重复值返回 None）
        """
        dup_mask = self._obj.duplicated(subset=subset)
        if not dup_mask.any():
            return None
        dup_count = dup_mask.sum()
        return dup_count if return_count else f'共{dup_count}个重复值'


class Clean(_BaseAccessor):
    """
    数据清洗模块
    """
    def __init__(self, pandas_obj):
        super().__init__(pandas_obj)

    def get_outliers(self, col_name: str, method: str = "iqr", threshold: float = 1.5) -> pd.DataFrame:
        """
        检测异常值
        :param col_name: 要检测的列名
        :param method: 检测方法，'iqr'（四分位距法）或 'zscore'（Z-score法）
        :param threshold: 阈值，iqr 默认 1.5，zscore 默认 3
        :return: 包含异常值的 DataFrame
        """
        col_data = self._obj[col_name]
        if method == "iqr":
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            outliers_mask = (col_data < lower) | (col_data > upper)
        elif method == "zscore":
            z_scores = (col_data - col_data.mean()) / col_data.std()
            outliers_mask = abs(z_scores) > threshold
        else:
            raise ValueError(f"不支持的异常值检测方法: {method}")
        return self._obj[outliers_mask]


class Convert(_BaseAccessor):
    """
    类型转换模块
    """
    def __init__(self, pandas_obj):
        super().__init__(pandas_obj)
    
    def to_datatype(self, dic: dict):

        for col_name in dic.get('num',[]):
            self._obj[col_name] = pd.to_numeric(self._obj[col_name], errors='coerce')
        for col_name in dic.get('str',[]):
            self._obj[col_name] = self._obj[col_name].astype(str)
        for col_name in dic.get('datetime',[]):
            self._obj[col_name] = self.to_datetime(col_name)
        return self._obj


    def to_datetime(self, col_name, format='mixed', errors='coerce', inplace: bool = True):
        """
        转换指定列为 datetime 类型，支持 format='mixed' 兼容多种格式
        :param col_name: 要转换的列名，可以是单个列名或列名列表
        :param format: 时间格式，默认 'mixed'（pandas ≥ 2.0.0 支持）
        :param errors: 错误处理方式，默认 'coerce'
        :return: dataframe
        """
        col_name = col_name if isinstance(col_name, list) else [col_name]
        df_to_process = self._obj[col_name].copy() if not inplace else self._obj

        def _to_datetime(col):
            if not pd.api.types.is_datetime64_any_dtype(df_to_process[col]):
                df_to_process[col] = pd.to_datetime(df_to_process[col], format=format, errors=errors)

        for col in col_name:
            _to_datetime(col)

        return df_to_process


class Process(_BaseAccessor):
    """
    数据处理模块
    """
    def __init__(self, pandas_obj):
        super().__init__(pandas_obj)

    def sample(self, n: int | None = None, frac: float | None = None, random_state: int | None = None) -> pd.DataFrame:
        """
        随机采样
        :param n: 采样数量
        :param frac: 采样比例，与 n 二选一
        :param random_state: 随机种子，保证结果可复现
        :return: 采样后的 DataFrame
        """
        return self._obj.sample(n=n, frac=frac, random_state=random_state)


class Analysis(_BaseAccessor):
    """
    统计分析模块
    """
    def __init__(self, pandas_obj):
        super().__init__(pandas_obj)

    def corr(self, method: str | None = "pearson") -> pd.DataFrame:
        """
        自动筛选数值型列，计算相关系数矩阵，避免字符串列转换报错
        :param method: 相关系数计算方法，默认 "pearson"，支持 "spearman"、"kendall"
        :return: 数值型列的相关系数矩阵
        """
        df_numeric = self._obj.select_dtypes(include=['number'])

        if df_numeric.empty:
            raise ValueError("错误：DataFrame 中无有效数值型列，无法计算相关系数")

        corr_matrix = df_numeric.corr(method=method)
        return corr_matrix

    def stand(self, col_name: str | None = None, max_min: bool = False) -> pd.Series | pd.DataFrame:
        """
        数据标准化：支持最大最小值归一化（[0,1]区间）和Z-score标准化（均值0，标准差1）
        Parameters:
            col_name: str  目标列名
            max_min: bool  是否执行最大最小值归一化，默认False（执行Z-score标准化）
        Returns:
            pandas.Series  标准化后的列数据，保持与原数据索引对齐
        """
        s = self._obj[col_name].copy() if col_name else self._obj.copy()

        s = s.fillna(0)

        if max_min:
            min_val = s.min()
            max_val = s.max()
            k1 = min_val
            k2 = max_val - min_val
        else:
            mean_val = s.mean()
            std_val = s.std()
            k1 = mean_val
            k2 = std_val

        if (col_name and k2 != 0) or (k2.all() != 0):
            return (s - k1) / k2

        return s * 0


class Utils(_BaseAccessor):
    """
    工具方法模块
    """
    def __init__(self, pandas_obj):
        super().__init__(pandas_obj)

    @staticmethod
    def map(from_data: list, to_map: list, default = np.nan) -> np.ndarray:
        """
        条件映射：根据多个条件返回对应值
        :param from_data: 条件列表，每个元素为布尔条件
        :param to_map: 值列表，与 from_data 一一对应
        :param default: 默认值，当所有条件都不满足时返回
        :return: 映射后的数组
        """
        return np.select(from_data, to_map, default=default)

    def save(self, path: str, index: bool = False, engine: Literal["auto", "pyarrow", "fastparquet"] = "pyarrow") -> None:
        """
        保存 DataFrame 为 parquet 格式
        :param path: 保存路径
        :param index: 是否保存索引
        :param engine: 保存引擎，默认 "pyarrow"
        """
        self._obj.to_parquet(path, engine=engine, index=index)

    def get_weekday(self, datetime_col: str) -> pd.Series:
        """
        从已转换的 datetime 列中提取星期几
        :param datetime_col: 已转换为 datetime 类型的列名
        :return: 星期几（1=周一，7=周日）
        """
        if datetime_col not in self._obj.columns:
            raise ValueError(f"错误：数据中不存在列 '{datetime_col}'，请检查列名是否正确")

        if self._obj[datetime_col].dtype != 'datetime64[ns]':
            raise AttributeError(f"错误：列 '{datetime_col}' 不是 datetime 类型！请先调用 to_datetime() 转换")

        return self._obj[datetime_col].dt.dayofweek + 1


@pd.api.extensions.register_dataframe_accessor("ljp_f")
class Ljp_dataframe(Info, Clean, Convert, Process, Analysis, Utils):
    """
    自定义 DataFrame 访问器，按功能模块封装数据分析常用工具函数
    使用方式：
    - 方式1（推荐）：df.ljp_f.模块名.方法名() - 按模块分类调用，结构清晰
    - 方式2：df.ljp_f.方法名() - 直接调用所有方法，快捷方便
    
    模块列表：
    - info: 信息查看（summary, describe, check_na, check_duplicates, check）
    - clean: 数据清洗（fill_na, drop_duplicates, drop_cols, get_outliers）
    - convert: 类型转换（dtypes, auto_int, auto_types, to_datetime）
    - process: 数据处理（filter, sample, group_summary, value_counts, sort, rename_cols, select_cols, get_top_n）
    - analysis: 统计分析（corr, stand）
    - utils: 工具方法（map, save, add_weekday）
    """
    def __init__(self, pandas_obj):
        self._obj: pd.DataFrame = pandas_obj

        self.info = Info(pandas_obj)
        self.clean = Clean(pandas_obj)
        self.convert = Convert(pandas_obj)
        self.process = Process(pandas_obj)
        self.analysis = Analysis(pandas_obj)
        self.utils = Utils(pandas_obj)

    @staticmethod
    def map(from_data: list, to_map: list, default = np.nan) -> np.ndarray:
        """
        条件映射：根据多个条件返回对应值（静态方法，可直接调用）
        :param from_data: 条件列表，每个元素为布尔条件
        :param to_map: 值列表，与 from_data 一一对应
        :param default: 默认值，当所有条件都不满足时返回
        :return: 映射后的数组
        """
        return np.select(from_data, to_map, default=default)

    def help(self,mode=None) -> dict[str, list[str]]:
        """
        显示所有可用方法，按模块分类
        :return: 包含各模块方法列表的字典
        """
        if mode:
            return {
                "info": self.info._help(),
                "clean": self.clean._help(),
                "convert": self.convert._help(),
                "process": self.process._help(),
                "analysis": self.analysis._help(),
                "utils": self.utils._help()
            }
        return self._help()
