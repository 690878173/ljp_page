import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Literal
from itertools import combinations
from dataclasses import dataclass
from pathlib import Path

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from ljp_page.data_analysis.ml.Kmean import KMeanCluster
from ljp_page.data_analysis.visualization.pyecharts import Pyecharts
from ljp_page.data_analysis.visualization.matplotlib import Matplotlib
from sklearn.cross_decomposition import CCA, PLSCanonical, PLSRegression
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

from scipy.stats import pearsonr

class ModalityData:
    """
    单模态数据容器类，用于存储和管理单一模态的数据
    """

    def __init__(self, data: Union[np.ndarray, pd.DataFrame],
                 modality_name: str,
                 feature_names: Optional[List[str]] = None):
        """
        初始化单模态数据
        :param data: 数据，可以是 numpy 数组或 DataFrame
        :param modality_name: 模态名称，如 'text', 'image', 'audio', 'numeric'
        :param feature_names: 特征名称列表
        """
        self.modality_name = modality_name
        if isinstance(data, pd.DataFrame):
            self.data = data.values
            self.feature_names = data.columns.tolist() if feature_names is None else feature_names
        else:
            self.data = np.asarray(data, dtype=np.float64)
            self.feature_names = [f'{modality_name}_f{i}' for i in
                                  range(data.shape[1])] if feature_names is None else feature_names

        self.scaler = StandardScaler()
        self.scaled_data = None
        self._minmax_scaler = None
        self.original_shape = self.data.shape

    def normalize(self, method: Literal['standard', 'minmax'] = 'standard') -> np.ndarray:
        """
        数据标准化
        :param method: 标准化方法，'standard'（Z-score）或 'minmax'（归一化到[0,1]）
        :return: 标准化后的数据
        """
        if method == 'standard':
            self.scaled_data = self.scaler.fit_transform(self.data)
        elif method == 'minmax':
            if self._minmax_scaler is None:
                self._minmax_scaler = MinMaxScaler()
            self.scaled_data = self._minmax_scaler.fit_transform(self.data)
        else:
            raise ValueError(f"不支持的标准化方法: {method}")

        return self.scaled_data

    def get_feature_vector(self, index: int) -> np.ndarray:
        """
        获取指定样本的特征向量，使用数组视图避免复制
        :param index: 样本索引
        :return: 特征向量
        """
        data = self.scaled_data if self.scaled_data is not None else self.data
        return data[index:index + 1].ravel()

    def pca(self,n_components: int,random_state: int = 42):
        data = self.scaled_data
        max_components = min(n_components, data.shape[1], data.shape[0])

        pca = PCA(n_components=max_components, random_state=random_state)
        reduced = pca.fit_transform(data)
        return reduced

    def __len__(self) -> int:
        return self.data.shape[0]

    def __repr__(self) -> str:
        return f"单模态数据(name={self.modality_name}, shape={self.data.shape})"


