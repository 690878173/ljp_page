import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Literal
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import CCA, PLSCanonical, PLSRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from scipy.stats import pearsonr

from ljp_page._ljp_data_analysis.ml.Kmean.kmean import KmeanCluster
from ljp_page._ljp_data_analysis.visualization.matplotlib import Matplotlib
from ljp_page._ljp_data_analysis.visualization.pyecharts import Pyecharts


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
            self.feature_names = [f'{modality_name}_f{i}' for i in range(data.shape[1])] if feature_names is None else feature_names
        
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
        self.cross_modal_similarity: Dict[Tuple[str, str], np.ndarray] = {}
        self.fusion_matrix: Optional[np.ndarray] = None
        self.pca_model: Optional[PCA] = None
        self.cluster_model: Optional[KmeanCluster] = None
        self.cluster_labels: Optional[np.ndarray] = None
        self.matplotlib = Matplotlib()
        self.pyecharts = Pyecharts()
        
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
        
        data = self.modalities[modality_name].scaled_data
        max_components = min(n_components, data.shape[1], data.shape[0])
        
        pca = PCA(n_components=max_components, random_state=self.random_state)
        reduced = pca.fit_transform(data)
        
        return reduced
    
    def _validate_sample_count(self) -> bool:
        """
        验证所有模态的样本数量是否一致
        :return: 是否一致
        """
        if len(self.modalities) < 2:
            return True
        
        sample_counts = [len(mod) for mod in self.modalities.values()]
        return len(set(sample_counts)) == 1
    
    def compute_cross_modal_similarity(self, 
                                      method: Literal['cosine', 'euclidean', 'pearson'] = 'cosine',
                                      store: bool = True,
                                      n_components: int = 10) -> Dict[Tuple[str, str], np.ndarray]:
        """
        计算跨模态相似度矩阵
        
        计算样本在两个模态之间的相似度矩阵，形状为 (n_samples, n_samples)
        对于不同维度的特征空间，通过特征相关性来计算模态间的关联
        
        :param method: 相似度计算方法
        - 'pearson': 计算特征间的皮尔逊相关性
        - 'cosine': 计算特征间的余弦相似度（降维后）
        - 'euclidean': 计算特征间的欧氏距离（降维后）
        :param store: 是否存储结果
        :param n_components: PCA降维维度（用于cosine/euclidean方法）
        :return: 跨模态相似度矩阵字典
        """
        if len(self.modalities) < 2:
            raise ValueError("至少需要两个模态才能计算跨模态相似度")
        
        if not self._validate_sample_count():
            raise ValueError("所有模态的样本数量必须一致")
        
        modality_names = list(self.modalities.keys())
        similarity_dict = {}
        
        if method == 'pearson':
            for i, name1 in enumerate(modality_names):
                for j, name2 in enumerate(modality_names):
                    if i < j:
                        data1 = self.modalities[name1].scaled_data
                        data2 = self.modalities[name2].scaled_data
                        
                        corr_matrix = np.corrcoef(data1.T, data2.T)[:data1.shape[1], data2.shape[1]:]
                        modality_sim = np.mean(np.abs(corr_matrix))
                        similarity_matrix = np.full((data1.shape[0], data2.shape[0]), modality_sim)
                        
                        similarity_dict[(name1, name2)] = similarity_matrix
                        similarity_dict[(name2, name1)] = similarity_matrix.T
        else:
            min_dim = min(mod.scaled_data.shape[1] for mod in self.modalities.values())
            pca_dim = min(min_dim, n_components)
            
            reduced_data = {}
            for name in modality_names:
                reduced_data[name] = self._reduce_modality_pca(name, pca_dim)
            
            for i, name1 in enumerate(modality_names):
                for j, name2 in enumerate(modality_names):
                    if i < j:
                        reduced1 = reduced_data[name1]
                        reduced2 = reduced_data[name2]
                        
                        if method == 'cosine':
                            similarity_matrix = cosine_similarity(reduced1, reduced2)
                        elif method == 'euclidean':
                            distances = euclidean_distances(reduced1, reduced2)
                            similarity_matrix = 1 / (1 + distances)
                        else:
                            raise ValueError(f"不支持的相似度计算方法: {method}")
                        
                        similarity_dict[(name1, name2)] = similarity_matrix
                        similarity_dict[(name2, name1)] = similarity_matrix.T
        
        if store:
            self.cross_modal_similarity = similarity_dict
        
        return similarity_dict
    
    def compute_intra_modal_similarity(self, 
                                      modality_name: str,
                                      method: Literal['cosine', 'euclidean'] = 'cosine') -> np.ndarray:
        """
        计算单模态内部的相似度矩阵
        :param modality_name: 模态名称
        :param method: 相似度计算方法
        :return: 相似度矩阵
        """
        if modality_name not in self.modalities:
            raise ValueError(f"模态 '{modality_name}' 不存在")
        
        data = self.modalities[modality_name].scaled_data
        
        if method == 'cosine':
            result = cosine_similarity(data)
        elif method == 'euclidean':
            distances = euclidean_distances(data)
            result = 1 / (1 + distances)
        else:
            raise ValueError(f"不支持的相似度计算方法: {method}")
        
        return result
    
    def fuse_modalities(self, 
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
    
    def reduce_dimension(self, 
                        n_components: int = 2,
                        data: Optional[np.ndarray] = None) -> np.ndarray:
        """
        降维
        :param n_components: 降维后的维度
        :param data: 输入数据，如果为None则使用融合后的数据
        :return: 降维后的数据
        """
        if data is None:
            if self.fusion_matrix is None:
                raise ValueError("请先调用 fuse_modalities() 进行数据融合")
            data = self.fusion_matrix
        
        self.pca_model = PCA(n_components=n_components, random_state=self.random_state)
        reduced_data = self.pca_model.fit_transform(data)
        
        return reduced_data
    
    def cross_modal_retrieval(self, 
                            query_modality: str,
                            target_modality: str,
                            query_index: int,
                            top_k: int = 5,
                            method: Literal['cosine', 'euclidean'] = 'cosine') -> Tuple[List[int], np.ndarray]:
        """
        跨模态检索：从一个模态查询，在另一个模态中找到最相似的样本
        :param query_modality: 查询模态名称
        :param target_modality: 目标模态名称
        :param query_index: 查询样本在查询模态中的索引
        :param top_k: 返回前K个最相似的样本
        :param method: 相似度计算方法
        :return: (目标样本索引列表, 相似度分数)
        """
        if query_modality not in self.modalities or target_modality not in self.modalities:
            raise ValueError("模态名称不存在")
        
        if query_modality == target_modality:
            raise ValueError("查询模态和目标模态不能相同")
        
        similarity_key = (query_modality, target_modality)
        if similarity_key not in self.cross_modal_similarity:
            self.compute_cross_modal_similarity(method=method, store=True)
        
        similarity_matrix = self.cross_modal_similarity[similarity_key]
        query_similarities = similarity_matrix[query_index]
        
        top_indices = np.argsort(query_similarities)[::-1][:top_k]
        top_similarities = query_similarities[top_indices]
        
        return top_indices.tolist(), top_similarities
    
    def get_modality_correlation(self, 
                                method: Literal['cosine', 'euclidean', 'pearson'] = 'cosine') -> pd.DataFrame:
        """
        获取各模态之间的平均相关性
        :param method: 相似度计算方法
        :return: 相关性矩阵 DataFrame
        """
        if len(self.modalities) < 2:
            raise ValueError("至少需要两个模态才能计算相关性")
        
        if not self.cross_modal_similarity:
            self.compute_cross_modal_similarity(method=method)
        
        modality_names = list(self.modalities.keys())
        n = len(modality_names)
        correlation_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    correlation_matrix[i, j] = 1.0
                elif i < j:
                    key = (modality_names[i], modality_names[j])
                    if key in self.cross_modal_similarity:
                        correlation_matrix[i, j] = np.mean(self.cross_modal_similarity[key])
                        correlation_matrix[j, i] = correlation_matrix[i, j]
        
        result = pd.DataFrame(correlation_matrix, index=modality_names, columns=modality_names)
        
        return result
    
    def get_fusion_feature_importance(self) -> pd.DataFrame:
        """
        获取各模态在融合特征中的重要性
        
        对于concat融合方式，计算各模态特征的方差贡献
        对于average/weighted融合方式，返回融合时使用的权重信息
        :return: 特征重要性 DataFrame
        """
        if self.fusion_matrix is None:
            raise ValueError("请先调用 fuse_modalities() 进行数据融合")
        
        modality_names = list(self.modalities.keys())
        importance_data = []
        
        if self.fusion_matrix.shape[1] == sum(self.modalities[name].scaled_data.shape[1] for name in modality_names):
            feature_start_idx = 0
            contributions = []
            
            for name in modality_names:
                modality_data = self.modalities[name].scaled_data
                n_features = modality_data.shape[1]
                
                contribution = np.var(self.fusion_matrix[:, feature_start_idx:feature_start_idx + n_features], axis=0)
                avg_contribution = np.mean(contribution)
                contributions.append(avg_contribution)
                
                importance_data.append({
                    '模态': name,
                    '特征数量': n_features,
                    '平均贡献度': avg_contribution,
                    '相对重要性': None
                })
                
                feature_start_idx += n_features
            
            total_contribution = sum(contributions)
            for i, item in enumerate(importance_data):
                if total_contribution > 0:
                    importance_data[i]['相对重要性'] = contributions[i] / total_contribution
        else:
            n_features = self.fusion_matrix.shape[1]
            total_importance = np.sum(np.var(self.fusion_matrix, axis=0))
            
            for i, name in enumerate(modality_names):
                importance_data.append({
                    '模态': name,
                    '特征数量': n_features,
                    '平均贡献度': np.var(self.fusion_matrix, axis=0).mean(),
                    '相对重要性': 1.0 / len(modality_names)
                })
        
        return pd.DataFrame(importance_data)
    
    def get_association_strength(self, 
                                modality1: str, 
                                modality2: str,
                                threshold: float = 0.5) -> Dict[str, float]:
        """
        计算两个模态之间的关联强度
        :param modality1: 第一个模态
        :param modality2: 第二个模态
        :param threshold: 相似度阈值
        :return: 关联强度指标
        """
        if (modality1, modality2) not in self.cross_modal_similarity:
            self.compute_cross_modal_similarity()
        
        similarity_matrix = self.cross_modal_similarity[(modality1, modality2)]
        
        return {
            '平均相似度': np.mean(similarity_matrix),
            '最大相似度': np.max(similarity_matrix),
            '最小相似度': np.min(similarity_matrix),
            '相似度标准差': np.std(similarity_matrix),
            '高相似度占比': np.mean(similarity_matrix > threshold) * 100,
            '中位数相似度': np.median(similarity_matrix)
        }
    
    def get_summary(self) -> Dict:
        """
        获取多模态关联模型的摘要信息
        :return: 摘要字典
        """
        modality_info = {}
        for name, modality in self.modalities.items():
            modality_info[name] = {
                '样本数量': len(modality),
                '特征维度': modality.data.shape[1],
                '特征名称': modality.feature_names
            }
        
        return {
            '模态数量': len(self.modalities),
            '模态信息': modality_info,
            '样本数量一致性': self._validate_sample_count(),
            '是否已计算跨模态相似度': len(self.cross_modal_similarity) > 0,
            '是否已融合': self.fusion_matrix is not None,
            '是否已降维': self.pca_model is not None
        }
    
    def _validate_and_get_max_components(self, 
                                        modality1: str, 
                                        modality2: str,
                                        n_components: int) -> Tuple[np.ndarray, np.ndarray, int]:
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
    
    def canonical_correlation_analysis(self, 
                                      modality1: str, 
                                      modality2: str,
                                      n_components: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        典型相关分析（CCA）
        寻找两个模态之间的最大相关性
        
        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_components: 典型变量数量
        :return: (X_scores, Y_scores, X_loadings, Y_loadings) 典型变量得分和载荷
        """
        X, Y, n_components = self._validate_and_get_max_components(modality1, modality2, n_components)
        
        cca = CCA(n_components=n_components)
        X_scores, Y_scores = cca.fit_transform(X, Y)
        
        return X_scores, Y_scores, cca.x_weights_, cca.y_weights_
    
    def get_canonical_correlations(self, 
                                   modality1: str, 
                                   modality2: str,
                                   n_components: int = 2) -> np.ndarray:
        """
        获取典型相关系数
        
        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_components: 典型变量数量
        :return: 典型相关系数数组
        """
        X_scores, Y_scores, _, _ = self.canonical_correlation_analysis(modality1, modality2, n_components)
        
        correlations = np.array([pearsonr(X_scores[:, i], Y_scores[:, i])[0] 
                                for i in range(X_scores.shape[1])])
        
        return correlations
    
    def partial_least_squares(self, 
                             modality1: str, 
                             modality2: str,
                             n_components: int = 2,
                             method: Literal['canonical', 'regression'] = 'canonical') -> Tuple[np.ndarray, np.ndarray]:
        """
        偏最小二乘法（PLS）
        用于多模态数据融合和预测
        
        :param modality1: 第一个模态名称（作为X）
        :param modality2: 第二个模态名称（作为Y）
        :param n_components: 潜变量数量
        :param method: PLS方法类型，'canonical'（PLS-Canonical）或 'regression'（PLS-Regression）
        :return: (X_scores, Y_scores) 潜变量得分
        """
        X, Y, n_components = self._validate_and_get_max_components(modality1, modality2, n_components)
        
        if method == 'canonical':
            pls = PLSCanonical(n_components=n_components)
        else:
            pls = PLSRegression(n_components=n_components)
        
        X_scores, Y_scores = pls.fit_transform(X, Y)
        
        return X_scores, Y_scores
    
    def get_pls_explained_variance(self, 
                                   modality1: str, 
                                   modality2: str,
                                   n_components: int = 2,
                                   method: Literal['canonical', 'regression'] = 'canonical') -> Tuple[np.ndarray, np.ndarray]:
        """
        获取PLS模型的解释方差（优化版）
        
        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_components: 潜变量数量
        :param method: PLS方法类型
        :return: (X_explained_variance, Y_explained_variance)
        """
        X, Y, n_components = self._validate_and_get_max_components(modality1, modality2, n_components)
        
        if method == 'canonical':
            pls = PLSCanonical(n_components=n_components)
        else:
            pls = PLSRegression(n_components=n_components)
        
        pls.fit(X, Y)
        
        X_explained_variance = np.sum(pls.x_loadings_ ** 2, axis=0)
        Y_explained_variance = np.sum(pls.y_loadings_ ** 2, axis=0)
        
        return X_explained_variance, Y_explained_variance
    
    def linear_discriminant_analysis(self, 
                                     labels: np.ndarray,
                                     n_components: Optional[int] = None) -> np.ndarray:
        """
        线性判别分析（LDA）
        使用类别信息进行有监督降维
        
        :param labels: 类别标签数组
        :param n_components: 降维后的维度，默认为min(n_classes-1, n_features)
        :return: 降维后的特征矩阵
        """
        if self.fusion_matrix is None:
            raise ValueError("请先调用 fuse_modalities() 进行数据融合")
        
        n_classes = len(np.unique(labels))
        n_features = self.fusion_matrix.shape[1]
        
        if n_components is None:
            n_components = min(n_classes - 1, n_features)
        
        lda = LDA(n_components=n_components)
        reduced_features = lda.fit_transform(self.fusion_matrix, labels)
        
        return reduced_features
    
    def compute_modality_divergence(self, modality1: str, modality2: str, n_bins: int = 20) -> Dict[str, float]:
        """
        计算两个模态之间的统计差异（KL散度等）（优化版，向量化计算）
        
        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_bins: 直方图箱数
        :return: 包含多种统计距离的字典
        """
        from scipy.stats import entropy, wasserstein_distance
        
        X = self.modalities[modality1].scaled_data
        Y = self.modalities[modality2].scaled_data
        
        min_features = min(X.shape[1], Y.shape[1])
        X_subset = X[:, :min_features]
        Y_subset = Y[:, :min_features]
        
        kl_divergences = np.zeros(min_features)
        wasserstein_distances = np.zeros(min_features)
        
        for i in range(min_features):
            hist_x, _ = np.histogram(X_subset[:, i], bins=n_bins, density=True)
            hist_y, _ = np.histogram(Y_subset[:, i], bins=n_bins, density=True)
            
            hist_x = hist_x + 1e-10
            hist_y = hist_y + 1e-10
            
            kl_divergences[i] = entropy(hist_x, hist_y)
            wasserstein_distances[i] = wasserstein_distance(X_subset[:, i], Y_subset[:, i])
        
        return {
            'mean_kl_divergence': np.mean(kl_divergences),
            'mean_wasserstein': np.mean(wasserstein_distances),
            'std_kl_divergence': np.std(kl_divergences),
            'std_wasserstein': np.std(wasserstein_distances),
            'min_kl_divergence': np.min(kl_divergences),
            'max_kl_divergence': np.max(kl_divergences),
            'min_wasserstein': np.min(wasserstein_distances),
            'max_wasserstein': np.max(wasserstein_distances),
            'per_feature_kl_divergence': kl_divergences,
            'per_feature_wasserstein': wasserstein_distances
        }
    
    def get_modality_statistics(self, modality_name: str) -> Dict[str, Union[float, np.ndarray]]:
        """
        获取指定模态的统计信息（优化版，减少重复计算）
        
        :param modality_name: 模态名称
        :return: 统计信息字典
        """
        if modality_name not in self.modalities:
            raise ValueError(f"模态不存在: {modality_name}")
        
        data = self.modalities[modality_name].scaled_data
        
        feature_stats = {
            'mean': np.mean(data, axis=0),
            'std': np.std(data, axis=0),
            'min': np.min(data, axis=0),
            'max': np.max(data, axis=0),
            'median': np.median(data, axis=0)
        }
        
        var_per_feature = np.var(data, axis=0)
        total_var = np.sum(var_per_feature)
        
        feature_stats.update({
            'global_mean': np.mean(data),
            'global_std': np.std(data),
            'variance_explained_ratio': var_per_feature / total_var if total_var > 0 else var_per_feature
        })
        
        return feature_stats
    
    def cluster_fusion_data(self, 
                           n_clusters: int = 3,
                           data: Optional[np.ndarray] = None,
                           init: Literal['k-means++', 'random'] = 'k-means++',
                           n_init: int = 10,
                           max_iter: int = 300) ->  KmeanCluster:
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
        
        self.cluster_model = KmeanCluster(data, random_state=self.random_state)
        self.cluster_model.fit(n_clusters=n_clusters, init=init, n_init=n_init, max_iter=max_iter)
        
        return self.cluster_model
    
    def get_cluster_metrics(self) -> Dict[str, float]:
        """
        获取聚类评估指标
        
        :return: 包含各项聚类指标的字典
        """
        if self.cluster_model is None:
            raise ValueError("请先调用 cluster_fusion_data() 进行聚类")
        
        silhouette = self.cluster_model.get_silhouette_score()
        inertia = self.cluster_model.get_inertia()
        
        return {
            'silhouette_score': silhouette,
            'inertia': inertia
        }
    
    def visualize_correlation_heatmap(self, 
                                       save_path: Optional[str] = None,
                                       title: str = '跨模态相关性热图',
                                       show: bool = True) -> None:
        """
        可视化跨模态相关性热图
        
        :param save_path: 保存路径
        :param title: 图表标题
        :param show: 是否显示图表
        """
        correlation_df = self.get_modality_correlation()
        
        self.matplotlib.heatmap(
            data=correlation_df.values,
            title=title,
            xlabel='模态',
            ylabel='模态',
            xticklabels=correlation_df.columns.tolist(),
            yticklabels=correlation_df.index.tolist(),
            cmap='RdYlBu_r',
            annot=True,
            fmt='.4f',
            save_path=save_path,
            show=show
        )
    
    def visualize_cluster_scatter(self, 
                                  save_path: Optional[str] = None,
                                  title: str = '多模态融合聚类结果',
                                  show: bool = True) -> None:
        """
        可视化聚类结果（降维后的散点图）
        
        :param save_path: 保存路径
        :param title: 图表标题
        :param show: 是否显示图表
        """
        if self.cluster_labels is None:
            raise ValueError("请先调用 cluster_fusion_data() 进行聚类")
        
        if self.pca_model is None or self.pca_model.n_components != 2:
            reduced_data = self.reduce_dimension(n_components=2)
        else:
            reduced_data = self.pca_model.transform(self.fusion_matrix)
        
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 8))
        unique_labels = np.unique(self.cluster_labels)
        colors = self.matplotlib.get_color(len(unique_labels))
        
        for i, label in enumerate(unique_labels):
            mask = self.cluster_labels == label
            plt.scatter(reduced_data[mask, 0], reduced_data[mask, 1], 
                       c=[colors[i]], label=f'聚类{label}', alpha=0.6)
        
        plt.title(title)
        plt.xlabel('第一主成分')
        plt.ylabel('第二主成分')
        plt.legend()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        
        plt.close()
    
    def visualize_feature_importance(self, 
                                     modality_name: str,
                                     save_path: Optional[str] = None,
                                     title: Optional[str] = None,
                                     show: bool = True) -> None:
        """
        可视化指定模态的特征重要性
        
        :param modality_name: 模态名称
        :param save_path: 保存路径
        :param title: 图表标题
        :param show: 是否显示图表
        """
        if modality_name not in self.modalities:
            raise ValueError(f"模态不存在: {modality_name}")
        
        data = self.modalities[modality_name].scaled_data
        feature_names = self.modalities[modality_name].feature_names
        importance = np.var(data, axis=0)
        
        if title is None:
            title = f'{modality_name}模态特征重要性'
        
        self.matplotlib.bar(
            x=np.arange(len(feature_names)),
            y=importance,
            title=title,
            xlabel='特征',
            ylabel='重要性（方差）',
            save_path=save_path,
            show=show,
            xlabel_rotation=45
        )
    
    def visualize_canonical_correlations(self, 
                                         modality1: str,
                                         modality2: str,
                                         n_components: int = 2,
                                         save_path: Optional[str] = None,
                                         title: Optional[str] = None,
                                         show: bool = True) -> None:
        """
        可视化典型相关系数
        
        :param modality1: 第一个模态名称
        :param modality2: 第二个模态名称
        :param n_components: 典型变量数量
        :param save_path: 保存路径
        :param title: 图表标题
        :param show: 是否显示图表
        """
        correlations = self.get_canonical_correlations(modality1, modality2, n_components)
        
        if title is None:
            title = f'{modality1}与{modality2}的典型相关系数'
        
        self.matplotlib.bar(
            x=np.arange(1, len(correlations) + 1),
            y=correlations,
            title=title,
            xlabel='典型变量编号',
            ylabel='典型相关系数',
            save_path=save_path,
            show=show
        )
    
    def visualize_cluster_pyecharts(self, 
                                   save_path: Optional[str] = None,
                                   title: str = '多模态融合聚类结果（交互式）') -> None:
        """
        使用Pyecharts创建交互式聚类可视化
        
        :param save_path: 保存路径（HTML格式）
        :param title: 图表标题
        """
        if self.cluster_labels is None:
            raise ValueError("请先调用 cluster_fusion_data() 进行聚类")
        
        if self.pca_model is None or self.pca_model.n_components != 2:
            reduced_data = self.reduce_dimension(n_components=2)
        else:
            reduced_data = self.pca_model.transform(self.fusion_matrix)
        
        from pyecharts.charts import Scatter
        from pyecharts import options as opts
        
        scatter = Scatter(init_opts=opts.InitOpts(width="800px", height="600px"))
        
        unique_labels = np.unique(self.cluster_labels)
        colors = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de"]
        
        for i, label in enumerate(unique_labels):
            mask = self.cluster_labels == label
            scatter.add_xaxis(reduced_data[mask, 0].tolist())
            scatter.add_yaxis(
                f"聚类{label}",
                reduced_data[mask, 1].tolist(),
                color=colors[i % len(colors)],
                label_opts=opts.LabelOpts(is_show=False)
            )
        
        scatter.set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(name="第一主成分"),
            yaxis_opts=opts.AxisOpts(name="第二主成分"),
            tooltip_opts=opts.TooltipOpts(trigger="axis")
        )
        
        if save_path:
            scatter.render(save_path)
        else:
            scatter.render()