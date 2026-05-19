from typing import Literal

import numpy as np
import pandas as pd


CorrelationMethod = Literal["pearson", "spearman", "kendall"]
OutlierMethod = Literal["iqr", "zscore"]
ParquetEngine = Literal["auto", "pyarrow", "fastparquet"]


class _BaseAccessor:
    """基础访问器类，封装公共校验和帮助方法。"""

    def __init__(self, pandas_obj: pd.DataFrame):
        self._obj = pandas_obj

    def _help(self) -> list[str]:
        """返回当前模块公开的方法名。"""
        methods: list[str] = []
        for name in dir(self.__class__):
            if name.startswith("_"):
                continue
            member = getattr(self.__class__, name)
            if callable(member):
                methods.append(name)
        return sorted(methods)

    def _ensure_columns(self, columns: str | list[str]) -> list[str]:
        """校验列名是否存在，并统一返回列表。"""
        column_names = [columns] if isinstance(columns, str) else list(columns)
        missing_columns = [name for name in column_names if name not in self._obj.columns]
        if missing_columns:
            missing_text = "、".join(missing_columns)
            raise ValueError(f"错误：数据中不存在列 {missing_text}，请检查列名是否正确")
        return column_names


class Info(_BaseAccessor):
    """信息查看模块。"""

    def summary(self, column_map: dict[str, str] | None = None) -> pd.DataFrame:
        """
        快速生成数据集摘要。

        数值列会附带 describe 统计结果，非数值列对应统计位显示为 "-".
        """
        summary_df = pd.DataFrame(index=self._obj.columns)

        if column_map:
            summary_df["中文名称"] = [column_map.get(col, col) for col in self._obj.columns]

        summary_df["数据类型"] = self._obj.dtypes.astype(str)
        summary_df["非空数量"] = self._obj.count()
        summary_df["缺失数量"] = self._obj.isna().sum()
        summary_df["缺失占比(%)"] = (self._obj.isna().mean() * 100).round(4)

        numeric_stats = self._obj.select_dtypes(include=["number"]).describe().T
        if not numeric_stats.empty:
            summary_df = summary_df.join(numeric_stats, how="left")
            stat_columns = list(numeric_stats.columns)
            summary_df[stat_columns] = summary_df[stat_columns].astype(object)
            summary_df[stat_columns] = summary_df[stat_columns].where(
                summary_df[stat_columns].notna(),
                "-",
            )

        summary_df.index.name = "列名"
        return summary_df

    def check_duplicates(
        self,
        subset: str | list[str] | None = None,
        return_count: bool = True,
    ) -> int | str | None:
        """检查 DataFrame 中是否存在重复记录。"""
        if subset is not None:
            self._ensure_columns(subset)

        duplicate_mask = self._obj.duplicated(subset=subset)
        duplicate_count = int(duplicate_mask.sum())
        if duplicate_count == 0:
            return None

        if return_count:
            return duplicate_count
        return f"共 {duplicate_count} 条重复记录"

    def value_counts(self,columns: list[str] | None = None) -> dict:
        value_counts = {}
        for column in columns:
            counts = self._obj[column].value_counts().sort_values()
            value_counts[column] = [counts.index,counts.values]
        return value_counts



class Clean(_BaseAccessor):
    """数据清洗模块。"""

    def get_outliers(
        self,
        col_name: str,
        method: OutlierMethod = "iqr",
        threshold: float | None = None,
    ) -> pd.DataFrame:
        """检测指定数值列中的异常值。"""
        self._ensure_columns(col_name)

        col_data = self._obj[col_name]
        if not pd.api.types.is_numeric_dtype(col_data):
            raise TypeError(f"错误：列 '{col_name}' 不是数值类型，无法执行异常值检测")

        if method == "iqr":
            effective_threshold = 1.5 if threshold is None else threshold
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - effective_threshold * iqr
            upper = q3 + effective_threshold * iqr
            outliers_mask = (col_data < lower) | (col_data > upper)
        elif method == "zscore":
            effective_threshold = 3.0 if threshold is None else threshold
            std = col_data.std()
            if pd.isna(std) or std == 0:
                return self._obj.iloc[0:0].copy()
            z_scores = (col_data - col_data.mean()) / std
            outliers_mask = z_scores.abs() > effective_threshold
        else:
            raise ValueError(f"错误：不支持的异常值检测方法 {method}")

        return self._obj.loc[outliers_mask.fillna(False)]


class Convert(_BaseAccessor):
    """类型转换模块。"""

    def to_datatype(self, mapping: dict[str, list[str]] | None = None) -> pd.DataFrame:
        """
        按分组批量转换列类型。

        支持的键:
        - "num": 转数值类型
        - "str": 转字符串类型
        - "datetime": 转时间类型
        """
        if not mapping:
            return self._obj

        for col_name in mapping.get("num", []):
            self._ensure_columns(col_name)
            self._obj[col_name] = pd.to_numeric(self._obj[col_name], errors="coerce")

        for col_name in mapping.get("str", []):
            self._ensure_columns(col_name)
            self._obj[col_name] = self._obj[col_name].astype(str)

        datetime_columns = mapping.get("datetime", [])
        if datetime_columns:
            self.to_datetime(datetime_columns, inplace=True)

        return self._obj

    def to_datetime(
        self,
        col_name: str | list[str],
        format: str | None = "mixed",
        errors: Literal["raise", "coerce", "ignore"] = "coerce",
        inplace: bool = True,
    ) -> pd.DataFrame:
        """
        转换指定列为 datetime 类型。

        `format="mixed"` 依赖 pandas 2.x，可兼容多种时间格式。
        """
        column_names = self._ensure_columns(col_name)
        target_df = self._obj if inplace else self._obj.copy()

        for column in column_names:
            if not pd.api.types.is_datetime64_any_dtype(target_df[column]):
                target_df[column] = pd.to_datetime(
                    target_df[column],
                    format=format,
                    errors=errors,
                )

        return target_df