class Multimodal:
    """
    多模态关联分析模型

    核心功能：
    1. 融合多种模态的数据
    2. 计算模态间和模态内的相似度
    3. 进行跨模态关联分析
    4. 降维和特征提取
    5. 多模态聚类和检索
    """

    def __init__(self, random_state: int = 42):
        """
        初始化多模态关联模型
        :param random_state: 随机种子
        """
        self.random_state = random_state
        self.modalities: Dict[str, ModalityData] = {}
        self.matplotlib = Matplotlib()
        self.pyecharts = Pyecharts()

    def _validate_and_get_max_components(self,modality1: str,modality2: str,n_components: int) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        验证模态并计算最大可用组件数

        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_components: 请求的组件数
        :return: (X数据, Y数据, 最大可用组件数)
        """
        if modality1 not in self.modalities or modality2 not in self.modalities:
            raise ValueError(f"模态不存在: {modality1}, {modality2}")

        X = self.modalities[modality1].scaled_data
        Y = self.modalities[modality2].scaled_data

        max_components = min(X.shape[1], Y.shape[1], X.shape[0] - 1)
        n_components = min(n_components, max_components)

        return X, Y, n_components

    def _validate_sample_count(self) -> bool:
        """
        验证所有模态的样本数量是否一致
        :return: 是否一致
        """
        if len(self.modalities) < 2:
            return True

        sample_counts = [len(mod) for mod in self.modalities.values()]
        return len(set(sample_counts)) == 1

    def add_modality(self, data: Union[np.ndarray, pd.DataFrame],
                     modality_name: str,
                     feature_names: Optional[List[str]] = None,
                     normalize: bool = True,
                     normalize_method: Literal['standard', 'minmax'] = 'standard') -> 'Multimodal':
        """
        添加一个模态数据
        :param data: 模态数据
        :param modality_name: 模态名称
        :param feature_names: 特征名称
        :param normalize: 是否标准化数据
        :param normalize_method: 标准化方法
        :return: self
        """
        modality = ModalityData(data, modality_name, feature_names)
        if normalize:
            modality.normalize(normalize_method)
        self.modalities[modality_name] = modality
        return self

    def _reduce_modality_pca(self, modality_name: str, n_components: int) -> np.ndarray:
        """
        对指定模态进行PCA降维
        :param modality_name: 模态名称
        :param n_components: 降维后的维度
        :return: 降维后的数据
        """

        if modality_name not in self.modalities:
            raise ValueError(f"模态 '{modality_name}' 不存在")

        reduced = self.modalities[modality_name].pca(n_components=n_components,random_state=self.random_state)
        return reduced

    def cca(self, modality1: str, modality2: str,n_components: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        典型相关分析（CCA）
        寻找两个模态之间的最大相关性,计算权重矩阵，双降维

        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_components: 典型变量数量
        :return: (X_scores, Y_scores, X_loadings, Y_loadings) 典型变量得分和载荷(即进过cca降维后的新特征和对应权重)
        """
        X, Y, n_components = self._validate_and_get_max_components(modality1, modality2, n_components)

        _cca = CCA(n_components=n_components)
        X_scores, Y_scores = _cca.fit_transform(X, Y)

        return X_scores, Y_scores, _cca.x_weights_, _cca.y_weights_

    def get_cca(self, modality1: str, modality2: str,n_components: int = 2):
        """
                获取典型相关系数

                :param modality1: 第一个模态名称
                :param modality2: 第二个模态名称
                :param n_components: 典型变量数量
                :return: 典型相关系数数组（典则相关系数为每一对 CCA 新特征之间的皮尔逊相关系数）
                """
        X_scores, Y_scores, _, _ = self.cca(modality1, modality2, n_components)

        # 皮尔逊计算
        # correlations = np.array([pearsonr(X_scores[:, i], Y_scores[:, i])[0]
        #                          for i in range(X_scores.shape[1])])

        X_centered = X_scores - X_scores.mean(axis=0)
        Y_centered = Y_scores - Y_scores.mean(axis=0)

        # 向量化
        correlations = np.sum(X_centered * Y_centered, axis=0) / (
                np.sqrt(np.sum(X_centered ** 2, axis=0)) * np.sqrt(np.sum(Y_centered ** 2, axis=0))
        )

        return correlations

    def fuse(self,
             fusion_method: Literal['concat', 'average', 'weighted'] = 'concat',
             weights: Optional[Dict[str, float]] = None,
             pca_dim: int = 10) -> np.ndarray:
        """
        融合多模态数据

        :param fusion_method: 融合方法
        - 'concat': 拼接所有模态的特征
        - 'average': 先降维到相同维度再取平均
        - 'weighted': 先降维到相同维度再加权融合
        :param weights: 加权融合时的权重字典
        :param pca_dim: average/weighted融合方法使用的PCA降维维度
        :return: 融合后的特征矩阵
        """
        if not self._validate_sample_count():
            raise ValueError("所有模态的样本数量必须一致")

        modality_names = list(self.modalities.keys())
        fused_features = None
        if fusion_method == 'concat':
            fused_features = np.hstack([self.modalities[name].scaled_data for name in modality_names])

        elif fusion_method in ['average', 'weighted']:
            min_dim = min(self.modalities[name].scaled_data.shape[1] for name in modality_names)
            pca_dim = min(min_dim, pca_dim)

            reduced_features = []
            for name in modality_names:
                reduced = self._reduce_modality_pca(name, pca_dim)
                reduced_features.append(reduced)

            if fusion_method == 'average':
                fused_features = np.mean(reduced_features, axis=0)

            elif fusion_method == 'weighted':
                if weights is None:
                    weights = {name: 1.0 / len(modality_names) for name in modality_names}
                elif set(weights.keys()) != set(modality_names):
                    raise ValueError("权重字典必须包含所有模态")

                fused_features = np.zeros_like(reduced_features[0])
                for i, name in enumerate(modality_names):
                    fused_features += weights[name] * reduced_features[i]

        else:
            raise ValueError(f"不支持的融合方法: {fusion_method}")

        self.fusion_matrix = fused_features
        return fused_features

    def cluster_fusion(self,
                            n_clusters: int = 3,
                            data: Optional[np.ndarray] = None,
                            init: Literal['k-means++', 'random'] = 'k-means++',
                            n_init: int = 10,
                            max_iter: int = 300):
        """
        对融合数据进行聚类分析

        :param n_clusters: 聚类数量
        :param data: 输入数据，如果为None则使用融合后的数据
        :param init: 初始化方法
        :param n_init: 运行k-means的次数
        :param max_iter: 最大迭代次数
        :return: (聚类标签, 聚类模型)
        """
        if data is None:
            if self.fusion_matrix is None:
                raise ValueError("请先调用 fuse_modalities() 进行数据融合")
            data = self.fusion_matrix

        self.cluster_model = KMeanCluster(data, random_state=self.random_state)
        self.cluster_model.fit(n_clusters=n_clusters, init=init, n_init=n_init, max_iter=max_iter)

        return self.cluster_model

    def _pearson_similarity(self, data1: np.ndarray, data2: np.ndarray) -> np.ndarray:
        """
        使用皮尔逊相关系数计算跨模态相似度矩阵
        
        计算特征级别的相关性后，将平均相关性广播到所有样本对
        
        :param data1: 第一个模态的标准化数据
        :param data2: 第二个模态的标准化数据
        :return: 相似度矩阵，形状为 (n_samples, n_samples)
        """
        feature_corr = np.corrcoef(data1.T, data2.T)[:data1.shape[1], data2.shape[1]:]
        avg_correlation = np.mean(np.abs(feature_corr))
        return np.full((data1.shape[0], data2.shape[0]), avg_correlation)

    def _distance_similarity(self, data1: np.ndarray, data2: np.ndarray, metric: Literal['cosine', 'euclidean']) -> np.ndarray:
        """
        基于距离度量计算跨模态相似度矩阵
        
        :param data1: 第一个模态的数据
        :param data2: 第二个模态的数据
        :param metric: 距离度量类型
        :return: 相似度矩阵，形状为 (n_samples, n_samples)
        """
        if metric == 'cosine':
            return cosine_similarity(data1, data2)
        elif metric == 'euclidean':
            distances = euclidean_distances(data1, data2)
            return 1 / (1 + distances)

    def _build_pca_reduced_data(self, modality_names: List[str], n_components: int) -> Dict[str, np.ndarray]:
        """
        对所有模态进行PCA降维
        
        :param modality_names: 模态名称列表
        :param n_components: 请求的降维维度
        :return: 降维后的数据字典
        """
        min_dim = min(mod.scaled_data.shape[1] for mod in self.modalities.values())
        pca_dim = min(min_dim, n_components)
        return {name: self._reduce_modality_pca(name, pca_dim) for name in modality_names}

    def cross(self,
              method: Literal['cosine', 'euclidean', 'pearson'] = 'cosine',
              store: bool = True,
              n_components: int = 10) -> Dict[Tuple[str, str], np.ndarray]:
        """
        计算跨模态相似度矩阵

        计算样本在两个模态之间的相似度矩阵，形状为 (n_samples, n_samples)
        
        :param method: 相似度计算方法
        - 'pearson': 基于特征间皮尔逊相关性，将平均相关性广播到样本级
        - 'cosine': 基于降维后样本间的余弦相似度
        - 'euclidean': 基于降维后样本间的欧氏距离转换的相似度
        :param store: 是否将结果存储到实例属性
        :param n_components: PCA降维维度（用于cosine/euclidean方法）
        :return: 跨模态相似度矩阵字典，键为模态对元组
        """
        if len(self.modalities) < 2:
            raise ValueError("至少需要两个模态才能计算跨模态相似度")

        if not self._validate_sample_count():
            raise ValueError("所有模态的样本数量必须一致")

        modality_names = list(self.modalities.keys())
        similarity_dict = {}
        modality_pairs = list(combinations(modality_names, 2))

        if method == 'pearson':
            for name1, name2 in modality_pairs:
                data1 = self.modalities[name1].scaled_data
                data2 = self.modalities[name2].scaled_data
                similarity_matrix = self._pearson_similarity(data1, data2)
                similarity_dict[(name1, name2)] = similarity_matrix
                similarity_dict[(name2, name1)] = similarity_matrix.T
        else:
            reduced_data = self._build_pca_reduced_data(modality_names, n_components)
            for name1, name2 in modality_pairs:
                similarity_matrix = self._distance_similarity(
                    reduced_data[name1], reduced_data[name2], method
                )
                similarity_dict[(name1, name2)] = similarity_matrix
                similarity_dict[(name2, name1)] = similarity_matrix.T

        if store:
            self.cross_modal_similarity = similarity_dict

        return similarity_dict


