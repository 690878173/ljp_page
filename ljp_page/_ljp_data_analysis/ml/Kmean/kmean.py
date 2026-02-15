from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt
from typing import Literal, Optional, Tuple, Union
import pandas as pd
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from..base import BaseModel, ModelType


class KmeanCluster(BaseModel):
    """
    K-means 聚类通用类，支持快速聚类和最佳 K 值确定
    继承自 BaseModel 基类
    """
    
    def __init__(self, data: Union[np.ndarray, pd.DataFrame], random_state: int = 42):
        """
        初始化 K-means 聚类器
        :param data: 输入数据，可以是 numpy 数组或 DataFrame
        :param random_state: 随机种子，保证结果可复现
        """
        super().__init__(data, ModelType.CLUSTER, random_state)
        self.model = KMeans
        self.scaler = StandardScaler()
        self.scaled_data = None
        self.labels = None
        self.centers = None
        
    def preprocess(self, scale: bool = True) -> 'KmeanCluster':
        """
        数据预处理
        :param scale: 是否标准化数据
        :return: self
        """
        if scale:
            self.scaled_data = self.scaler.fit_transform(self.data)
        else:
            self.scaled_data = self.data.copy()
        return self
    
    def fit(self, n_clusters: int, init: Literal['k-means++', 'random'] = 'k-means++',
            n_init: int = 10, max_iter: int = 300) -> 'KmeanCluster':
        """
        训练 K-means 模型
        :param n_clusters: 聚类数量 K
        :param init: 初始化方法，'k-means++' 或 'random'
        :param n_init: 运行 k-means 算法的次数，选择最好的结果
        :param max_iter: 最大迭代次数
        :return: self
        """
        if self.scaled_data is None:
            self.preprocess()
            
        self.model = KMeans(
            n_clusters=n_clusters,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            random_state=self.random_state
        )
        self.labels = self.model.fit_predict(self.scaled_data)
        self.centers = self.model.cluster_centers_
        self.is_fitted = True
        return self
    
    def predict(self, new_data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        预测新数据的聚类标签
        :param new_data: 新数据
        :return: 预测的标签
        """
        self._check_is_fitted()
        
        if isinstance(new_data, pd.DataFrame):
            new_data = new_data.values
            
        scaled_new_data = self.scaler.transform(new_data)
        return self.model.predict(scaled_new_data)
    
    def get_inertia(self) -> float:
        """
        获取模型的 inertia（样本到最近聚类中心的平方距离之和）
        :return: inertia 值
        """
        self._check_is_fitted()
        return self.model.inertia_
    
    def get_cluster_centers(self) -> np.ndarray:
        """
        获取聚类中心
        :return: 聚类中心坐标
        """
        self._check_is_fitted()
        return self.scaler.inverse_transform(self.centers) if hasattr(self.scaler, 'scale_') else self.centers
    
    def get_cluster_info(self) -> pd.DataFrame:
        """
        获取各簇的统计信息
        :return: 包含各簇数量、占比的 DataFrame
        """
        if self.labels is None:
            raise ValueError('模型尚未训练，请先调用 fit() 方法')
            
        unique_labels, counts = np.unique(self.labels, return_counts=True)
        total = len(self.labels)
        
        info = pd.DataFrame({
            '簇编号': unique_labels,
            '样本数量': counts,
            '占比(%)': (counts / total * 100).round(2)
        })
        
        return info
    
    def find_optimal_k(self, k_range: Tuple[int, int] = (2, 10),
                      method: Literal['elbow', 'silhouette', 'gap'] = 'elbow',
                      plot: bool = True) -> int:
        """
        寻找最佳 K 值
        :param k_range: K 值搜索范围，如 (2, 10) 表示搜索 2 到 9
        :param method: 选择方法：'elbow'（肘部法）、'silhouette'（轮廓系数）、'gap'（Gap统计量）
        :param plot: 是否绘制可视化图表
        :return: 最佳 K 值
        """
        k_min, k_max = k_range
        k_values = range(k_min, k_max + 1)
        
        if self.scaled_data is None:
            self.preprocess()
            
        if method == 'elbow':
            return self._find_k_by_elbow(k_values, plot)
        elif method == 'silhouette':
            return self._find_k_by_silhouette(k_values, plot)
        elif method == 'gap':
            return self._find_k_by_gap(k_values, plot)
        else:
            raise ValueError(f'不支持的 method: {method}')
    
    def _find_k_by_elbow(self, k_values: range, plot: bool = True) -> int:
        """
        使用肘部法寻找最佳 K 值
        :param k_values: K 值范围
        :param plot: 是否绘制图表
        :return: 最佳 K 值
        """
        inertias = []
        
        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans.fit(self.scaled_data)
            inertias.append(kmeans.inertia_)
        
        if plot:
            plt.figure(figsize=(10, 6))
            plt.plot(k_values, inertias, 'bo-', linewidth=2, markersize=8)
            plt.xlabel('K 值', fontsize=12)
            plt.ylabel('Inertia (平方误差和)', fontsize=12)
            plt.title('肘部法 - 寻找最佳 K 值', fontsize=14, fontweight='bold')
            plt.grid(False)
            
            best_k = self._find_elbow_point(k_values, inertias)
            plt.axvline(x=best_k, color='r', linestyle='--', linewidth=2, label=f'最佳 K 值 = {best_k}')
            plt.legend(fontsize=12)
            plt.tight_layout()
            plt.savefig('j:/ljp_page/ljp_page/_ljp_applications/pc/res/pt/1_肘部法寻找最佳K值.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return self._find_elbow_point(k_values, inertias)
    
    def _find_elbow_point(self, k_values: range, inertias: list) -> int:
        """
        通过计算距离变化率寻找肘部点
        """
        x = np.array(k_values)
        y = np.array(inertias)
        
        first_point = np.array([x[0], y[0]])
        last_point = np.array([x[-1], y[-1]])
        
        distances = []
        for i in range(len(x)):
            point = np.array([x[i], y[i]])
            distance = np.abs(np.cross(last_point - first_point, point - first_point)) / np.linalg.norm(last_point - first_point)
            distances.append(distance)
        
        return int(k_values[np.argmax(distances)])
    
    def _find_k_by_silhouette(self, k_values: range, plot: bool = True) -> int:
        """
        使用轮廓系数寻找最佳 K 值
        :param k_values: K 值范围
        :param plot: 是否绘制图表
        :return: 最佳 K 值
        """
        silhouette_scores = []
        
        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = kmeans.fit_predict(self.scaled_data)
            score = silhouette_score(self.scaled_data, labels)
            silhouette_scores.append(score)
        
        best_k = int(k_values[np.argmax(silhouette_scores)])
        
        if plot:
            plt.figure(figsize=(10, 6))
            plt.bar(k_values, silhouette_scores, color='skyblue', edgecolor='navy', linewidth=1.5)
            plt.xlabel('K 值', fontsize=12)
            plt.ylabel('轮廓系数', fontsize=12)
            plt.title('轮廓系数法 - 寻找最佳 K 值', fontsize=14, fontweight='bold')
            plt.axvline(x=best_k, color='r', linestyle='--', linewidth=2, label=f'最佳 K 值 = {best_k}')
            plt.legend(fontsize=12)
            plt.grid(False)
            plt.tight_layout()
            plt.savefig('j:/ljp_page/ljp_page/_ljp_applications/pc/res/pt/2_轮廓系数法寻找最佳K值.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return best_k
    
    def _find_k_by_gap(self, k_values: range, plot: bool = True, n_refs: int = 10) -> int:
        """
        使用 Gap 统计量寻找最佳 K 值
        :param k_values: K 值范围
        :param plot: 是否绘制图表
        :param n_refs: 生成参考数据集的数量
        :return: 最佳 K 值
        """
        gap_values = []
        std_values = []
        
        for k in k_values:
            kmeans_real = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans_real.fit(self.scaled_data)
            inertia_real = kmeans_real.inertia_
            
            inertia_refs = []
            for _ in range(n_refs):
                ref_data = np.random.uniform(
                    low=self.scaled_data.min(axis=0),
                    high=self.scaled_data.max(axis=0),
                    size=self.scaled_data.shape
                )
                kmeans_ref = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
                kmeans_ref.fit(ref_data)
                inertia_refs.append(kmeans_ref.inertia_)
            
            gap = np.mean(np.log(inertia_refs)) - np.log(inertia_real)
            gap_values.append(gap)
            std_values.append(np.std(np.log(inertia_refs)))
        
        best_k = int(k_values[0])
        for i in range(len(k_values) - 1):
            if gap_values[i] >= gap_values[i + 1] - std_values[i + 1]:
                best_k = int(k_values[i])
                break
        else:
            best_k = int(k_values[np.argmax(gap_values)])
        
        if plot:
            plt.figure(figsize=(10, 6))
            plt.errorbar(k_values, gap_values, yerr=std_values, fmt='bo-', 
                        linewidth=2, markersize=8, capsize=5, capthick=2)
            plt.xlabel('K 值', fontsize=12)
            plt.ylabel('Gap 统计量', fontsize=12)
            plt.title('Gap 统计量法 - 寻找最佳 K 值', fontsize=14, fontweight='bold')
            plt.axvline(x=best_k, color='r', linestyle='--', linewidth=2, label=f'最佳 K 值 = {best_k}')
            plt.legend(fontsize=12)
            plt.grid(False)
            plt.tight_layout()
            plt.savefig('j:/ljp_page/ljp_page/_ljp_applications/pc/res/pt/3_Gap统计量法寻找最佳K值.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        return best_k
    
    def plot_clusters(self, feature_indices: Optional[Tuple[int, int]] = None,
                     title: str = 'K-means 聚类结果') -> None:
        """
        可视化聚类结果（仅适用于2维数据）
        :param feature_indices: 要绘制的特征索引，如 (0, 1) 表示绘制第1和第2列
        :param title: 图表标题
        """
        self._check_is_fitted()
        
        if self.scaled_data.shape[1] != 2 and feature_indices is None:
            raise ValueError('数据维度超过2维，请指定 feature_indices 参数选择两个特征进行可视化')
        
        if feature_indices is not None:
            x_data = self.scaled_data[:, feature_indices[0]]
            y_data = self.scaled_data[:, feature_indices[1]]
            centers = self.centers[:, feature_indices]
        else:
            x_data = self.scaled_data[:, 0]
            y_data = self.scaled_data[:, 1]
            centers = self.centers
        
        plt.figure(figsize=(10, 8))
        colors = plt.cm.tab10(np.linspace(0, 1, len(np.unique(self.labels))))
        
        for i, label in enumerate(np.unique(self.labels)):
            mask = self.labels == label
            plt.scatter(x_data[mask], y_data[mask], c=[colors[i]], 
                       s=100, alpha=0.7, label=f'簇 {label}', edgecolors='black', linewidth=0.5)
        
        plt.scatter(centers[:, 0], centers[:, 1], c='red', marker='X', 
                   s=300, linewidths=3, edgecolors='black', label='聚类中心', zorder=10)
        
        plt.xlabel(f'特征 {feature_indices[0] if feature_indices else 0}', fontsize=12)
        plt.ylabel(f'特征 {feature_indices[1] if feature_indices else 1}', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend(fontsize=12, loc='best')
        plt.grid(False)
        plt.tight_layout()
        plt.savefig('j:/ljp_page/ljp_page/_ljp_applications/pc/res/pt/4_K-means聚类结果可视化.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    @staticmethod
    def quick_cluster(data: Union[np.ndarray, pd.DataFrame], k_range: Tuple[int, int] = (2, 10),
                     method: Literal['elbow', 'silhouette', 'gap'] = 'silhouette',
                     plot: bool = True) -> Tuple['KmeanCluster', int]:
        """
        快速聚类方法，自动寻找最佳 K 值并聚类
        :param data: 输入数据
        :param k_range: K 值搜索范围
        :param method: 最佳 K 值选择方法
        :param plot: 是否绘制可视化图表
        :return: (训练好的聚类器, 最佳 K 值)
        """
        clusterer = KmeanCluster(data)
        best_k = clusterer.find_optimal_k(k_range=k_range, method=method, plot=plot)
        clusterer.fit(n_clusters=best_k)
        
        if plot and data.shape[1] == 2:
            clusterer.plot_clusters()
        
        return clusterer, best_k


def kmeans_auto(data: Union[np.ndarray, pd.DataFrame], k_range: Tuple[int, int] = (2, 10),
                method: Literal['elbow', 'silhouette', 'gap'] = 'silhouette',
                plot: bool = True) -> Tuple[np.ndarray, int, KmeanCluster]:
    """
    自动 K-means 聚类的便捷函数
    :param data: 输入数据
    :param k_range: K 值搜索范围
    :param method: 最佳 K 值选择方法
    :param plot: 是否绘制可视化图表
    :return: (聚类标签, 最佳 K 值, 聚类器对象)
    """
    clusterer, best_k = KmeanCluster.quick_cluster(data, k_range, method, plot)
    return clusterer.labels, best_k, clusterer
