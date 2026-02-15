
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Literal
from itertools import combinations

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from ljp_page._ljp_data_analysis.ml.Kmean import KmeanCluster
from ljp_page._ljp_data_analysis.visualization.pyecharts import Pyecharts
from ljp_page._ljp_data_analysis.visualization.matplotlib import Matplotlib
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
        :return: (X_scores, Y_scores, X_loadings, Y_loadings) 典型变量得分和载荷
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
                :return: 典型相关系数数组
                """
        X_scores, Y_scores, _, _ = self.cca(modality1, modality2, n_components)

        correlations = np.array([pearsonr(X_scores[:, i], Y_scores[:, i])[0]
                                 for i in range(X_scores.shape[1])])

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

        self.cluster_model = KmeanCluster(data, random_state=self.random_state)
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
















class create_data:
    @staticmethod
    def data(n_samples=200):
        """
            生成真正的多模态数据：智能健康监测系统（四模态）

            场景：结合多种数据源进行综合健康状况分析

            模态1 - 传感器时序数据（连续生理信号）：
            - 心率变异性特征：HRV时域、频域指标
            - 血压特征：收缩压、舒张压、脉压差
            - 体温特征：基础体温、体温波动

            模态2 - 图像特征数据（视觉特征）：
            - 皮肤图像特征：颜色直方图、纹理特征
            - 面部特征：气色指数、水肿程度

            模态3 - 临床检验数据（血液生化指标）：
            - 血常规：白细胞、红细胞、血红蛋白、血小板
            - 生化指标：血糖、胆固醇、甘油三酯、尿酸

            模态4 - 行为活动数据（生活方式指标）：
            - 运动数据：每日步数、运动时长、消耗卡路里
            - 睡眠数据：睡眠时长、深睡比例、早睡次数、睡眠质量评分

            参数：
                n_samples: 样本数量

            返回：
                dict: 包含四个模态的数据字典
                health_labels: 健康状态标签（健康/亚健康/疾病）
            """
        np.random.seed(42)

        # 健康状态标签：0-健康，1-亚健康，2-疾病风险
        health_labels = np.random.choice([0, 1, 2], size=n_samples, p=[0.5, 0.35, 0.15])

        # 统一配置：{健康状态: [传感器参数, 图像参数, 临床检验参数, 行为活动参数]}
        # 每个参数格式: [[均值, 标准差], ...]
        params = {
            0: [  # 健康
                [[50, 8], [45, 6], [42, 7], [800, 150], [1200, 200], [115, 8], [75, 5], [36.5, 0.3], [0.3, 0.1]],
                # 传感器10维
                [[230, 10], [190, 12], [180, 15], [25, 5], [28, 6], [30, 7], [40, 10], [0.85, 0.05], [0.15, 0.03],
                 [85, 8], [0.1, 0.05]],  # 图像11维
                [[6.5, 1.2], [4.8, 0.5], [140, 10], [250, 40], [5.0, 0.6], [4.5, 0.8], [1.2, 0.3], [320, 50]],  # 临床8维
                [[10000, 2000], [60, 15], [450, 100], [7.5, 1.0], [85, 5], [5, 1], [90, 5]]  # 行为7维
            ],
            1: [  # 亚健康
                [[35, 10], [30, 8], [28, 9], [1100, 200], [700, 150], [128, 12], [82, 8], [36.8, 0.4], [0.5, 0.15]],
                [[210, 15], [175, 18], [165, 20], [32, 8], [35, 9], [38, 10], [55, 12], [0.75, 0.08], [0.10, 0.04],
                 [65, 12], [0.25, 0.08]],
                [[7.8, 1.5], [4.5, 0.6], [135, 12], [280, 50], [5.8, 0.8], [5.2, 1.0], [1.8, 0.4], [380, 60]],
                [[7000, 2500], [40, 20], [350, 150], [6.5, 1.2], [75, 8], [3, 1], [70, 10]]
            ],
            2: [  # 疾病风险
                [[20, 12], [18, 10], [15, 8], [1500, 300], [400, 120], [145, 18], [90, 12], [37.2, 0.5], [0.8, 0.2]],
                [[180, 20], [150, 22], [140, 25], [45, 12], [48, 14], [50, 15], [75, 15], [0.60, 0.10], [0.05, 0.03],
                 [40, 15], [0.45, 0.12]],
                [[10.5, 2.0], [4.2, 0.8], [125, 15], [320, 70], [7.2, 1.2], [6.5, 1.5], [2.8, 0.6], [480, 80]],
                [[4000, 2000], [20, 15], [200, 100], [5.0, 1.5], [60, 12], [1, 1], [50, 15]]
            ]
        }

        # 特征名称
        sensor_names = [
            'HRV均值', 'HRV_SDNN', 'HRV_RMSSD', 'HRV低频功率', 'HRV高频功率',
            '收缩压', '舒张压', '脉压差', '基础体温', '体温波动'
        ]
        image_names = [
            '皮肤R均值', '皮肤G均值', '皮肤B均值',
            '皮肤R标准差', '皮肤G标准差', '皮肤B标准差',
            '纹理对比度', '纹理均匀性', '纹理能量',
            '气色指数', '水肿程度'
        ]
        lab_names = [
            '白细胞计数', '红细胞计数', '血红蛋白', '血小板计数',
            '空腹血糖', '总胆固醇', '甘油三酯', '尿酸'
        ]
        behavior_names = [
            '每日步数', '运动时长', '消耗卡路里',
            '睡眠时长', '深睡比例', '早睡次数', '睡眠质量'
        ]

        # 在一个循环中同时生成四个模态的数据
        sensor_features = []
        image_features = []
        lab_features = []
        behavior_features = []

        for health_state in health_labels:
            sensor_param, image_param, lab_param, behavior_param = params[health_state]

            # 生成传感器数据
            sensor_data = [np.random.normal(p[0], p[1]) for p in sensor_param[:7]]
            pp = sensor_data[5] - sensor_data[6]
            sensor_data.append(pp)
            sensor_data.extend([np.random.normal(p[0], p[1]) for p in sensor_param[7:]])
            sensor_data = np.array(sensor_data) + np.random.normal(0, 1, 10)
            sensor_features.append(sensor_data)

            # 生成图像数据
            img_data = [np.random.normal(p[0], p[1]) for p in image_param]
            img_data = np.array(img_data) + np.random.normal(0, 2, 11)
            image_features.append(img_data)

            # 生成临床检验数据
            lab_data = [np.random.normal(p[0], p[1]) for p in lab_param]
            lab_data = np.array(lab_data) + np.random.normal(0, 0.5, 8)
            lab_features.append(lab_data)

            # 生成行为活动数据
            behavior_data = [np.random.normal(p[0], p[1]) for p in behavior_param]
            behavior_data = np.array(behavior_data) + np.random.normal(0, 3, 7)
            behavior_features.append(behavior_data)

        X_sensor = np.array(sensor_features)
        X_image = np.array(image_features)
        X_lab = np.array(lab_features)
        X_behavior = np.array(behavior_features)

        # 创建DataFrame
        df_sensor = pd.DataFrame(X_sensor, columns=sensor_names)
        df_image = pd.DataFrame(X_image, columns=image_names)
        df_lab = pd.DataFrame(X_lab, columns=lab_names)
        df_behavior = pd.DataFrame(X_behavior, columns=behavior_names)

        # 返回包含四个模态的字典
        return {
            'sensor': df_sensor,
            'image': df_image,
            'lab': df_lab,
            'behavior': df_behavior
        }, health_labels



