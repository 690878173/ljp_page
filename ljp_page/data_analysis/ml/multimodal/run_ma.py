# 生成时间: 02-15-14-45-00
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # 设置为非交互后端
from matplotlib import pyplot as plt
import seaborn as sns
from sklearn.metrics import adjusted_rand_score, confusion_matrix

from ljp_page.data_analysis.ml.multimodal.multimodal import (
    Multimodal, DataConfig, DataGen
)
from ljp_page.data_analysis.visualization.matplotlib import Plotter
Matplotlib = Plotter
def plot_cca_scatter(ax, X_scores, Y_scores, true_labels, corr, 
                     xlabel, ylabel, title, colors_list, n_classes):
    """
    绘制 CCA 得分散点图的辅助函数
    
    :param ax: matplotlib axes 对象
    :param X_scores: 第一模态的 CCA 得分
    :param Y_scores: 第二模态的 CCA 得分
    :param true_labels: 真实标签
    :param corr: 典型相关系数
    :param xlabel: x轴标签
    :param ylabel: y轴标签
    :param title: 图表标题
    :param colors_list: 颜色列表
    :param n_classes: 类别数
    """
    # 为每个类别绘制散点
    for label in range(n_classes):
        mask = true_labels == label
        ax.scatter(X_scores[mask, 0], Y_scores[mask, 0],
                  c=[colors_list[label]], label=f'类别{label}',
                  alpha=0.6, s=40, edgecolors='white', linewidth=0.5)
    
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='best')
    ax.grid(False)


