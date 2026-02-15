# 生成时间: 02-10-22-53-15
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix
import seaborn as sns

from multimodal import *
from sklearn.metrics import adjusted_rand_score
from ljp_page._ljp_data_analysis.visualization.matplotlib import Matplotlib
viz = Matplotlib()

def visualize_data_overview(modality_info, true_labels, output_dir):
    print("  生成健康状态分布饼图")
    label_counts = [np.sum(true_labels == i) for i in range(3)]
    label_names_cn = ['健康', '亚健康', '疾病风险']
    colors = ['#4A90E2', '#F5A623', '#D0021B']

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
    plt.savefig(output_dir / '01_健康状态分布.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 01_健康状态分布.png")

    viz.pie(
        label_counts,
        labels=label_names_cn,
        title= '健康状态分布',
        save_path=output_dir/ '01_健康状态分布2.png'
    )
    viz.close()


def analyze_cca(ma, modality_pairs, modality_info, output_dir):
    print("\n[步骤三] 模态关联分析（CCA）")
    print("  分析各模态之间的跨模态关联...")

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

    # 可视化典型相关系数
    print("  生成图表: 多模态典型相关系数对比")
    modality_pair_names = list(cca_results.keys())
    correlations = [cca_results[pair]['correlations'][0] for pair in modality_pair_names]

    viz = Matplotlib()
    viz.bar(modality_pair_names, correlations,
            title='多模态典型相关系数对比',
            xlabel='模态对',
            ylabel='第一典型相关系数',
            save_path=output_dir / '02_多模态典型相关系数对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 02_多模态典型相关系数对比.png")

    # CCA载荷分析
    print("\n  CCA载荷分析（特征重要性）...")
    for pair_name, result in cca_results.items():
        print(f"  【{pair_name}】")
        X_loadings = result['X_loadings']
        Y_loadings = result['Y_loadings']

        mod1_name, mod2_name = None, None
        for mod1, mod2, display_name in modality_pairs:
            if display_name == pair_name:
                mod1_name, mod2_name = mod1, mod2
                break

        if mod1_name and mod2_name:
            mod1_features = modality_info[mod1_name]['features']
            mod2_features = modality_info[mod2_name]['features']

            X_importance = np.abs(X_loadings[:, 0])
            Y_importance = np.abs(Y_loadings[:, 0])

            X_top_idx = np.argsort(X_importance)[::-1][:3]
            Y_top_idx = np.argsort(Y_importance)[::-1][:3]

            print(f"    第一模态前3重要特征: {[mod1_features[i] for i in X_top_idx]}")
            print(f"    第二模态前3重要特征: {[mod2_features[i] for i in Y_top_idx]}")

    return cca_results


def analyze_cross_modality_similarity(ma, output_dir):
    print("\n[步骤四] 跨模态相似度分析")
    print("  评估各模态之间的跨模态预测能力...")

    # 详细分析各模态对相似度
    print("\n  4.1 各模态对相似度详细分析...")
    similarity_dict = ma.cross(method='cosine', store=True)
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

    # 可视化各模态对相似度
    print("  生成图表: 各模态对跨模态相似度对比")
    pair_names = [item['pair'] for item in modality_pair_analysis]
    diag_means = [item['diag_mean'] for item in modality_pair_analysis]
    diag_stds = [item['diag_std'] for item in modality_pair_analysis]

    viz = Matplotlib()
    viz.bar(pair_names, diag_means,
            yerr=diag_stds,
            title='各模态对跨模态相似度对比',
            xlabel='模态对',
            ylabel='同个体相似度均值',
            save_path=output_dir / '03_跨模态相似度对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 03_跨模态相似度对比.png")

    # 不同相似度方法对比
    print("\n  4.2 不同相似度计算方法对比...")
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
        print(f"    同个体均值: {np.mean(diag_sims):.4f}")
        print(f"    同个体标准差: {np.std(diag_sims):.4f}")

    # 可视化不同方法对比
    print("  生成图表: 不同相似度计算方法对比")
    methods = list(method_comparison.keys())
    method_diag_means = [method_comparison[m]['diag_mean'] for m in methods]
    method_diag_stds = [method_comparison[m]['diag_std'] for m in methods]

    viz = Matplotlib()
    viz.bar(methods, method_diag_means,
            yerr=method_diag_stds,
            title='不同相似度计算方法对比',
            xlabel='计算方法',
            ylabel='同个体相似度均值',
            save_path=output_dir / '04_不同相似度方法对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 04_不同相似度方法对比.png")

    return method_comparison


def analyze_feature_fusion_and_clustering(ma, true_labels, output_dir):
    print("\n[步骤五] 特征融合与聚类分析")
    print("  将四个模态的特征融合为统一表示并进行聚类...")

    # 多种融合方法对比
    fusion_method = {'concat': '简单拼接', 'average': '降维平均', 'weighted': '加权融合'}
    fusion_results = {}

    for method in fusion_method.keys():
        fused_features = ma.fuse(fusion_method=method)
        fusion_results[method] = fused_features
        print(f"  {fusion_method[method]}融合后特征维度: {fused_features.shape}")

    # 各融合方法聚类效果对比
    print("\n  5.1 不同融合方法聚类效果对比...")
    fusion_comparison = {}
    for method, features in fusion_results.items():
        cluster_model = ma.cluster_fusion(n_clusters=3, data=features, init='k-means++', max_iter=300)
        ari = adjusted_rand_score(true_labels, cluster_model.labels)
        silhouette = cluster_model.get_silhouette_score()
        inertia = cluster_model.get_inertia()
        fusion_comparison[method] = {
            'ari': ari,
            'silhouette': silhouette,
            'inertia': inertia,
            'labels': cluster_model.labels
        }
        print(f"  {method}:")
        print(f"    调整兰德指数: {ari:.4f}")
        print(f"    轮廓系数: {silhouette:.4f}")
        print(f"    惯性值: {inertia:.4f}")

    # 选择最优融合方法进行详细分析
    best_method = 'concat'
    best_features = fusion_results[best_method]
    best_labels = fusion_comparison[best_method]['labels']

    # 可视化融合方法对比
    print("  生成图表: 不同融合方法聚类效果对比")
    fusion_methods = list(fusion_comparison.keys())
    fusion_aris = [fusion_comparison[m]['ari'] for m in fusion_methods]
    fusion_silhouettes = [fusion_comparison[m]['silhouette'] for m in fusion_methods]

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
    plt.savefig(output_dir / '05_不同融合方法聚类效果对比.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ 图表已保存: 05_不同融合方法聚类效果对比.png")

    return fusion_results, fusion_comparison, best_labels


def visualize_comprehensive_analysis(ma, modality_info, true_labels, cluster_labels,
                                     fusion_results, cca_results, output_dir):
    print("\n[步骤六] 综合分析与可视化")

    label_names_cn = ['健康', '亚健康', '疾病风险']
    colors = ['#4A90E2', '#F5A623', '#D0021B']

    # 6.1 聚类混淆矩阵
    print("  生成图表: 聚类结果与真实标签混淆矩阵")
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

    # 6.2 各模态PCA投影
    print("  生成图表: 各模态PCA降维2D投影")
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    axes = axes.ravel()

    pca = PCA(n_components=2)

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

    # 6.3 融合特征PCA可视化
    print("  生成图表: 融合特征PCA降维可视化")
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

    # 6.4 模态间相关性热力图
    print("  生成图表: 模态间相关性热力图")
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

    # 6.5 CCA典型变量得分散点图
    print("  生成图表: CCA典型变量得分散点图")
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


if __name__ == '__main__':
    # ============================================================
    # 第一部分：数据准备
    # ============================================================
    print("=" * 60)
    print("多模态健康数据关联分析")
    print("=" * 60)

    print("\n[步骤一] 数据加载与探索")
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
    label_names = {0: '健康', 1: '亚健康', 2: '疾病风险'}
    for label, count in zip(*np.unique(true_labels, return_counts=True)):
        print(f"  {label_names[label]}: {count}人 ({count / len(true_labels) * 100:.1f}%)")

    # ============================================================
    # 第二部分：多模态分析器初始化
    # ============================================================
    print("\n[步骤二] 多模态分析器初始化")
    ma = Multimodal(random_state=42)

    print("  添加四个模态数据...")
    for key in ['sensor', 'image', 'lab', 'behavior']:
        ma.add_modality(
            data_dict[key].values,
            key,
            feature_names=modality_info[key]['features'],
            normalize=True
        )

    print(f"  模态数量: {len(ma.modalities)}")
    print(f"  模态名称: {list(ma.modalities.keys())}")

    # 定义要分析的模态对
    modality_pairs = [
        ('sensor', 'image', '传感器-图像'),
        ('lab', 'behavior', '临床-行为'),
        ('sensor', 'lab', '传感器-临床'),
    ]

    # 创建输出目录
    output_dir = Path('res/figures')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 数据概览可视化
    visualize_data_overview(modality_info, true_labels, output_dir)

    # ============================================================
    # 第三部分：模态关联分析（CCA）
    # ============================================================
    cca_results = analyze_cca(ma, modality_pairs, modality_info, output_dir)

    # ============================================================
    # 第四部分：跨模态相似度分析
    # ============================================================
    method_comparison = analyze_cross_modality_similarity(ma, output_dir)

    # ============================================================
    # 第五部分：特征融合与聚类分析
    # ============================================================
    fusion_results, fusion_comparison, best_labels = analyze_feature_fusion_and_clustering(
        ma, true_labels, output_dir
    )

    # 输出最优聚类结果摘要
    print(f"\n  【最优聚类结果摘要】")
    print(f"  融合方法: 简单拼接")
    print(f"  聚类数量: {len(np.unique(best_labels))}")
    print(f"  调整兰德指数: {fusion_comparison['concat']['ari']:.4f}")
    print(f"  轮廓系数: {fusion_comparison['concat']['silhouette']:.4f}")
    print(f"  惯性值: {fusion_comparison['concat']['inertia']:.4f}")

    # ============================================================
    # 第六部分：综合分析与可视化
    # ============================================================
    visualize_comprehensive_analysis(
        ma, modality_info, true_labels, best_labels,
        fusion_results, cca_results, output_dir
    )

    # ============================================================
    # 分析完成
    # ============================================================
    print("\n" + "=" * 60)
    print("分析完成！")
    print(f"共生成 10 张图表，已保存至 {output_dir.absolute()}/ 目录")
    print("=" * 60)