class Process(_BaseAccessor):
    """数据处理模块。"""

    def sample(
        self,
        n: int | None = None,
        frac: float | None = None,
        random_state: int | None = None,
    ) -> pd.DataFrame:
        """随机抽样。"""
        return self._obj.sample(n=n, frac=frac, random_state=random_state)


class Analysis(_BaseAccessor):
    """统计分析模块。"""

    def corr(self, method: CorrelationMethod = "pearson") -> pd.DataFrame:
        """自动筛选数值列并计算相关系数矩阵。"""
        numeric_df = self._obj.select_dtypes(include=["number"])
        if numeric_df.empty:
            raise ValueError("错误：DataFrame 中没有有效数值列，无法计算相关系数")
        return numeric_df.corr(method=method)

    def stand(self, col_name: str | None = None, max_min: bool = False) -> pd.Series | pd.DataFrame:
        """
        标准化数值数据。

        - `col_name` 有值时，仅处理单列并返回 Series
        - `col_name` 为空时，只处理全部数值列并返回 DataFrame
        """
        if col_name is not None:
            self._ensure_columns(col_name)
            numeric_series = pd.to_numeric(self._obj[col_name], errors="coerce")
            return self._scale_series(numeric_series, max_min=max_min)

        numeric_df = self._obj.select_dtypes(include=["number"]).copy()
        if numeric_df.empty:
            raise ValueError("错误：DataFrame 中没有可标准化的数值列")

        for column in numeric_df.columns:
            numeric_df[column] = self._scale_series(numeric_df[column], max_min=max_min)
        return numeric_df

    @staticmethod
    def _scale_series(series: pd.Series, max_min: bool = False) -> pd.Series:
        """对单列数值做标准化，保留原始缺失值。"""
        result = pd.to_numeric(series, errors="coerce").astype("float64")
        valid_values = result.dropna()
        if valid_values.empty:
            return result

        if max_min:
            base_value = valid_values.min()
            divisor = valid_values.max() - base_value
        else:
            base_value = valid_values.mean()
            divisor = valid_values.std()

        if pd.isna(divisor) or divisor == 0:
            zero_series = pd.Series(0.0, index=series.index, name=series.name, dtype="float64")
            zero_series[result.isna()] = np.nan
            return zero_series

        return (result - base_value) / divisor


class Utils(_BaseAccessor):
    """工具方法模块。"""

    @staticmethod
    def map(from_data: list, to_map: list, default=np.nan) -> np.ndarray:
        """条件映射。"""
        return np.select(from_data, to_map, default=default)

    def save(
        self,
        path: str,
        index: bool = False,
        engine: ParquetEngine = "pyarrow",
    ) -> None:
        """将 DataFrame 保存为 parquet 文件。"""
        self._obj.to_parquet(path, engine=engine, index=index)

    def get_weekday(self, datetime_col: str) -> pd.Series:
        """从 datetime 列中提取星期几，返回 1 到 7。"""
        self._ensure_columns(datetime_col)

        if not pd.api.types.is_datetime64_any_dtype(self._obj[datetime_col]):
            raise AttributeError(
                f"错误：列 '{datetime_col}' 不是 datetime 类型，请先调用 to_datetime() 转换",
            )

        return self._obj[datetime_col].dt.dayofweek + 1


@pd.api.extensions.register_dataframe_accessor("ljp_f")
class Ljp_dataframe:
    """
    DataFrame 访问器。

    支持两种调用方式:
    - `df.ljp_f.info.summary()`：按模块调用，结构更清晰
    - `df.ljp_f.summary()`：直接快捷调用，兼容原有使用习惯
    """

    _accessor_classes = {
        "info": Info,
        "clean": Clean,
        "convert": Convert,
        "process": Process,
        "analysis": Analysis,
        "utils": Utils,
    }

    def __init__(self, pandas_obj: pd.DataFrame):
        self._obj = pandas_obj
        self._accessors = {
            name: accessor_class(pandas_obj)
            for name, accessor_class in self._accessor_classes.items()
        }

        for name, accessor in self._accessors.items():
            setattr(self, name, accessor)

        self._method_map = self._build_method_map()

    def _build_method_map(self) -> dict[str, _BaseAccessor]:
        """建立平铺方法名到模块实例的映射，便于快捷调用。"""
        method_map: dict[str, _BaseAccessor] = {}

        for accessor in self._accessors.values():
            for method_name in accessor._help():
                if method_name in method_map:
                    raise AttributeError(f"错误：访问器方法名冲突 '{method_name}'")
                method_map[method_name] = accessor

        return method_map

    def __getattr__(self, name: str):
        """将未命中的公开方法委托到具体模块。"""
        if name.startswith("_"):
            raise AttributeError(name)

        accessor = self._method_map.get(name)
        if accessor is None:
            raise AttributeError(f"'Ljp_dataframe' 对象没有属性 '{name}'")

        return getattr(accessor, name)

    def __dir__(self) -> list[str]:
        """补充自动补全列表，方便在交互环境中查看方法。"""
        return sorted(set(super().__dir__()) | set(self._accessors) | set(self._method_map))

    def help(self, mode: bool | None = None) -> dict[str, list[str]] | list[str]:
        """查看全部可用方法，支持分组和扁平两种展示形式。"""
        if mode:
            return {
                name: accessor._help()
                for name, accessor in self._accessors.items()
            }

        return ["help", *sorted(self._method_map)]
