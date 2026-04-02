from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix
import seaborn as sns

from ljp_page.data_analysis.ml.multimodal.multimodal import Multimodal
from ljp_page.data_analysis.visualization.matplotlib import Matplotlib
from sklearn.metrics import adjusted_rand_score

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

if __name__ == '__main__':
    output_dir = Path('res/pt')
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dict, true_labels = create_data.data()
    print(f"  样本数量: {len(true_labels)}")

    # 显示各模态信息
    modality_info = {
        'sensor': {'name': '传感器时序数据', 'features': list(data_dict['sensor'].columns)},
        'image': {'name': '图像视觉特征', 'features': list(data_dict['image'].columns)},
        'lab': {'name': '临床检验数据', 'features': list(data_dict['lab'].columns)},
        'behavior': {'name': '行为活动数据', 'features': list(data_dict['behavior'].columns)}
    }

    for key, info in modality_info.items():
        print(f"\n  【模态 - {info['name']}】")
        print(f"  特征维度: {len(info['features'])}")
        print(f"  特征列表: {info['features']}")

    print(f"\n  【健康状态分布】")
    print(f'true_labels: {true_labels}')
    label_names = {0: '健康', 1: '亚健康', 2: '疾病风险'}
    for label, count in zip(*np.unique(true_labels, return_counts=True)):
        print(f"  {label_names[label]}: {count}人 ({count / len(true_labels) * 100:.1f}%)")

    # 2. 初始化ljp_page库的多模态关联分析器
    print("\n[步骤2] 初始化多模态关联分析器（使用ljp_page库）...")

    ma = Multimodal(random_state=42)
    print("\n[步骤3] 添加四个模态数据...")
    for key in ['sensor', 'image', 'lab', 'behavior']:
        ma.add_modality(
            data_dict[key].values,
            key,
            feature_names=modality_info[key]['features'],
            normalize=True
        )
    # for i,j in ma.modalities.items():
    #     print(i,j)
    print(f"  模态数量: {len(ma.modalities)}")
    print(f"  模态名称: {list(ma.modalities.keys())}")

    print("\n[步骤4] 执行多模态典型相关分析(CCA)...")
    print("  分析各模态之间的跨模态关联...")

    # 定义要分析的模态对（可灵活扩展，模态越多优势越明显）
    modality_pairs = [
        ('sensor', 'image', '传感器-图像'),
        ('lab', 'behavior', '临床-行为'),
        ('sensor', 'lab', '传感器-临床'),
    ]

    # 循环分析所有模态对，存储结果
    cca_results = {}
    for mod1, mod2, pair_name in modality_pairs:
        X_scores, Y_scores, X_loadings, Y_loadings = ma.cca(
            mod1, mod2, n_components=2
        )
        correlations = ma.get_cca(mod1, mod2, n_components=3)
        cca_results[pair_name] = {
            'correlations': correlations,
            'X_scores': X_scores,
            'Y_scores': Y_scores,
            'X_loadings': X_loadings,
            'Y_loadings': Y_loadings
        }
        print(f"  {pair_name}典型相关系数: {[f'{c:.4f}' for c in correlations]}")

    print("\n[步骤5] 执行多模态特征融合...")
    print("  将四个模态的特征融合为统一表示...")
    fusion_method = {'concat': '简单拼接', 'average': '降维平均', 'weighted': '加权融合'}
    fusion_results = {}

    for method in fusion_method.keys():
        fused_features = ma.fuse(fusion_method=method)
        fusion_results[method] = fused_features
        print(f"  {fusion_method[method]}融合后特征维度: {fused_features.shape}")

    print("\n[步骤6] 在融合特征空间进行聚类分析...")
    print("  基于多模态特征识别健康状态模式...")
    best_method = 'concat'
    best_features = fusion_results[best_method]

    cluster_model = ma.cluster_fusion(n_clusters=3, data=best_features, init='k-means++', max_iter=300)
    cluster_labels = cluster_model.labels
    silhouette = cluster_model.get_silhouette_score()
    inertia = cluster_model.get_inertia()

    print(f"  聚类方法: K-Means")
    print(f"  发现聚类数量: {len(np.unique(cluster_labels))}")
    print(f"  轮廓系数: {silhouette:.4f}")
    print(f"  惯性值: {inertia:.4f}")

    # 与真实健康标签对比
    ari = adjusted_rand_score(true_labels, cluster_labels)
    print(f"  调整兰德指数(与真实健康状态对比): {ari:.4f}")

    print("\n[步骤7] 计算跨模态相似度...")
    print("  评估各模态之间的跨模态预测能力...")
    similarity_dict = ma.cross(method='cosine', store=True)
    valid_similarities = [d.mean() for d in similarity_dict.values()]

    avg_similarity = np.mean(valid_similarities) if valid_similarities else 0.00
    print(f"  整体跨模态平均相似度: {avg_similarity:.4f}")

    print("\n[步骤7.1] 跨模态相似度详细分析...")
    modality_pair_analysis = []
    for (mod1, mod2), matrix in similarity_dict.items():
        if mod1 < mod2:
            diag_sim = np.diag(matrix)
            modality_pair_analysis.append({
                'pair': f'{mod1}-{mod2}',
                'overall_mean': matrix.mean(),
                'diag_mean': diag_sim.mean(),
                'diag_std': diag_sim.std(),
                'diag_min': diag_sim.min(),
                'diag_max': diag_sim.max()
            })
            print(f"  {mod1}-{mod2}:")
            print(f"    整体均值: {matrix.mean():.4f}")
            print(f"    同个体均值: {diag_sim.mean():.4f}")
            print(f"    同个体标准差: {diag_sim.std():.4f}")
            print(f"    同个体范围: [{diag_sim.min():.4f}, {diag_sim.max():.4f}]")

    print("\n[步骤7.2] 不同相似度计算方法对比...")
    method_comparison = {}
    for method in ['cosine', 'euclidean', 'pearson']:
        sim_dict = ma.cross(method=method, store=False)
        avg_sim = np.mean([d.mean() for d in sim_dict.values()])
        diag_sims = []
        for (mod1, mod2), matrix in sim_dict.items():
            if mod1 < mod2:
                diag_sims.extend(np.diag(matrix).tolist())
        method_comparison[method] = {
            'overall_mean': avg_sim,
            'diag_mean': np.mean(diag_sims),
            'diag_std': np.std(diag_sims)
        }
        print(f"  {method}:")
        print(f"    整体均值: {avg_sim:.4f}")
        print(f"    同个体均值: {np.mean(diag_sims):.4f}")
        print(f"    同个体标准差: {np.std(diag_sims):.4f}")

    print("\n[步骤7.3] CCA载荷分析（特征重要性）...")
    for pair_name, result in cca_results.items():
        print(f"\n  【{pair_name}】")
        X_loadings = result['X_loadings']
        Y_loadings = result['Y_loadings']

        # 获取对应模态的特征名称
        mod1_name, mod2_name = None, None
        for mod1, mod2, display_name in modality_pairs:
            if display_name == pair_name:
                mod1_name, mod2_name = mod1, mod2
                break

        if mod1_name and mod2_name:
            mod1_features = modality_info[mod1_name]['features']
            mod2_features = modality_info[mod2_name]['features']

            # 第一典型变量的载荷（按绝对值排序）
            X_importance = np.abs(X_loadings[:, 0])
            Y_importance = np.abs(Y_loadings[:, 0])

            X_top_idx = np.argsort(X_importance)[::-1][:3]
            Y_top_idx = np.argsort(Y_importance)[::-1][:3]

            print(f"    第一模态前3重要特征: {[mod1_features[i] for i in X_top_idx]}")
            print(f"    第二模态前3重要特征: {[mod2_features[i] for i in Y_top_idx]}")

    print("\n[步骤7.4] 不同融合方法聚类效果对比...")
    fusion_comparison = {}
    for method, features in fusion_results.items():
        cluster_model = ma.cluster_fusion(n_clusters=3, data=features, init='k-means++', max_iter=300)
        ari = adjusted_rand_score(true_labels, cluster_model.labels)
        silhouette = cluster_model.get_silhouette_score()
        inertia = cluster_model.get_inertia()
        fusion_comparison[method] = {
            'ari': ari,
            'silhouette': silhouette,
            'inertia': inertia
        }
        print(f"  {method}:")
        print(f"    调整兰德指数: {ari:.4f}")
        print(f"    轮廓系数: {silhouette:.4f}")
        print(f"    惯性值: {inertia:.4f}")

    viz = Matplotlib()

    print("\n[步骤8] 生成可视化图表...")

    print("  生成图表1: 多模态典型相关系数对比")
    modality_pair_names = list(cca_results.keys())
    correlations = [cca_results[pair]['correlations'][0] for pair in modality_pair_names]

    viz.bar(modality_pair_names, correlations,
            title='多模态典型相关系数对比',
            xlabel='模态对',
            ylabel='第一典型相关系数',
            save_path=output_dir / '01_多模态典型相关系数对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 01_多模态典型相关系数对比.png")

    print("  生成图表2: 跨模态相似度对比（同个体）")
    pair_names = [item['pair'] for item in modality_pair_analysis]
    diag_means = [item['diag_mean'] for item in modality_pair_analysis]
    diag_stds = [item['diag_std'] for item in modality_pair_analysis]

    viz = Matplotlib()
    viz.bar(pair_names, diag_means,
            yerr=diag_stds,
            title='各模态对跨模态相似度对比',
            xlabel='模态对',
            ylabel='同个体相似度均值',
            save_path=output_dir / '02_跨模态相似度对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 02_跨模态相似度对比.png")

    print("  生成图表3: 不同相似度方法对比")
    methods = list(method_comparison.keys())
    method_diag_means = [method_comparison[m]['diag_mean'] for m in methods]
    method_diag_stds = [method_comparison[m]['diag_std'] for m in methods]

    viz = Matplotlib()
    viz.bar(methods, method_diag_means,
            yerr=method_diag_stds,
            title='不同相似度计算方法对比',
            xlabel='计算方法',
            ylabel='同个体相似度均值',
            save_path=output_dir / '03_不同相似度方法对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 03_不同相似度方法对比.png")

    print("  生成图表4: 不同融合方法聚类效果对比")
    fusion_methods = list(fusion_comparison.keys())
    fusion_aris = [fusion_comparison[m]['ari'] for m in fusion_methods]
    fusion_silhouettes = [fusion_comparison[m]['silhouette'] for m in fusion_methods]

    viz = Matplotlib()

    x = np.arange(len(fusion_methods))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width / 2, fusion_aris, width, label='调整兰德指数', color='#4A90E2')
    bars2 = ax.bar(x + width / 2, fusion_silhouettes, width, label='轮廓系数', color='#50E3C2')

    ax.set_xlabel('融合方法', fontsize=12)
    ax.set_ylabel('评估指标值', fontsize=12)
    ax.set_title('不同融合方法聚类效果对比', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['简单拼接', '降维平均', '加权融合'])
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_dir / '04_不同融合方法聚类效果对比.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 04_不同融合方法聚类效果对比.png")

    print("  生成图表5: 健康状态分布饼图")
    label_counts = [np.sum(true_labels == i) for i in range(3)]
    label_names_cn = ['健康', '亚健康', '疾病风险']
    colors = ['#4A90E2', '#F5A623', '#D0021B']

    viz = Matplotlib()
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(label_counts,
                                      labels=label_names_cn,
                                      colors=colors,
                                      autopct='%1.1f%%',
                                      startangle=90,
                                      textprops={'fontsize': 12})

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(13)

    ax.set_title('健康状态分布', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / '05_健康状态分布.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 05_健康状态分布.png")

    print("  生成图表6: 聚类结果与真实标签混淆矩阵")
    conf_matrix = confusion_matrix(true_labels, cluster_labels)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
                xticklabels=['聚类0', '聚类1', '聚类2'],
                yticklabels=['健康', '亚健康', '疾病风险'],
                annot_kws={'size': 14}, cbar_kws={'label': '样本数量'})
    ax.set_xlabel('预测聚类标签', fontsize=12, fontweight='bold')
    ax.set_ylabel('真实健康标签', fontsize=12, fontweight='bold')
    ax.set_title('聚类结果与真实标签混淆矩阵', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(output_dir / '06_聚类混淆矩阵.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 06_聚类混淆矩阵.png")

    print("  生成图表7: 各模态PCA降维2D投影")
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    axes = axes.ravel()

    pca = PCA(n_components=2)
    label_names_cn = ['健康', '亚健康', '疾病风险']
    colors = ['#4A90E2', '#F5A623', '#D0021B']

    for idx, (key, info) in enumerate(modality_info.items()):
        modality_data = ma.modalities[key].data
        pca_result = pca.fit_transform(modality_data)

        for label in range(3):
            mask = true_labels == label
            axes[idx].scatter(pca_result[mask, 0], pca_result[mask, 1],
                              c=colors[label], label=label_names_cn[label],
                              alpha=0.6, s=50, edgecolors='white', linewidth=0.5)

        explained_var = pca.explained_variance_ratio_
        axes[idx].set_xlabel(f'第一主成分 ({explained_var[0] * 100:.1f}%)', fontsize=11)
        axes[idx].set_ylabel(f'第二主成分 ({explained_var[1] * 100:.1f}%)', fontsize=11)
        axes[idx].set_title(f'{info["name"]} PCA投影', fontsize=13, fontweight='bold')
        axes[idx].legend(fontsize=10, loc='best')
        axes[idx].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / '07_各模态PCA投影.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 07_各模态PCA投影.png")

    print("  生成图表8: 融合特征PCA降维可视化")
    fused_concat = fusion_results['concat']
    pca_fused = PCA(n_components=2)
    fused_pca = pca_fused.fit_transform(fused_concat)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    for label in range(3):
        mask = true_labels == label
        axes[0].scatter(fused_pca[mask, 0], fused_pca[mask, 1],
                        c=colors[label], label=label_names_cn[label],
                        alpha=0.6, s=50, edgecolors='white', linewidth=0.5)

    explained_var = pca_fused.explained_variance_ratio_
    axes[0].set_xlabel(f'第一主成分 ({explained_var[0] * 100:.1f}%)', fontsize=12)
    axes[0].set_ylabel(f'第二主成分 ({explained_var[1] * 100:.1f}%)', fontsize=12)
    axes[0].set_title('真实标签分布', fontsize=14, fontweight='bold')
    axes[0].legend(fontsize=11, loc='best')
    axes[0].grid(True, alpha=0.3)

    for label in range(3):
        mask = cluster_labels == label
        axes[1].scatter(fused_pca[mask, 0], fused_pca[mask, 1],
                        c=colors[label], label=f'聚类{label}',
                        alpha=0.6, s=50, edgecolors='white', linewidth=0.5)

    axes[1].set_xlabel(f'第一主成分 ({explained_var[0] * 100:.1f}%)', fontsize=12)
    axes[1].set_ylabel(f'第二主成分 ({explained_var[1] * 100:.1f}%)', fontsize=12)
    axes[1].set_title('聚类结果分布', fontsize=14, fontweight='bold')
    axes[1].legend(fontsize=11, loc='best')
    axes[1].grid(True, alpha=0.3)

    plt.suptitle('融合特征PCA降维可视化（简单拼接）', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '08_融合特征PCA可视化.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 08_融合特征PCA可视化.png")

    print("  生成图表9: 模态间相关性热力图")
    modality_names = list(ma.modalities.keys())
    n_modalities = len(modality_names)
    correlation_matrix = np.zeros((n_modalities, n_modalities))

    for i, mod1 in enumerate(modality_names):
        for j, mod2 in enumerate(modality_names):
            if i == j:
                correlation_matrix[i, j] = 1.0
            elif i < j:
                sim_dict = ma.cross(method='pearson', store=False)
                if (mod1, mod2) in sim_dict:
                    corr = np.diag(sim_dict[(mod1, mod2)]).mean()
                    correlation_matrix[i, j] = corr
                    correlation_matrix[j, i] = corr

    fig, ax = plt.subplots(figsize=(10, 8))
    modality_labels_cn = ['传感器', '图像', '临床', '行为']
    sns.heatmap(correlation_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                xticklabels=modality_labels_cn,
                yticklabels=modality_labels_cn,
                annot_kws={'size': 13}, cbar_kws={'label': '皮尔逊相关系数'},
                vmin=-0.5, vmax=1.0, linewidths=1, linecolor='white')
    ax.set_title('各模态间相关性热力图', fontsize=15, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(output_dir / '09_模态间相关性热力图.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 09_模态间相关性热力图.png")

    print("  生成图表10: CCA典型变量得分散点图")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for idx, pair_name in enumerate(['传感器-图像', '临床-行为', '传感器-临床']):
        result = cca_results[pair_name]
        X_scores = result['X_scores']
        Y_scores = result['Y_scores']

        for label in range(3):
            mask = true_labels == label
            axes[idx].scatter(X_scores[mask, 0], Y_scores[mask, 0],
                              c=colors[label], label=label_names_cn[label],
                              alpha=0.6, s=40, edgecolors='white', linewidth=0.5)

        corr = cca_results[pair_name]['correlations'][0]
        axes[idx].set_xlabel('第一模态典型变量', fontsize=11)
        axes[idx].set_ylabel('第二模态典型变量', fontsize=11)
        axes[idx].set_title(f'{pair_name}\n典型相关系数: {corr:.4f}',
                            fontsize=12, fontweight='bold')
        axes[idx].legend(fontsize=9, loc='best')
        axes[idx].grid(True, alpha=0.3)

    plt.suptitle('模态对典型变量得分分布', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '10_CCA典型变量得分.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 10_CCA典型变量得分.png")

    print("\n" + "=" * 60)
    print("分析完成！所有图表已保存至 res/figures/ 目录")
    print("=" * 60)