def main():
    """
    多模态关联分析 - 专注于多模态关联分析
    
    核心分析内容：
    1. 典型相关分析（CCA）- 模态间关联深度分析
    2. 跨模态相似度分析 - 模态间相似性评估
    3. 多模态融合方法对比 - 不同融合策略效果
    4. CCA 载荷分析 - 特征重要性识别
    5. 融合特征聚类分析 - 综合模态信息
    """

    print("\n" + "=" * 80)
    print("多模态关联分析 - 专注于多模态关联分析")
    print("=" * 80)

    # ========== 第一步：自定义数据配置 ==========
    print("\n【第一步】自定义数据配置")
    print("-" * 80)

    custom_config = DataConfig(
        n_samples=300,
        n_features_per_modality={
            'sensor': 25,
            'image': 20,
            'text': 30,
            'audio': 18
        },
        n_classes=4,
        noise_level=0.12,
        missing_rate=0.06,
        outlier_rate=0.04,
        class_balance=[0.40, 0.30, 0.20, 0.10],
        concept_drift=False,
        temporal_dependence=False,
        random_state=42
    )

    print(f"\n数据生成配置：")
    print(f"  样本数：{custom_config.n_samples}")
    print(f"  模态配置：{custom_config.n_features_per_modality}")
    print(f"  类别数：{custom_config.n_classes}")
    print(f"  噪声水平：{custom_config.noise_level}")
    print(f"  缺失值率：{custom_config.missing_rate}")
    print(f"  异常值率：{custom_config.outlier_rate}")
    print(f"  类别分布：{custom_config.class_balance}")

    # ========== 第二步：生成数据 ==========
    print("\n【第二步】生成多模态数据")
    print("-" * 80)

    generator = DataGen(custom_config)
    data = generator.generate()
    feature_names = generator.generate_feature_names()

    print(f"\n生成的数据形状：")
    for modality_name, modality_data in data.items():
        if modality_name != 'labels':
            print(f"  {modality_name}: {modality_data.shape}")

    # 保存数据
    output_dir = Path('./res/multimodal')
    output_dir.mkdir(parents=True, exist_ok=True)
    generator.save_data(data, str(output_dir))

    # ========== 第三步：创建 Multimodal 实例 ==========
    print("\n【第三步】创建 Multimodal 分析实例")
    print("-" * 80)

    ma = Multimodal(random_state=42)

    # 添加模态数据（含缺失值处理）
    print(f"\n正在添加模态数据...")
    modality_features = {}
    for modality_name, modality_data in data.items():
        if modality_name != 'labels':
            # 处理缺失值：使用均值填充
            mod_data_clean = modality_data.copy()
            if np.isnan(mod_data_clean).any():
                col_means = np.nanmean(mod_data_clean, axis=0)
                for i in range(mod_data_clean.shape[1]):
                    mask = np.isnan(mod_data_clean[:, i])
                    mod_data_clean[mask, i] = col_means[i]
                print(f"  {modality_name}：已填充 {np.isnan(modality_data).sum()} 个缺失值")

            ma.add_modality(mod_data_clean, modality_name, normalize=True)
            modality_features[modality_name] = list(feature_names[modality_name])
            print(f"  已添加 {modality_name} 模态（{mod_data_clean.shape[1]} 维）")

    # 获取模态名称列表
    modality_names = list(ma.modalities.keys())
    print(f"\n模态列表：{modality_names}")

    # ========== 第四步：典型相关分析（CCA）- 核心关联分析 ==========
    print("\n【第四步】典型相关分析（CCA）- 模态间关联深度分析")
    print("-" * 80)

    # 定义模态对进行 CCA 分析
    modality_pairs = [
        ('sensor', 'image', '传感器-图像'),
        ('text', 'audio', '文本-音频'),
        ('sensor', 'text', '传感器-文本'),
        ('image', 'audio', '图像-音频')
    ]

    cca_results = {}
    cca_correlations = {}

    print("\n执行典型相关分析...")
    for mod1, mod2, pair_name in modality_pairs:
        if mod1 in ma.modalities and mod2 in ma.modalities:
            print(f"\n  分析模态对：{pair_name} ({mod1} <-> {mod2})")

            # 执行 CCA
            X_scores, Y_scores, X_loadings, Y_loadings = ma.cca(
                mod1, mod2, n_components=3
            )
            correlations = ma.get_cca(mod1, mod2, n_components=3)

            # 存储结果
            cca_results[pair_name] = {
                'correlations': correlations,
                'X_scores': X_scores,
                'Y_scores': Y_scores,
                'X_loadings': X_loadings,
                'Y_loadings': Y_loadings
            }
            cca_correlations[pair_name] = correlations[0]  # 第一典型相关系数

            print(f"    典型相关系数：{[f'{c:.4f}' for c in correlations]}")

    # ========== 第五步：跨模态相似度分析 ==========
    print("\n【第五步】跨模态相似度分析")
    print("-" * 80)

    # 使用三种方法计算跨模态相似度
    similarity_methods = ['cosine', 'pearson', 'euclidean']
    similarity_results = {}

    for method in similarity_methods:
        print(f"\n  计算方法：{method}")
        sim_dict = ma.cross(method=method, store=True)

        # 计算各模态对的平均相似度
        pair_similarities = {}
        for i, name1 in enumerate(modality_names):
            for name2 in modality_names[i + 1:]:
                pair_name = f'{name1}-{name2}'
                sim_matrix = sim_dict[(name1, name2)]
                
                # 对角线元素（同个体）的相似度
                diag_sim = np.diag(sim_matrix)
                pair_similarities[pair_name] = {
                    'overall_mean': sim_matrix.mean(),
                    'diag_mean': diag_sim.mean(),
                    'diag_std': diag_sim.std()
                }
                
                print(f"    {pair_name}:")
                print(f"      整体均值: {sim_matrix.mean():.4f}")
                print(f"      同个体均值: {diag_sim.mean():.4f}")

        similarity_results[method] = pair_similarities

    # ========== 第六步：多模态融合方法对比 ==========
    print("\n【第六步】多模态融合方法对比")
    print("-" * 80)

    fusion_results = {}
    fusion_methods = ['concat', 'average', 'weighted']

    for method in fusion_methods:
        print(f"\n  {method.upper()} 融合方法：")

        fused = ma.fuse(fusion_method=method)
        print(f"    融合后形状：{fused.shape}")

        fusion_results[method] = fused

    # ========== 第七步：基于融合特征的聚类分析 ==========
    print("\n【第七步】基于融合特征的聚类分析")
    print("-" * 80)

    cluster_comparison = {}
    true_labels = data['labels'].ravel()

    for method, fused_data in fusion_results.items():
        print(f"\n  使用 {method.upper()} 融合特征聚类：")

        cluster_model = ma.cluster_fusion(
            n_clusters=4,
            data=fused_data,
            init='k-means++',
            n_init=10,
            max_iter=300
        )

        cluster_labels = cluster_model.labels
        silhouette = cluster_model.get_silhouette_score()
        inertia = cluster_model.get_inertia()
        ari = adjusted_rand_score(true_labels, cluster_labels)

        cluster_comparison[method] = {
            'model': cluster_model,
            'labels': cluster_labels,
            'silhouette': silhouette,
            'inertia': inertia,
            'ari': ari
        }

        print(f"    轮廓系数：{silhouette:.4f}")
        print(f"    惯性值：{inertia:.4f}")
        print(f"    调整兰德指数：{ari:.4f}")

    # ========== 第八步：生成多模态关联分析可视化 ==========
    print("\n【第八步】生成多模态关联分析可视化")
    print("-" * 80)

    viz = Plotter(theme='report')

    # 图表1：典型相关系数对比柱状图
    print("\n  生成图表1：典型相关系数对比")
    pair_names = list(cca_correlations.keys())
    corr_values = list(cca_correlations.values())

    viz.bar(
        x=pair_names,
        y=corr_values,
        colors=['#4A90E2'] * len(pair_names),
        title='各模态对典型相关系数对比（第一成分）',
        xlabel='模态对',
        ylabel='典型相关系数',
        save_path=str(output_dir / '01_典型相关系数对比.png'),
        show=False
    )
    plt.close()
    print("  ✓ 图表已保存：01_典型相关系数对比.png")

    # 图表2：跨模态相似度热力图（余弦）
    print("\n  生成图表2：跨模态余弦相似度热力图")
    n_modalities = len(modality_names)
    cosine_heatmap = np.zeros((n_modalities, n_modalities))

    cosine_dict = similarity_results['cosine']
    for i, name1 in enumerate(modality_names):
        for j, name2 in enumerate(modality_names):
            if i == j:
                cosine_heatmap[i, j] = 1.0
            elif i < j:
                pair_name = f'{name1}-{name2}'
                cosine_heatmap[i, j] = cosine_dict[pair_name]['diag_mean']
                cosine_heatmap[j, i] = cosine_dict[pair_name]['diag_mean']

    viz.heatmap(
        data=cosine_heatmap,
        xticklabels=modality_names,
        yticklabels=modality_names,
        title='跨模态余弦相似度热力图（同个体）',
        save_path=str(output_dir / '02_跨模态余弦相似度热力图.png'),
        show=False
    )
    plt.close()
    print("  ✓ 图表已保存：02_跨模态余弦相似度热力图.png")

    # 图表3：不同相似度方法对比
    print("\n  生成图表3：不同相似度方法对比")
    methods = list(similarity_results.keys())
    
    # 计算每种方法的平均相似度
    method_avg_sims = []
    for method in methods:
        pair_sims = [v['diag_mean'] for v in similarity_results[method].values()]
        method_avg_sims.append(np.mean(pair_sims))

    viz.bar(
        x=methods,
        y=method_avg_sims,
        colors=['#4A90E2', '#50E3C2', '#F5A623'],
        title='不同相似度计算方法对比',
        xlabel='相似度方法',
        ylabel='平均相似度',
        save_path=str(output_dir / '03_不同相似度方法对比.png'),
        show=False
    )
    viz.close()
    print("  ✓ 图表已保存：03_不同相似度方法对比.png")

    # 图表4：CCA 得分散点图（传感器-图像）
    print("\n  生成图表4：CCA 得分散点图（传感器-图像）")
    if '传感器-图像' in cca_results:
        result = cca_results['传感器-图像']
        X_scores = result['X_scores']
        Y_scores = result['Y_scores']
        corr = result['correlations'][0]


        fig, ax = viz.scatter(
            x=X_scores[:, 0].tolist(),
            y=Y_scores[:, 0].tolist(),
            title='传感器-图像模态 CCA 得分散点图',
            xlabel='传感器模态第一典型变量',
            ylabel='图像模态第一典型变量',
            show=False,
            grid=False,
            c=true_labels,
            cmap='tab10',

        )
        #
        # 添加相关系数标注
        ax.text(0.05, 0.95, f'典型相关系数: {corr:.4f}',
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        #
        # # 添加颜色条
        scatter = ax.collections[0]
        fig = ax.figure
        cbar = fig.colorbar(scatter)
        cbar.set_label('类别', fontsize=11)
        #
        # plt.tight_layout()
        plt.savefig(output_dir / '04_CCA得分散点图(传感器-图像).png', dpi=300, bbox_inches='tight')
        # plt.close()
        viz.close()
    print("  ✓ 图表已保存：04_CCA得分散点图(传感器-图像).png")

    # 图表5：CCA 得分散点图（文本-音频）
    print("\n  生成图表5：CCA 得分散点图（文本-音频）")
    if '文本-音频' in cca_results:
        result = cca_results['文本-音频']
        X_scores = result['X_scores']
        Y_scores = result['Y_scores']
        corr = result['correlations'][0]

        fig, ax = viz.scatter(
            x=X_scores[:, 0].tolist(),
            y=Y_scores[:, 0].tolist(),
            color=None,
            title='文本-音频模态 CCA 得分散点图',
            xlabel='文本模态第一典型变量',
            ylabel='音频模态第一典型变量',
            show=False,
            grid=False,
            c=true_labels,
            cmap='tab10'
        )


        # 添加相关系数标注
        ax.text(0.05, 0.95, f'典型相关系数: {corr:.4f}',
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # 添加颜色条
        scatter = ax.collections[0]
        fig = ax.figure
        cbar = fig.colorbar(scatter)
        cbar.set_label('类别', fontsize=11)
        plt.savefig(output_dir / '05_CCA得分散点图(文本-音频).png',)
        viz.close()
    print("  ✓ 图表已保存：05_CCA得分散点图(文本-音频).png")

    # 图表6：CCA 载荷分析图（传感器-图像）
    print("\n  生成图表6：CCA 载荷分析图（传感器-图像）")
    if '传感器-图像' in cca_results:
        result = cca_results['传感器-图像']
        X_loadings = result['X_loadings']
        Y_loadings = result['Y_loadings']

        # 获取前10个最重要的特征
        sensor_features = modality_features['sensor']
        image_features = modality_features['image']

        # 第一典型变量的载荷
        X_importance = np.abs(X_loadings[:, 0])
        Y_importance = np.abs(Y_loadings[:, 0])

        # 选择前10个
        top_n = min(10, len(sensor_features))
        X_top_idx = np.argsort(X_importance)[::-1][:top_n]
        Y_top_idx = np.argsort(Y_importance)[::-1][:top_n]

        viz.create_subplots(nrows=1, ncols=2, figsize=(16, 6))

        # 传感器模态载荷
        ax1 = viz.figure_manager.get_ax(position=0)
        ax1.barh(range(top_n), X_importance[X_top_idx], color='#4A90E2')
        ax1.set_yticks(range(top_n))
        ax1.set_yticklabels([sensor_features[i][:15] for i in X_top_idx], fontsize=10)
        ax1.set_xlabel('载荷绝对值', fontsize=11)
        ax1.set_title('传感器模态特征重要性（前10）', fontsize=12, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)

        # 图像模态载荷
        ax2 = viz.figure_manager.get_ax(position=1)
        ax2.barh(range(top_n), Y_importance[Y_top_idx], color='#50E3C2')
        ax2.set_yticks(range(top_n))
        ax2.set_yticklabels([image_features[i][:15] for i in Y_top_idx], fontsize=10)
        ax2.set_xlabel('载荷绝对值', fontsize=11)
        ax2.set_title('图像模态特征重要性（前10）', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / '06_CCA载荷分析(传感器-图像).png', 
                   dpi=300, bbox_inches='tight')
        viz.close()
    print("  ✓ 图表已保存：06_CCA载荷分析(传感器-图像).png")

    # 图表7：不同融合方法聚类效果对比
    print("\n  生成图表7：不同融合方法聚类效果对比")
    fusion_methods_for_plot = list(cluster_comparison.keys())
    fusion_silhouettes = [cluster_comparison[m]['silhouette'] for m in fusion_methods_for_plot]
    fusion_aris = [cluster_comparison[m]['ari'] for m in fusion_methods_for_plot]

    x = np.arange(len(fusion_methods_for_plot))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width / 2, fusion_silhouettes, width, 
                   label='轮廓系数', color='#4A90E2')
    bars2 = ax.bar(x + width / 2, fusion_aris, width, 
                   label='调整兰德指数', color='#50E3C2')

    ax.set_xlabel('融合方法', fontsize=12)
    ax.set_ylabel('评估指标值', fontsize=12)
    ax.set_title('不同融合方法聚类效果对比', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['简单拼接', '降维平均', '加权融合'])
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    # 添加数值标注
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_dir / '07_不同融合方法聚类效果对比.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：07_不同融合方法聚类效果对比.png")

    # 图表8：各模态对相似度对比（多方法）
    print("\n  生成图表8：各模态对相似度对比（多方法）")
    
    # 获取所有模态对
    pair_names_list = []
    cosine_sims = []
    pearson_sims = []
    euclidean_sims = []

    for i, name1 in enumerate(modality_names):
        for name2 in modality_names[i + 1:]:
            pair_name = f'{name1}-{name2}'
            pair_names_list.append(pair_name)
            cosine_sims.append(similarity_results['cosine'][pair_name]['diag_mean'])
            pearson_sims.append(similarity_results['pearson'][pair_name]['diag_mean'])
            euclidean_sims.append(similarity_results['euclidean'][pair_name]['diag_mean'])

    x = np.arange(len(pair_names_list))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width, cosine_sims, width, label='余弦', color='#4A90E2')
    bars2 = ax.bar(x, pearson_sims, width, label='皮尔逊', color='#50E3C2')
    bars3 = ax.bar(x + width, euclidean_sims, width, label='欧氏', color='#F5A623')

    ax.set_xlabel('模态对', fontsize=12)
    ax.set_ylabel('相似度', fontsize=12)
    ax.set_title('各模态对相似度对比（不同方法）', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(pair_names_list, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / '08_各模态对相似度对比.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：08_各模态对相似度对比.png")

    # 图表9：PCA 降维后的模态数据分布
    print("\n  生成图表9：PCA 降维后的模态数据分布")
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.ravel()

    for idx, modality_name in enumerate(modality_names):
        ax = axes[idx]
        mod_data = ma.modalities[modality_name]
        
        # 使用 ModalityData 的 pca 方法进行降维
        if mod_data.data.shape[1] > 2:
            pca_2d = mod_data.pca(2)
        else:
            pca_2d = mod_data.data

        # 直接在子图上绘制散点图
        scatter = ax.scatter(pca_2d[:, 0], pca_2d[:, 1],
                            c=true_labels, cmap='tab10', alpha=0.6,
                            edgecolors='white', linewidth=0.5)
        ax.set_xlabel('第一主成分', fontsize=10)
        ax.set_ylabel('第二主成分', fontsize=10)
        ax.set_title(f'{modality_name} 模态 PCA 降维', fontsize=11, fontweight='bold')
        ax.grid(False)

    plt.tight_layout()
    plt.savefig(output_dir / '09_PCA降维后的模态数据分布.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：09_PCA降维后的模态数据分布.png")

    # 图表10：最佳融合方法的聚类混淆矩阵
    print("\n  生成图表10：最佳融合方法的聚类混淆矩阵")
    
    # 找到 ARI 最高的融合方法
    best_method = max(cluster_comparison.keys(), 
                     key=lambda k: cluster_comparison[k]['ari'])
    best_cluster_labels = cluster_comparison[best_method]['labels']
    
    conf_matrix = confusion_matrix(true_labels, best_cluster_labels)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
               xticklabels=[f'聚类{i}' for i in range(conf_matrix.shape[1])],
               yticklabels=[f'类别{i}' for i in range(conf_matrix.shape[0])],
               annot_kws={'size': 14}, cbar_kws={'label': '样本数量'},
               ax=ax)
    ax.set_xlabel('预测聚类标签', fontsize=12, fontweight='bold')
    ax.set_ylabel('真实类别标签', fontsize=12, fontweight='bold')
    ax.set_title(f'聚类混淆矩阵（{best_method.upper()} 融合）', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / '10_聚类混淆矩阵.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：10_聚类混淆矩阵.png")

    # 图表11：所有模态对的典型相关系数对比（多个成分）
    print("\n  生成图表11：所有模态对的典型相关系数对比")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(cca_results))
    width = 0.25
    
    # 获取前3个典型相关系数
    correlations_comp1 = [result['correlations'][0] if len(result['correlations']) > 0 else 0 
                         for result in cca_results.values()]
    correlations_comp2 = [result['correlations'][1] if len(result['correlations']) > 1 else 0 
                         for result in cca_results.values()]
    correlations_comp3 = [result['correlations'][2] if len(result['correlations']) > 2 else 0 
                         for result in cca_results.values()]
    
    bars1 = ax.bar(x - width, correlations_comp1, width, label='第一成分', color='#4A90E2')
    bars2 = ax.bar(x, correlations_comp2, width, label='第二成分', color='#50E3C2')
    bars3 = ax.bar(x + width, correlations_comp3, width, label='第三成分', color='#F5A623')
    
    ax.set_xlabel('模态对', fontsize=12)
    ax.set_ylabel('典型相关系数', fontsize=12)
    ax.set_title('所有模态对的典型相关系数对比（多成分）', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(list(cca_results.keys()), rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '11_所有模态对典型相关系数对比.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    viz.close()
    print("  ✓ 图表已保存：11_所有模态对典型相关系数对比.png")

    # 图表12：融合特征空间的可视化（最佳方法）
    print("\n  生成图表12：融合特征空间的可视化（最佳方法）")
    
    # 使用最佳融合方法
    best_fused_data = fusion_results[best_method]
    
    # 创建临时的 ModalityData 对象来使用其 pca 方法
    from ljp_page.data_analysis.ml.multimodal.multimodal import ModalityData
    fused_modality = ModalityData(best_fused_data, 'fused')
    fused_modality.normalize(method='minmax')
    fused_2d = fused_modality.pca(2)
    
    fig, ax = viz.scatter(
        x=fused_2d[:, 0].tolist(),
        y=fused_2d[:, 1].tolist(),
        color=None,
        title=f'融合特征空间可视化（{best_method.upper()} 融合 + K-Means）',
        xlabel='第一主成分',
        ylabel='第二主成分',
        show=False,
        grid=False,
        c=best_cluster_labels,
        cmap='tab10',
    )
    
    # 添加颜色条
    scatter = ax.collections[0]
    fig = ax.figure
    cbar = fig.colorbar(scatter)
    cbar.set_label('聚类标签', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_dir / '12_融合特征空间可视化.png', dpi=300, bbox_inches='tight')
    viz.close()
    print("  ✓ 图表已保存：12_融合特征空间可视化.png")

    # 图表13：模态间相关性热力图
    print("\n  生成图表13：模态间相关性热力图")
    
    # 计算模态间相关性矩阵
    n_modalities = len(modality_names)
    correlation_matrix = np.zeros((n_modalities, n_modalities))
    
    for i, mod1 in enumerate(modality_names):
        for j, mod2 in enumerate(modality_names):
            if i == j:
                correlation_matrix[i, j] = 1.0
            elif i < j:
                # 使用 Pearson 相似度的对角线均值作为相关性
                if f'{mod1}-{mod2}' in similarity_results['pearson']:
                    corr = similarity_results['pearson'][f'{mod1}-{mod2}']['diag_mean']
                    correlation_matrix[i, j] = corr
                    correlation_matrix[j, i] = corr
                elif f'{mod2}-{mod1}' in similarity_results['pearson']:
                    corr = similarity_results['pearson'][f'{mod2}-{mod1}']['diag_mean']
                    correlation_matrix[i, j] = corr
                    correlation_matrix[j, i] = corr
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                xticklabels=modality_names,
                yticklabels=modality_names,
                annot_kws={'size': 13}, 
                cbar_kws={'label': '皮尔逊相关系数'},
                vmin=-0.5, vmax=1.0, linewidths=1, linecolor='white',
                ax=ax)
    ax.set_title('各模态间相关性热力图', fontsize=15, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(output_dir / '13_模态间相关性热力图.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：13_模态间相关性热力图.png")

    # 图表14：t-SNE 降维可视化（融合特征）
    print("\n  生成图表14：t-SNE 降维可视化（融合特征）")
    
    try:
        from sklearn.manifold import TSNE
        
        # 使用最佳融合方法进行 t-SNE
        best_fused_data = fusion_results[best_method]
        
        # t-SNE 降维到 2D
        tsne = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=1000)
        tsne_2d = tsne.fit_transform(best_fused_data)
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 左图：真实标签
        scatter1 = axes[0].scatter(tsne_2d[:, 0], tsne_2d[:, 1], 
                                  c=true_labels, cmap='tab10', 
                                  alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
        axes[0].set_xlabel('t-SNE 第一维度', fontsize=12)
        axes[0].set_ylabel('t-SNE 第二维度', fontsize=12)
        axes[0].set_title('真实标签分布', fontsize=14, fontweight='bold')
        cbar1 = plt.colorbar(scatter1, ax=axes[0])
        cbar1.set_label('真实类别', fontsize=11)
        axes[0].grid(False)
        
        # 右图：聚类标签
        scatter2 = axes[1].scatter(tsne_2d[:, 0], tsne_2d[:, 1], 
                                  c=best_cluster_labels, cmap='tab10', 
                                  alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
        axes[1].set_xlabel('t-SNE 第一维度', fontsize=12)
        axes[1].set_ylabel('t-SNE 第二维度', fontsize=12)
        axes[1].set_title('聚类结果分布', fontsize=14, fontweight='bold')
        cbar2 = plt.colorbar(scatter2, ax=axes[1])
        cbar2.set_label('聚类标签', fontsize=11)
        axes[1].grid(False)
        
        plt.suptitle(f'融合特征 t-SNE 可视化（{best_method.upper()} 融合）', 
                    fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        save_path = output_dir / '14_tSNE降维可视化.png'
        plt.savefig(str(save_path), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ 图表已保存：14_tSNE降维可视化.png")
    except ImportError:
        print("  ⚠ sklearn.manifold.TSNE 不可用，跳过 t-SNE 可视化")

    # 图表15：多模态对的 CCA 得分散点图
    print("\n 生成图表15：多模态对的 CCA 得分散点图")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.ravel()
    
    colors_list = plt.cm.tab10(np.linspace(0, 1, custom_config.n_classes))
    
    for idx, (pair_name, result) in enumerate(cca_results.items()):
        if idx >= 4:
            break
        ax = axes[idx]
        
        X_scores = result['X_scores']
        Y_scores = result['Y_scores']
        corr = result['correlations'][0]
        
        # 使用辅助函数绘制散点图
        plot_cca_scatter(
            ax=ax,
            X_scores=X_scores,
            Y_scores=Y_scores,
            true_labels=true_labels,
            corr=corr,
            xlabel='第一模态典型变量',
            ylabel='第二模态典型变量',
            title=f'{pair_name}\n典型相关系数: {corr:.4f}',
            colors_list=colors_list,
            n_classes=custom_config.n_classes
        )
    
    plt.suptitle('各模态对 CCA 得分散点图', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '15_多模态对CCA得分图.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：15_多模态对CCA得分图.png")

    # 图表16：类别分布饼图
    print("\n  生成图表16：类别分布饼图")
    
    label_counts = np.bincount(true_labels, minlength=custom_config.n_classes)
    label_names_cn = [f'类别{i}' for i in range(custom_config.n_classes)]
    colors_pie = ['#4A90E2', '#50E3C2', '#F5A623', '#D0021B'][:custom_config.n_classes]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(label_counts,
                                      labels=label_names_cn,
                                      colors=colors_pie,
                                      autopct='%1.1f%%',
                                      startangle=90,
                                      textprops={'fontsize': 12})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(13)
    
    ax.set_title('数据类别分布', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / '16_类别分布饼图.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：16_类别分布饼图.png")

    # 图表17：各模态特征分布箱线图
    print("\n  生成图表17：各模态特征分布箱线图")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.ravel()
    
    for idx, modality_name in enumerate(modality_names):
        ax = axes[idx]
        mod_data = ma.modalities[modality_name].data
        
        # 选择前 10 个特征进行可视化
        n_features_show = min(10, mod_data.shape[1])
        data_to_plot = [mod_data[:, i] for i in range(n_features_show)]
        
        bp = ax.boxplot(data_to_plot, tick_labels=[f'F{i+1}' for i in range(n_features_show)],
                       patch_artist=True, showmeans=True)
        
        # 设置箱线图颜色
        for patch, color in zip(bp['boxes'], plt.cm.viridis(np.linspace(0, 1, n_features_show))):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        ax.set_xlabel('特征编号', fontsize=11)
        ax.set_ylabel('特征值', fontsize=11)
        ax.set_title(f'{modality_name} 模态特征分布（前10维）', 
                    fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
    
    plt.suptitle('各模态特征分布箱线图', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '17_各模态特征分布箱线图.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存：17_各模态特征分布箱线图.png")

    # ========== 第九步：生成分析报告 ==========
    print("\n【第九步】生成分析报告")
    print("-" * 80)

    report_path = output_dir / '多模态关联分析报告.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('# 多模态关联分析报告\n\n')
        f.write('## 一、分析概述\n\n')
        f.write('本报告专注于多模态关联分析，重点分析不同模态之间的关联性、\n')
        f.write('相似性以及融合效果，为多模态数据的综合利用提供深度见解。\n\n')

        f.write('## 二、数据配置\n\n')
        f.write(f'- 样本数：{custom_config.n_samples}\n')
        f.write(f'- 模态数：{len(custom_config.n_features_per_modality)}\n')
        f.write(f'- 模态配置：{custom_config.n_features_per_modality}\n')
        f.write(f'- 类别数：{custom_config.n_classes}\n\n')

        f.write('## 三、典型相关分析（CCA）结果\n\n')
        f.write('CCA 是分析两个模态之间线性关联关系的核心方法。\n\n')
        for pair_name, result in cca_results.items():
            f.write(f'### {pair_name}\n')
            f.write(f'- 典型相关系数：{result["correlations"]}\n')
            f.write(f'- 第一成分相关系数：{result["correlations"][0]:.4f}\n\n')

        f.write('## 四、跨模态相似度分析\n\n')
        f.write('### 余弦相似度\n')
        for pair_name, metrics in similarity_results['cosine'].items():
            f.write(f'- {pair_name}: {metrics["diag_mean"]:.4f} (同个体均值)\n')
        f.write('\n')

        f.write('### Pearson 相关性\n')
        for pair_name, metrics in similarity_results['pearson'].items():
            f.write(f'- {pair_name}: {metrics["diag_mean"]:.4f} (同个体均值)\n')
        f.write('\n')

        f.write('### 欧氏距离相似度\n')
        for pair_name, metrics in similarity_results['euclidean'].items():
            f.write(f'- {pair_name}: {metrics["diag_mean"]:.4f} (同个体均值)\n')
        f.write('\n')

        f.write('## 五、融合方法聚类效果对比\n\n')
        for method, metrics in cluster_comparison.items():
            f.write(f'### {method.upper()} 融合\n')
            f.write(f'- 轮廓系数：{metrics["silhouette"]:.4f}\n')
            f.write(f'- 调整兰德指数：{metrics["ari"]:.4f}\n')
            f.write(f'- 惯性值：{metrics["inertia"]:.4f}\n\n')

        f.write('## 六、关键发现\n\n')
        
        # 找出关联最强的模态对
        max_corr_pair = max(cca_correlations.items(), key=lambda x: x[1])
        f.write(f'1. **最强模态关联**：{max_corr_pair[0]} 模态对的典型相关系数最高（{max_corr_pair[1]:.4f}），\n')
        f.write(f'   表明这两个模态之间存在最强的线性关联关系。\n\n')
        
        # 找出最佳融合方法
        best_fusion = max(cluster_comparison.items(), key=lambda x: x[1]['ari'])
        f.write(f'2. **最佳融合方法**：{best_fusion[0].upper()} 融合方法的聚类效果最好，\n')
        f.write(f'   调整兰德指数为 {best_fusion[1]["ari"]:.4f}。\n\n')
        
        # 找出最相似的模态对
        max_sim_pair = max(similarity_results['cosine'].items(), 
                          key=lambda x: x[1]['diag_mean'])
        f.write(f'3. **最相似模态对**：{max_sim_pair[0]} 的余弦相似度最高（{max_sim_pair[1]["diag_mean"]:.4f}），\n')
        f.write(f'   表明这两个模态在样本层面最为相似。\n\n')

        f.write('## 七、可视化图表\n\n')
        f.write('本次分析生成了 17 张多模态关联分析图表，涵盖多个维度的关联分析：\n\n')
        f.write('**核心关联分析图表**：\n')
        f.write('1. 典型相关系数对比 - 各模态对第一典型相关系数对比\n')
        f.write('2. 跨模态余弦相似度热力图 - 模态间余弦相似度矩阵\n')
        f.write('3. 不同相似度方法对比 - 余弦、Pearson、欧氏三种方法对比\n')
        f.write('4. CCA 得分散点图（传感器-图像） - 传感器与图像模态的关联可视化\n')
        f.write('5. CCA 得分散点图（文本-音频） - 文本与音频模态的关联可视化\n')
        f.write('6. CCA 载荷分析（传感器-图像） - 特征重要性识别\n')
        f.write('11. 所有模态对的典型相关系数对比（多成分） - 多成分 CCA 对比\n')
        f.write('13. 模态间相关性热力图 - 各模态间皮尔逊相关系数\n')
        f.write('15. 多模态对 CCA 得分散点图 - 所有模态对的 CCA 结果对比\n\n')
        
        f.write('**融合与聚类分析图表**：\n')
        f.write('7. 不同融合方法聚类效果对比 - 轮廓系数与 ARI 对比\n')
        f.write('8. 各模态对相似度对比（多方法） - 各模态对的相似度对比\n')
        f.write('9. PCA 降维后的模态数据分布 - 各模态 PCA 投影\n')
        f.write('10. 聚类混淆矩阵 - 最佳融合方法的聚类效果\n')
        f.write('12. 融合特征空间可视化 - 最佳融合方法的 PCA 可视化\n')
        f.write('14. t-SNE 降维可视化 - 融合特征的 t-SNE 非线性降维\n\n')
        
        f.write('**数据分布分析图表**：\n')
        f.write('16. 类别分布饼图 - 数据类别分布情况\n')
        f.write('17. 各模态特征分布箱线图 - 各模态特征的统计分布\n\n')

    print(f"  分析报告已保存：{report_path}")

    # ========== 完成 ==========
    print("\n" + "=" * 80)
    print("✓ 多模态关联分析完成！")
    print(f"✓ 共生成 17 张可视化图表")
    print(f"✓ 数据已保存至：{output_dir}")
    print(f"✓ 分析报告已保存至：{report_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()