@dataclass
class DataConfig:
    """数据生成配置"""
    n_samples: int
    n_features_per_modality: Dict[str, int]
    n_classes: int = 3
    noise_level: float = 0.0
    missing_rate: float = 0.0
    outlier_rate: float = 0.0
    class_balance: Optional[List[float]] = None
    concept_drift: bool = False
    temporal_dependence: bool = False
    multi_label: bool = False
    random_state: int = 42


class DataGen:
    """
    多模态数据生成器

    生成各种复杂场景的多模态测试数据：
    - 噪声干扰
    - 缺失值
    - 异常值
    - 类别不平衡
    - 概念漂移
    - 时间序列依赖
    - 多标签分类
    """

    def __init__(self, config: DataConfig|None=None):
        """
        初始化数据生成器

        参数：
            config: 数据生成配置
        """
        if config is None:
            config = DataConfig(
            n_samples=200,
            n_features_per_modality={
                'sensor': 20,
                'image': 15,
                'text': 25,
                'audio': 12
            },
            n_classes=4,
            noise_level=0.15,
            missing_rate=0.08,
            outlier_rate=0.05,
            class_balance=[0.4, 0.3, 0.2, 0.1],
            concept_drift=False,
            temporal_dependence=False,
            random_state=42
        )
        self._change_config(config)

    def _change_config(self,config):
        self.config = config
        self.rng = np.random.RandomState(config.random_state)
        self.modality_names = list(config.n_features_per_modality.keys())

    def _generate_base_data(self, modality: str, n_features: int) -> Tuple[np.ndarray, np.ndarray]:
        """生成基础数据"""
        n_samples = self.config.n_samples
        n_classes = self.config.n_classes

        if self.config.class_balance is None:
            class_probs = np.ones(n_classes) / n_classes
        else:
            class_probs = np.array(self.config.class_balance)
            class_probs = class_probs / class_probs.sum()

        labels = self.rng.choice(n_classes, size=n_samples, p=class_probs)

        base_means = []
        base_stds = []
        for class_idx in range(n_classes):
            if modality == 'sensor':
                class_mean = self.rng.uniform(50, 100, n_features)
                class_std = self.rng.uniform(5, 15, n_features)
            elif modality == 'image':
                class_mean = self.rng.uniform(150, 250, n_features)
                class_std = self.rng.uniform(10, 30, n_features)
            elif modality == 'text':
                class_mean = self.rng.uniform(0, 1, n_features)
                class_std = self.rng.uniform(0.1, 0.3, n_features)
            elif modality == 'audio':
                class_mean = self.rng.uniform(-1, 1, n_features)
                class_std = self.rng.uniform(0.2, 0.5, n_features)
            else:
                class_mean = self.rng.uniform(0, 100, n_features)
                class_std = self.rng.uniform(10, 20, n_features)

            base_means.append(class_mean)
            base_stds.append(class_std)

        data = np.zeros((n_samples, n_features))
        for i in range(n_samples):
            class_idx = labels[i]
            data[i] = self.rng.normal(base_means[class_idx], base_stds[class_idx])

        return data, labels

    def _add_noise(self, data: np.ndarray) -> np.ndarray:
        """添加噪声"""
        if self.config.noise_level <= 0:
            return data

        noise = self.rng.normal(0, self.config.noise_level * data.std(), data.shape)
        return data + noise

    def _add_missing_values(self, data: np.ndarray) -> np.ndarray:
        """添加缺失值"""
        if self.config.missing_rate <= 0:
            return data

        data_with_missing = data.copy()
        n_missing = int(data.size * self.config.missing_rate)

        for _ in range(n_missing):
            i = self.rng.randint(0, data.shape[0])
            j = self.rng.randint(0, data.shape[1])
            data_with_missing[i, j] = np.nan

        return data_with_missing

    def _add_outliers(self, data: np.ndarray) -> np.ndarray:
        """添加异常值"""
        if self.config.outlier_rate <= 0:
            return data

        data_with_outliers = data.copy()
        n_outliers = int(data.size * self.config.outlier_rate)

        for _ in range(n_outliers):
            i = self.rng.randint(0, data.shape[0])
            j = self.rng.randint(0, data.shape[1])

            outlier_multiplier = self.rng.choice([3, 5, 10])
            data_with_outliers[i, j] = data_with_outliers[i, j] * outlier_multiplier

        return data_with_outliers

    def _apply_concept_drift(self, data: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """应用概念漂移"""
        if not self.config.concept_drift:
            return data, labels

        n_samples = data.shape[0]
        drift_point = int(n_samples * 0.6)

        drifted_data = data.copy()
        drifted_labels = labels.copy()

        drift_factor = 1.5
        for i in range(drift_point, n_samples):
            drifted_data[i] = drifted_data[i] * drift_factor

        return drifted_data, drifted_labels

    def _apply_temporal_dependence(self, data: np.ndarray) -> np.ndarray:
        """应用时间序列依赖"""
        if not self.config.temporal_dependence:
            return data

        temporal_data = data.copy()
        lag = 5
        dependence = 0.3

        for i in range(lag, temporal_data.shape[0]):
            temporal_data[i] = (1 - dependence) * temporal_data[i] + dependence * temporal_data[i - lag]

        return temporal_data

    def _generate_multi_label(self, labels: np.ndarray) -> np.ndarray:
        """生成多标签"""
        if not self.config.multi_label:
            return labels.reshape(-1, 1)

        n_samples = labels.shape[0]
        n_classes = self.config.n_classes
        multi_labels = np.zeros((n_samples, n_classes), dtype=int)

        for i in range(n_samples):
            primary_class = labels[i]
            multi_labels[i, primary_class] = 1

            n_additional_labels = self.rng.randint(0, 2)
            available_classes = [c for c in range(n_classes) if c != primary_class]

            if available_classes and n_additional_labels > 0:
                additional_classes = self.rng.choice(available_classes, n_additional_labels, replace=False)
                for ac in additional_classes:
                    multi_labels[i, ac] = 1

        return multi_labels

    def generate(self) -> Dict[str, np.ndarray]:
        """
        生成完整的多模态数据集

        返回：
            dict: 包含所有模态数据和标签的字典
        """
        modality_data = {}
        primary_labels = None

        for modality_name, n_features in self.config.n_features_per_modality.items():
            data, labels = self._generate_base_data(modality_name, n_features)

            data = self._add_noise(data)
            data = self._add_missing_values(data)
            data = self._add_outliers(data)
            data, labels = self._apply_concept_drift(data, labels)
            data = self._apply_temporal_dependence(data)

            modality_data[modality_name] = data

            if primary_labels is None:
                primary_labels = labels

        final_labels = self._generate_multi_label(primary_labels)
        modality_data['labels'] = final_labels

        return modality_data

    def generate_feature_names(self) -> Dict[str, List[str]]:
        """生成特征名称"""
        feature_names = {}
        for modality_name, n_features in self.config.n_features_per_modality.items():
            names = [f'{modality_name}_feature_{i}' for i in range(n_features)]
            feature_names[modality_name] = names
        return feature_names

    def get_data_statistics(self, data: Dict[str, np.ndarray]) -> pd.DataFrame:
        """获取数据统计信息"""
        stats = []
        for modality_name, modality_data in data.items():
            if modality_name == 'labels':
                continue

            n_missing = np.isnan(modality_data).sum()
            missing_pct = (n_missing / modality_data.size) * 100

            stats.append({
                '模态': modality_name,
                '形状': str(modality_data.shape),
                '缺失值数量': n_missing,
                '缺失值比例': f'{missing_pct:.2f}%',
                '均值': f'{np.nanmean(modality_data):.4f}',
                '标准差': f'{np.nanstd(modality_data):.4f}',
                '最小值': f'{np.nanmin(modality_data):.4f}',
                '最大值': f'{np.nanmax(modality_data):.4f}'
            })

        return pd.DataFrame(stats)

    def get_small_data(self,random_state: int = 42):
        config = DataConfig(
            n_samples=50,
            n_features_per_modality={
                'sensor': 10,
                'image': 8,
                'text': 15
            },
            n_classes=3,
            noise_level=0.1,
            missing_rate=0.05,
            outlier_rate=0.03,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_medium_data(self,random_state: int = 42):
        config = DataConfig(
            n_samples=200,
            n_features_per_modality={
                'sensor': 20,
                'image': 15,
                'text': 25,
                'audio': 12
            },
            n_classes=4,
            noise_level=0.15,
            missing_rate=0.08,
            outlier_rate=0.05,
            class_balance=[0.4, 0.3, 0.2, 0.1],
            concept_drift=False,
            temporal_dependence=False,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_large_data(self,random_state: int = 42):
        """
        生成大规模数据（1000 样本）

        适用于：
        - 大规模模型训练
        - 深度学习算法测试
        - 性能压力测试
        """
        config = DataConfig(
            n_samples=1000,
            n_features_per_modality={
                'sensor': 50,
                'image': 40,
                'text': 100,
                'audio': 30,
                'video': 25
            },
            n_classes=5,
            noise_level=0.2,
            missing_rate=0.1,
            outlier_rate=0.05,
            class_balance=[0.5, 0.25, 0.15, 0.07, 0.03],
            concept_drift=True,
            temporal_dependence=True,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_imbalanced_data(self,random_state: int = 42):
        """
        生成高度不平衡数据（模拟罕见类别）

        适用于：
        - 不平衡学习算法测试
        - 代价敏感学习验证
        - 少数类识别能力评估
        """
        config = DataConfig(
            n_samples=300,
            n_features_per_modality={
                'sensor': 15,
                'image': 12,
                'text': 20
            },
            n_classes=4,
            noise_level=0.1,
            missing_rate=0.05,
            outlier_rate=0.04,
            class_balance=[0.70, 0.20, 0.08, 0.02],
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_concept_drift_data(self,random_state: int = 42):
        """
        生成概念漂移数据

        适用于：
        - 概念漂移检测算法测试
        - 增量学习验证
        - 模型适应性评估
        """
        config = DataConfig(
            n_samples=500,
            n_features_per_modality={
                'sensor': 20,
                'image': 15,
                'text': 25
            },
            n_classes=3,
            noise_level=0.1,
            missing_rate=0.15,
            outlier_rate=0.03,
            concept_drift=True,
            temporal_dependence=True,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_time_series_data(self,random_state: int = 42):
        """
        生成时间序列依赖数据

        适用于：
        - 时序模型测试
        - 序列相关性分析
        - 时间依赖性验证
        """
        config = DataConfig(
            n_samples=400,
            n_features_per_modality={
                'sensor': 18,
                'image': 14,
                'audio': 16
            },
            n_classes=3,
            noise_level=0.08,
            missing_rate=0.04,
            outlier_rate=0.02,
            temporal_dependence=True,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_multi_label_data(self,random_state: int = 42):
        """
        生成多标签分类数据

        适用于：
        - 多标签学习算法测试
        - 标签相关性分析
        - 多标签评估指标验证
        """
        config = DataConfig(
            n_samples=250,
            n_features_per_modality={
                'sensor': 18,
                'image': 15,
                'text': 22
            },
            n_classes=5,
            noise_level=0.12,
            missing_rate=0.06,
            outlier_rate=0.04,
            multi_label=True,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def get_high_noise_data(self,random_state: int = 42):
        """
        生成高噪声数据

        适用于：
        - 鲁棒性测试
        - 噪声处理算法验证
        - 信号处理能力评估
        """
        config = DataConfig(
            n_samples=150,
            n_features_per_modality={
                'sensor': 12,
                'image': 10,
                'text': 16
            },
            n_classes=3,
            noise_level=0.5,
            missing_rate=0.1,
            outlier_rate=0.08,
            random_state=random_state
        )
        self._change_config(config)
        data = self.generate()
        return data,config

    def save_data(self, data: Dict[str, np.ndarray], output_dir: str) -> None:
        """
        保存生成的数据

        参数：
            data: 生成的数据
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        feature_names = self.generate_feature_names()

        for modality_name, modality_data in data.items():
            if modality_name == 'labels':
                continue

            df = pd.DataFrame(modality_data, columns=feature_names.get(modality_name))
            df.to_csv(output_path / f'{modality_name}.csv', index=False, encoding='utf-8-sig')

        labels_df = pd.DataFrame(data['labels'])
        labels_df.to_csv(output_path / 'labels.csv', index=False, encoding='utf-8-sig')

        print(f"数据已保存至: {output_path}")


