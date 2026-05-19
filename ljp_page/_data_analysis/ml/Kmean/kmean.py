"""KMeans 聚类封装（工程化重构版）。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ...visualization.matplotlib import Plotter
from ..base import BaseModel, ModelType

KMethod = Literal["elbow", "silhouette", "gap"]


@dataclass(slots=True)
class KSearchResult:
    """记录最佳 K 搜索结果。"""

    method: KMethod
    k_values: list[int]
    scores: list[float]
    best_k: int
    metric_name: str
    std_values: Optional[list[float]] = None
    figure_path: Optional[Path] = None


class KMeanCluster(BaseModel):
    """
    KMeans 聚类封装。

    设计目标：
    1. 支持标准训练/预测流程；
    2. 支持自动搜索最佳 K；
    3. 支持项目内绘图能力并统一输出目录；
    4. 保留旧接口（`quick_cluster`、`kmeans_auto`）以兼容已有调用。
    """

    def __init__(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        random_state: int = 42,
        scale: bool = True,
    ):
        clean_data = self._validate_and_convert_data(data)
        super().__init__(clean_data, ModelType.CLUSTER, random_state)
        self.scale = scale
        self.scaler = StandardScaler()
        self.scaled_data: Optional[np.ndarray] = None
        self.labels: Optional[np.ndarray] = None
        self.centers: Optional[np.ndarray] = None
        self.last_search_result: Optional[KSearchResult] = None
        self._is_scaled_data = False

    @staticmethod
    def _validate_and_convert_data(data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """将输入数据统一转换为二维浮点数组，并做基础校验。"""
        if isinstance(data, pd.DataFrame):
            array = data.values
        else:
            array = np.asarray(data)

        if array.ndim != 2:
            raise ValueError(f"输入数据必须是二维矩阵，当前维度为 {array.ndim}")
        if array.shape[0] < 2:
            raise ValueError("样本数至少为 2 才能进行聚类")
        if array.shape[1] < 1:
            raise ValueError("特征数至少为 1")
        if np.isnan(array).any():
            raise ValueError("输入数据包含 NaN，请先完成缺失值处理")
        if np.isinf(array).any():
            raise ValueError("输入数据包含无穷值，请先清洗数据")

        try:
            return array.astype(np.float64, copy=False)
        except ValueError as exc:
            raise ValueError("输入数据必须可以转换为浮点数矩阵") from exc

    @staticmethod
    def _validate_k_range(
        k_range: Tuple[int, int],
        n_samples: int,
        method: KMethod,
    ) -> list[int]:
        """校验 K 搜索范围并返回离散 K 列表。"""
        if len(k_range) != 2:
            raise ValueError("k_range 必须是长度为 2 的元组，例如 (2, 10)")

        k_min, k_max = k_range
        if not isinstance(k_min, int) or not isinstance(k_max, int):
            raise TypeError("k_range 的边界必须是整数")
        if k_min < 2:
            raise ValueError("k_range 的最小 K 必须 >= 2")
        if k_min > k_max:
            raise ValueError("k_range 的最小值不能大于最大值")

        max_k = n_samples - 1 if method == "silhouette" else n_samples
        if k_max > max_k:
            raise ValueError(
                f"k_range 上限过大：当前方法 {method} 允许的最大 K 为 {max_k}，"
                f"但传入了 {k_max}"
            )

        return list(range(k_min, k_max + 1))

    @staticmethod
    def _infer_caller_base_dir() -> Path:
        """
        推断调用脚本所在目录。

        优先使用 `__main__.__file__`，失败时回退到当前工作目录。
        """
        main_module = sys.modules.get("__main__")
        main_file = getattr(main_module, "__file__", None)
        if main_file:
            return Path(main_file).resolve().parent

        argv0 = Path(sys.argv[0]) if sys.argv and sys.argv[0] else None
        if argv0 and argv0.suffix.lower() in {".py", ".pyw"} and argv0.exists():
            return argv0.resolve().parent

        return Path.cwd().resolve()

    def _resolve_output_dir(self, output_dir: Optional[Union[str, Path]]) -> Path:
        """
        解析输出目录。

        约定：未显式指定时，图像输出到“调用脚本目录/res/pt”。
        """
        if output_dir is None:
            output = self._infer_caller_base_dir() / "res" / "pt"
        else:
            output = Path(output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        return output

    def preprocess(self, scale: Optional[bool] = None) -> "KMeanCluster":
        """预处理输入数据（可选标准化）。"""
        use_scale = self.scale if scale is None else bool(scale)
        if use_scale:
            self.scaled_data = self.scaler.fit_transform(self.data)
            self._is_scaled_data = True
        else:
            self.scaled_data = self.data.copy()
            self._is_scaled_data = False
        return self

    def _ensure_preprocessed(self) -> None:
        if self.scaled_data is None:
            self.preprocess(scale=self.scale)

    def fit(
        self,
        n_clusters: Optional[int] = None,
        init: Literal["k-means++", "random"] = "k-means++",
        n_init: int = 10,
        max_iter: int = 300,
        auto_find_k: bool = False,
        k_range: Tuple[int, int] = (2, 10),
        method: KMethod = "silhouette",
        n_refs: int = 10,
        plot: bool = False,
        output_dir: Optional[Union[str, Path]] = None,
        figure_filename: Optional[str] = None,
    ) -> "KMeanCluster":
        """
        训练 KMeans 模型。

        参数说明：
        - `auto_find_k=True` 时，会先按 `method` 自动搜索最佳 K；
        - `plot=True` 时，会将搜索曲线图输出到目标目录。
        """
        self._ensure_preprocessed()

        if auto_find_k:
            n_clusters = self.find_optimal_k(
                k_range=k_range,
                method=method,
                plot=plot,
                n_refs=n_refs,
                output_dir=output_dir,
                figure_filename=figure_filename,
            )

        if n_clusters is None:
            raise ValueError("n_clusters 不能为空；或设置 auto_find_k=True 让模型自动搜索")
        if not isinstance(n_clusters, int):
            raise TypeError("n_clusters 必须是整数")
        if n_clusters < 1:
            raise ValueError("n_clusters 必须 >= 1")
        if n_clusters > self.scaled_data.shape[0]:
            raise ValueError(
                f"n_clusters 不能大于样本数（{self.scaled_data.shape[0]}）"
            )

        self.model = KMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            random_state=self.random_state,
        )
        self.labels = self.model.fit_predict(self.scaled_data)
        self.centers = self.model.cluster_centers_
        self._mark_fitted(True)
        return self

    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """预测新样本的聚类标签。"""
        self._check_is_fitted()
        features = self._validate_and_convert_data(new_data)
        if features.shape[1] != self.data.shape[1]:
            raise ValueError(
                f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {features.shape[1]}"
            )

        if self._is_scaled_data:
            features = self.scaler.transform(features)
        return self.model.predict(features)

    def get_inertia(self) -> float:
        """返回训练后模型的 inertia（簇内平方和）。"""
        self._check_is_fitted()
        return float(self.model.inertia_)

    def get_silhouette_score(
        self,
        data: Optional[Union[np.ndarray, pd.DataFrame]] = None,
        labels: Optional[Union[np.ndarray, list[int]]] = None,
    ) -> float:
        """返回当前聚类结果的轮廓系数。"""
        self._check_is_fitted()

        use_cache = data is None and labels is None
        if use_cache and "silhouette_score" in self._metrics_cache:
            return self._metrics_cache["silhouette_score"]

        if data is None:
            eval_data = self.scaled_data
        else:
            raw_data = self._validate_and_convert_data(data)
            if raw_data.shape[1] != self.data.shape[1]:
                raise ValueError(
                    f"输入特征维度不匹配：期望 {self.data.shape[1]}，实际 {raw_data.shape[1]}"
                )
            eval_data = self.scaler.transform(raw_data) if self._is_scaled_data else raw_data

        if labels is None:
            eval_labels = self.labels if data is None else self.predict(data)
        else:
            eval_labels = np.asarray(labels).ravel()

        if eval_data.shape[0] != np.asarray(eval_labels).shape[0]:
            raise ValueError(
                f"样本数与标签数不一致: {eval_data.shape[0]} != {np.asarray(eval_labels).shape[0]}"
            )
        if len(np.unique(eval_labels)) < 2:
            raise ValueError("簇数量少于 2，无法计算轮廓系数")

        score = float(silhouette_score(eval_data, eval_labels))
        if use_cache:
            self._metrics_cache["silhouette_score"] = score
        return score

    def get_cluster_centers(self, inverse_transform: bool = True) -> np.ndarray:
        """
        获取聚类中心。

        - 当训练时做了标准化且 `inverse_transform=True`，返回反标准化后的中心；
        - 否则返回模型内部中心。
        """
        self._check_is_fitted()
        if self.centers is None:
            raise ValueError("模型尚未生成聚类中心")
        if inverse_transform and self._is_scaled_data:
            return self.scaler.inverse_transform(self.centers)
        return self.centers.copy()

    def get_cluster_info(self) -> pd.DataFrame:
        """返回每个簇的样本数和占比。"""
        self._check_is_fitted()
        unique_labels, counts = np.unique(self.labels, return_counts=True)
        total = counts.sum()
        return pd.DataFrame(
            {
                "簇编号": unique_labels.astype(int),
                "样本数量": counts.astype(int),
                "占比(%)": np.round(counts / total * 100.0, 2),
            }
        ).sort_values("簇编号", ascending=True, ignore_index=True)

    def _get_serializable_state(self) -> dict[str, object]:
        """保存 KMeans 子类状态。"""
        return {
            "scale": self.scale,
            "scaler": self.scaler,
            "scaled_data": self.scaled_data,
            "labels": self.labels,
            "centers": self.centers,
            "_is_scaled_data": self._is_scaled_data,
            "last_search_result": self.last_search_result,
        }

    def _load_serializable_state(self, state: Mapping[str, object]) -> None:
        """恢复 KMeans 子类状态。"""
        self.scale = bool(state.get("scale", self.scale))
        self.scaler = state.get("scaler", StandardScaler())
        self.scaled_data = state.get("scaled_data")
        self.labels = state.get("labels")
        self.centers = state.get("centers")
        self._is_scaled_data = bool(state.get("_is_scaled_data", False))
        search_result = state.get("last_search_result")
        self.last_search_result = search_result if isinstance(search_result, KSearchResult) else None

    def find_optimal_k(
        self,
        k_range: Tuple[int, int] = (2, 10),
        method: KMethod = "elbow",
        plot: bool = True,
        n_refs: int = 10,
        output_dir: Optional[Union[str, Path]] = None,
        figure_filename: Optional[str] = None,
    ) -> int:
        """
        搜索最佳 K。

        支持三种策略：
        - `elbow`：肘部法（inertia 曲线拐点）；
        - `silhouette`：轮廓系数最大；
        - `gap`：Gap Statistic。
        """
        self._ensure_preprocessed()
        k_values = self._validate_k_range(k_range, self.scaled_data.shape[0], method)

        if method == "elbow":
            scores = self._compute_inertias(k_values)
            best_k = self._find_elbow_point(k_values, scores)
            result = KSearchResult(
                method="elbow",
                k_values=k_values,
                scores=scores,
                best_k=best_k,
                metric_name="inertia",
            )
        elif method == "silhouette":
            scores = self._compute_silhouette_scores(k_values)
            best_k = int(k_values[int(np.argmax(scores))])
            result = KSearchResult(
                method="silhouette",
                k_values=k_values,
                scores=scores,
                best_k=best_k,
                metric_name="silhouette",
            )
        elif method == "gap":
            scores, std_values = self._compute_gap_scores(k_values, n_refs=n_refs)
            best_k = self._pick_k_by_gap_rule(k_values, scores, std_values)
            result = KSearchResult(
                method="gap",
                k_values=k_values,
                scores=scores,
                std_values=std_values,
                best_k=best_k,
                metric_name="gap",
            )
        else:
            raise ValueError(f"不支持的 method: {method}")

        if plot:
            result.figure_path = self._plot_k_search_result(
                result=result,
                output_dir=output_dir,
                figure_filename=figure_filename,
            )

        self.last_search_result = result
        return result.best_k

    def plot_elbow(
        self,
        k_range: Tuple[int, int] = (2, 10),
        output_dir: Optional[Union[str, Path]] = None,
        figure_filename: Optional[str] = None,
    ) -> Path:
        """专门绘制肘部图，并返回图片路径。"""
        self._ensure_preprocessed()
        best_k = self.find_optimal_k(
            k_range=k_range,
            method="elbow",
            plot=True,
            output_dir=output_dir,
            figure_filename=figure_filename,
        )
        if self.last_search_result is None or self.last_search_result.figure_path is None:
            raise RuntimeError("肘部图生成失败")
        # best_k 变量保留用于强调本次绘图对应的最佳 K
        _ = best_k
        return self.last_search_result.figure_path

    def plot_clusters(
        self,
        feature_indices: Optional[Tuple[int, int]] = None,
        title: str = "KMeans 聚类结果",
        output_dir: Optional[Union[str, Path]] = None,
        figure_filename: str = "kmeans_clusters.png",
    ) -> Path:
        """绘制二维聚类散点图（高维时可指定两个特征索引）。"""
        self._check_is_fitted()

        n_features = self.scaled_data.shape[1]
        if feature_indices is None:
            if n_features < 2:
                raise ValueError("特征维度不足 2，无法绘制二维聚类图")
            x_idx, y_idx = 0, 1
        else:
            x_idx, y_idx = feature_indices
            if x_idx == y_idx:
                raise ValueError("feature_indices 中两个索引不能相同")
            if not (0 <= x_idx < n_features and 0 <= y_idx < n_features):
                raise ValueError(
                    f"feature_indices 越界，当前有效索引范围为 [0, {n_features - 1}]"
                )

        output = self._resolve_output_dir(output_dir)
        save_path = output / figure_filename

        plotter = Plotter(theme="report")
        _, ax = plotter.scatter(
            x=self.scaled_data[:, x_idx].tolist(),
            y=self.scaled_data[:, y_idx].tolist(),
            title=title,
            xlabel=f"特征 {x_idx}",
            ylabel=f"特征 {y_idx}",
            show=False,
            grid=False,
            c=self.labels,
            cmap="tab10",
            s=65,
            alpha=0.78,
        )

        centers = self.centers[:, [x_idx, y_idx]]
        ax.scatter(
            centers[:, 0],
            centers[:, 1],
            c="red",
            marker="X",
            s=220,
            linewidths=1.2,
            edgecolors="black",
            label="聚类中心",
            zorder=10,
        )
        ax.legend(loc="best")

        plotter.figure_manager.save(save_path)
        plotter.close()
        return save_path

    def _compute_inertias(self, k_values: list[int]) -> list[float]:
        """计算每个 K 对应的 inertia。"""
        inertias: list[float] = []
        for k in k_values:
            model = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            model.fit(self.scaled_data)
            inertias.append(float(model.inertia_))
        return inertias

    def _compute_silhouette_scores(self, k_values: list[int]) -> list[float]:
        """计算每个 K 对应的轮廓系数。"""
        scores: list[float] = []
        for k in k_values:
            model = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = model.fit_predict(self.scaled_data)
            scores.append(float(silhouette_score(self.scaled_data, labels)))
        return scores

    def _compute_gap_scores(
        self,
        k_values: list[int],
        n_refs: int,
    ) -> tuple[list[float], list[float]]:
        """计算 Gap Statistic。"""
        if n_refs < 2:
            raise ValueError("n_refs 必须 >= 2")

        rng = np.random.default_rng(self.random_state)
        data_min = self.scaled_data.min(axis=0)
        data_max = self.scaled_data.max(axis=0)

        gap_scores: list[float] = []
        std_values: list[float] = []
        for k in k_values:
            model = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            model.fit(self.scaled_data)
            inertia_real = model.inertia_

            ref_inertias = []
            for _ in range(n_refs):
                ref_data = rng.uniform(
                    low=data_min,
                    high=data_max,
                    size=self.scaled_data.shape,
                )
                ref_model = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
                ref_model.fit(ref_data)
                ref_inertias.append(ref_model.inertia_)

            log_ref = np.log(ref_inertias)
            gap_scores.append(float(np.mean(log_ref) - np.log(inertia_real)))
            std_values.append(float(np.std(log_ref, ddof=0)))
        return gap_scores, std_values

    @staticmethod
    def _find_elbow_point(k_values: list[int], inertias: list[float]) -> int:
        """
        使用“首尾连线最大垂距”法定位拐点。

        该方法比简单二阶差分更稳健，对单调下降曲线较可靠。
        """
        if len(k_values) == 1:
            return int(k_values[0])

        x = np.asarray(k_values, dtype=np.float64)
        y = np.asarray(inertias, dtype=np.float64)

        first = np.array([x[0], y[0]], dtype=np.float64)
        last = np.array([x[-1], y[-1]], dtype=np.float64)
        line = last - first
        norm = np.linalg.norm(line)

        if norm == 0:
            return int(k_values[0])

        distances = []
        for xi, yi in zip(x, y):
            point = np.array([xi, yi], dtype=np.float64)
            # 2D 向量叉积的绝对值等价于平行四边形面积，除以底边得到垂距。
            distance = abs(np.cross(line, point - first)) / norm
            distances.append(distance)

        return int(k_values[int(np.argmax(distances))])

    @staticmethod
    def _pick_k_by_gap_rule(
        k_values: list[int],
        gap_scores: list[float],
        std_values: list[float],
    ) -> int:
        """按 Gap 论文中的一标准差规则选择 K。"""
        for idx in range(len(k_values) - 1):
            if gap_scores[idx] >= gap_scores[idx + 1] - std_values[idx + 1]:
                return int(k_values[idx])
        return int(k_values[int(np.argmax(gap_scores))])

    @staticmethod
    def _default_figure_name(method: KMethod) -> str:
        mapping = {
            "elbow": "kmeans_elbow_curve.png",
            "silhouette": "kmeans_silhouette_curve.png",
            "gap": "kmeans_gap_curve.png",
        }
        return mapping[method]

    def _plot_k_search_result(
        self,
        result: KSearchResult,
        output_dir: Optional[Union[str, Path]],
        figure_filename: Optional[str],
    ) -> Path:
        """使用项目绘图库绘制 K 搜索曲线图。"""
        output = self._resolve_output_dir(output_dir)
        filename = figure_filename or self._default_figure_name(result.method)
        save_path = output / filename

        plotter = Plotter(theme="report")
        x = result.k_values
        y = result.scores

        if result.method == "silhouette":
            _, ax = plotter.bar(
                x=x,
                y=y,
                title="KMeans 最佳 K 搜索（轮廓系数）",
                xlabel="K 值",
                ylabel="Silhouette Score",
                show=False,
                grid=True,
                colors=["#4A90E2"] * len(x),
            )
        elif result.method == "gap":
            _, ax = plotter.line(
                x=x,
                y=y,
                title="KMeans 最佳 K 搜索（Gap Statistic）",
                xlabel="K 值",
                ylabel="Gap Score",
                show=False,
                grid=True,
                colors=["#4A90E2"],
            )
            if result.std_values is not None:
                ax.errorbar(
                    x,
                    y,
                    yerr=result.std_values,
                    fmt="none",
                    ecolor="#2D3A4B",
                    capsize=4,
                    linewidth=1.2,
                    alpha=0.8,
                )
        else:
            _, ax = plotter.line(
                x=x,
                y=y,
                title="KMeans 最佳 K 搜索（肘部法）",
                xlabel="K 值",
                ylabel="Inertia",
                show=False,
                grid=True,
                colors=["#4A90E2"],
            )

        best_idx = result.k_values.index(result.best_k)
        best_y = result.scores[best_idx]
        ax.axvline(
            x=result.best_k,
            color="#D0021B",
            linestyle="--",
            linewidth=1.6,
            label=f"最佳 K = {result.best_k}",
        )
        ax.scatter([result.best_k], [best_y], color="#D0021B", s=85, zorder=6)
        ax.legend(loc="best")

        plotter.figure_manager.save(save_path)
        plotter.close()
        return save_path

    @staticmethod
    def quick_cluster(
        data: Union[np.ndarray, pd.DataFrame],
        k_range: Tuple[int, int] = (2, 10),
        method: KMethod = "silhouette",
        plot: bool = True,
        random_state: int = 42,
        scale: bool = True,
        output_dir: Optional[Union[str, Path]] = None,
        figure_filename: Optional[str] = None,
        plot_clusters: Optional[bool] = None,
    ) -> Tuple["KMeanCluster", int]:
        """
        快速聚类：自动找 K + 训练。

        返回 `(clusterer, best_k)`。
        """
        clusterer = KMeanCluster(data=data, random_state=random_state, scale=scale)
        best_k = clusterer.find_optimal_k(
            k_range=k_range,
            method=method,
            plot=plot,
            output_dir=output_dir,
            figure_filename=figure_filename,
        )
        clusterer.fit(n_clusters=best_k)

        should_plot_clusters = (
            (clusterer.data.shape[1] >= 2 and plot)
            if plot_clusters is None
            else plot_clusters
        )
        if should_plot_clusters and clusterer.data.shape[1] >= 2:
            clusterer.plot_clusters(output_dir=output_dir)

        return clusterer, best_k


def kmeans_auto(
    data: Union[np.ndarray, pd.DataFrame],
    k_range: Tuple[int, int] = (2, 10),
    method: KMethod = "silhouette",
    plot: bool = True,
    random_state: int = 42,
    scale: bool = True,
    output_dir: Optional[Union[str, Path]] = None,
    figure_filename: Optional[str] = None,
) -> Tuple[np.ndarray, int, KMeanCluster]:
    """
    自动执行 KMeans 聚类。

    返回 `(labels, best_k, clusterer)`。
    """
    clusterer, best_k = KMeanCluster.quick_cluster(
        data=data,
        k_range=k_range,
        method=method,
        plot=plot,
        random_state=random_state,
        scale=scale,
        output_dir=output_dir,
        figure_filename=figure_filename,
    )
    return clusterer.labels.copy(), best_k, clusterer


KmeanCluster = KMeanCluster

__all__ = ["KSearchResult", "KMeanCluster", "KmeanCluster", "kmeans_auto"]
