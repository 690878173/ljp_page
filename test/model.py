# 生成时间：02-02-14-45-00

"""
多模态关联分析模型 - 基于ljp_page库
结合典型相关分析、特征融合与聚类分析的多模态数据分析框架
优先使用ljp_page库中的MultimodalAssociation和Matplotlib类
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ljp_page._ljp_data_analysis.multimodal.multimodal import Multimodal
from ljp_page._ljp_data_analysis.visualization.matplotlib import Matplotlib
from sklearn.metrics import adjusted_rand_score


def generate_multimodal_sensor_image_data(n_samples=200):
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
            [[50, 8], [45, 6], [42, 7], [800, 150], [1200, 200], [115, 8], [75, 5], [36.5, 0.3], [0.3, 0.1]],  # 传感器10维
            [[230, 10], [190, 12], [180, 15], [25, 5], [28, 6], [30, 7], [40, 10], [0.85, 0.05], [0.15, 0.03], [85, 8], [0.1, 0.05]],  # 图像11维
            [[6.5, 1.2], [4.8, 0.5], [140, 10], [250, 40], [5.0, 0.6], [4.5, 0.8], [1.2, 0.3], [320, 50]],  # 临床8维
            [[10000, 2000], [60, 15], [450, 100], [7.5, 1.0], [85, 5], [5, 1], [90, 5]]  # 行为7维
        ],
        1: [  # 亚健康
            [[35, 10], [30, 8], [28, 9], [1100, 200], [700, 150], [128, 12], [82, 8], [36.8, 0.4], [0.5, 0.15]],
            [[210, 15], [175, 18], [165, 20], [32, 8], [35, 9], [38, 10], [55, 12], [0.75, 0.08], [0.10, 0.04], [65, 12], [0.25, 0.08]],
            [[7.8, 1.5], [4.5, 0.6], [135, 12], [280, 50], [5.8, 0.8], [5.2, 1.0], [1.8, 0.4], [380, 60]],
            [[7000, 2500], [40, 20], [350, 150], [6.5, 1.2], [75, 8], [3, 1], [70, 10]]
        ],
        2: [  # 疾病风险
            [[20, 12], [18, 10], [15, 8], [1500, 300], [400, 120], [145, 18], [90, 12], [37.2, 0.5], [0.8, 0.2]],
            [[180, 20], [150, 22], [140, 25], [45, 12], [48, 14], [50, 15], [75, 15], [0.60, 0.10], [0.05, 0.03], [40, 15], [0.45, 0.12]],
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


def run_comprehensive_case_study():
    """
    运行完整的案例研究：智能健康监测系统多模态分析（基于ljp_page库，四模态）
    """
    print("="*70)
    print("多模态关联分析案例：智能健康监测系统（四模态融合）")
    print("结合传感器时序、图像特征、临床检验、行为活动的综合健康分析")
    print("使用ljp_page库的MultimodalAssociation和Matplotlib类")
    print("="*70)
    
    # 1. 生成多模态数据
    print("\n[步骤1] 生成多模态健康监测数据...")
    data_dict, true_labels = generate_multimodal_sensor_image_data(n_samples=200)
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
        print(f"  {label_names[label]}: {count}人 ({count/len(true_labels)*100:.1f}%)")
    
    # 2. 初始化ljp_page库的多模态关联分析器
    print("\n[步骤2] 初始化多模态关联分析器（使用ljp_page库）...")
    ma = Multimodal(random_state=42)
    
    # 3. 添加四个模态数据
    print("\n[步骤3] 添加四个模态数据...")
    for key in ['sensor', 'image', 'lab', 'behavior']:
        ma.add_modality(
            data_dict[key].values, 
            key, 
            feature_names=modality_info[key]['features'],
            normalize=True
        )
    print(f"  模态数量: {len(ma.modalities)}")
    print(f"  模态名称: {list(ma.modalities.keys())}")
    
    # 4. 多模态典型相关分析
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
        X_scores, Y_scores, X_loadings, Y_loadings = ma.canonical_correlation_analysis(
            mod1, mod2, n_components=2
        )
        correlations = ma.get_canonical_correlations(mod1, mod2, n_components=2)
        cca_results[pair_name] = {
            'correlations': correlations,
            'X_scores': X_scores,
            'Y_scores': Y_scores,
            'X_loadings': X_loadings,
            'Y_loadings': Y_loadings
        }
        print(f"  {pair_name}典型相关系数: {[f'{c:.4f}' for c in correlations]}")
    
    # 5. 特征融合分析
    print("\n[步骤5] 执行多模态特征融合...")
    print("  将四个模态的特征融合为统一表示...")
    fusion_methods = ['concat', 'average', 'weighted']
    fusion_results = {}
    
    for method in fusion_methods:
        fused_features = ma.fuse_modalities(fusion_method=method)
        fusion_results[method] = fused_features
        method_name = {'concat': '简单拼接', 'average': '降维平均', 'weighted': '加权融合'}
        print(f"  {method_name[method]}融合后特征维度: {fused_features.shape}")
    
    # 6. 聚类分析
    print("\n[步骤6] 在融合特征空间进行聚类分析...")
    print("  基于多模态特征识别健康状态模式...")
    best_method = 'concat'
    best_features = fusion_results[best_method]
    
    # 使用ljp_page库的KmeanCluster进行聚类
    cluster_model = ma.cluster_fusion_data(n_clusters=3,data=best_features,init='k-means++',max_iter=300)
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
    
    # 7. 计算跨模态相似度
    print("\n[步骤7] 计算跨模态相似度...")
    print("  评估各模态之间的跨模态预测能力...")
    similarity_dict = ma.compute_cross_modal_similarity(method='cosine', store=True)
    
    # 计算整体跨模态平均相似度（只处理实际存在的模态对）
    valid_similarities = [similarity_dict[(i, j)].mean() 
                         for i in ma.modalities.keys() for j in ma.modalities.keys()
                         if i != j and (i, j) in similarity_dict]
    avg_similarity = np.mean(valid_similarities) if valid_similarities else 0.00
    print(f"  整体跨模态平均相似度: {avg_similarity:.4f}")
    
    # 8. 生成分析可视化
    print("\n[步骤8] 生成分析可视化（使用ljp_page库）...")
    viz = Matplotlib()
    output_dir = Path('res/figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 图表1：多模态典型相关系数对比
    print("  生成图表1: 多模态典型相关系数对比")
    
    # 从循环结果中提取数据，自动适配所有模态对
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
    
    # 图表2：跨模态相关性热图
    print("  生成图表2: 跨模态相关性热图")
    print("  分析四个模态之间的关联...")
    
    # 获取模态相关性矩阵
    correlation_df = ma.get_modality_correlation()
    
    # 使用ljp_page库的热力图功能
    viz.heatmap(
        data=correlation_df.values,
        title='跨模态相关性热图',
        xlabel='模态',
        ylabel='模态',
        xticklabels=correlation_df.columns.tolist(),
        yticklabels=correlation_df.index.tolist(),
        cmap='RdYlBu_r',
        annot=True,
        fmt='.4f',
        save_path=output_dir / '02_跨模态相关性热图.png',
        show=False
    )
    viz.close()
    print("  ✓ 图表已保存: 02_跨模态相关性热图.png")
    
    # 图表3：聚类结果可视化
    print("  生成图表3: 多模态融合聚类结果")
    reduced_features = ma.reduce_dimension(n_components=2)
    
    # 为每个聚类分配不同的颜色
    unique_labels = np.unique(cluster_labels)
    colors_list = ['#2E86AB', '#A23B72', '#F18F01']
    colors = [colors_list[i % len(colors_list)] for i in cluster_labels]
    
    viz.scatter(
        x=reduced_features[:, 0],
        y=reduced_features[:, 1],
        title='多模态融合聚类结果',
        xlabel='第一主成分',
        ylabel='第二主成分',
        colors=colors,
        save_path=output_dir / '03_多模态融合聚类结果.png',
        show=False
    )
    viz.close()
    print("  ✓ 图表已保存: 03_多模态融合聚类结果.png")
    
    # 图表4：各模态特征重要性对比
    print("  生成图表4: 各模态特征重要性对比")
    
    # 获取各模态的特征重要性
    importance_dict = {}
    for modality_key in ['sensor', 'image', 'lab', 'behavior']:
        # 简单计算各模态特征的标准差作为重要性指标
        modality_data = data_dict[modality_key].values
        importance = np.std(modality_data, axis=0)
        importance_dict[modality_key] = importance.mean()
    
    # 绘制条形图
    modality_names_cn = {'sensor': '传感器', 'image': '图像', 'lab': '临床检验', 'behavior': '行为活动'}
    modality_names = [modality_names_cn[k] for k in importance_dict.keys()]
    importance_values = list(importance_dict.values())
    
    viz.bar(modality_names, importance_values,
            title='各模态特征重要性对比',
            xlabel='模态',
            ylabel='平均特征重要性',
            save_path=output_dir / '04_各模态特征重要性对比.png',
            show=False)
    viz.close()
    print("  ✓ 图表已保存: 04_各模态特征重要性对比.png")
    
    # 9. 生成分析摘要报告
    print("\n[步骤9] 生成分析摘要报告...")
    summary = {
        'canonical_correlations': correlations,
        'silhouette_score': silhouette,
        'adjusted_rand_index': ari,
        'cross_modal_similarity': avg_similarity
    }
    print("\n" + "="*70)
    print("分析结果摘要")
    print("="*70)
    for key, value in summary.items():
        if isinstance(value, list):
            print(f"  {key}: {[f'{v:.4f}' for v in value]}")
        else:
            print(f"  {key}: {value:.4f}" if isinstance(value, (int, float)) else f"  {key}: {value}")
    
    # 9. 详细结果分析
    print("\n" + "="*70)
    print("详细结果分析与医学解释")
    print("="*70)
    
    print("\n【多模态典型相关分析结果】")
    # 动态生成所有模态对的描述
    pair_descriptions = []
    for pair_name, result in cca_results.items():
        corr_value = result['correlations'][0]
        pair_descriptions.append(f"{pair_name}的第一典型相关系数为 {corr_value:.4f}")
    
    # 将描述用顿号连接，最后用句号
    description_text = "，\n  ".join(pair_descriptions) + "。"
    print(f"  {description_text}")
    
    # 计算所有模态对中的最大相关系数
    all_correlations = [result['correlations'][0] for result in cca_results.values()]
    max_corr = max(all_correlations)
    if max_corr > 0.7:
        print(f"\n  总体上，不同模态之间存在较强的跨模态关联。")
        print(f"  这说明生理信号、体表特征、临床指标和生活方式之间存在复杂的相互作用。")
        print(f"  例如：心率变异性（传感器）与血糖水平（临床）可能相关，")
        print(f"  运动量（行为）可能与心血管指标（临床）相关。")
        print(f"  医学价值：多模态融合可以提供更全面、准确的健康评估。")
    elif max_corr > 0.5:
        print(f"\n  总体上，不同模态之间存在中等程度的跨模态关联。")
        print(f"  说明部分健康指标的变化会体现在多个模态上，")
        print(f"  但需要结合多种模态才能准确判断健康状况。")
        print(f"  医学价值：多模态融合可以提高健康评估的鲁棒性和准确性。")
    else:
        print(f"\n  总体上，不同模态之间的跨模态关联相对较弱。")
        print(f"  说明四种模态捕捉的是健康状态的不同方面，")
        print(f"  具有很强的互补性，联合分析可以获得更全面的健康画像。")
        print(f"  医学价值：多模态互补可以挖掘单一模态无法发现的健康模式。")
    
    print(f"\n【聚类分析结果】")
    print(f"  轮廓系数为 {silhouette:.4f}，")
    if silhouette > 0.5:
        print(f"  表明多模态特征聚类效果良好，样本呈现出明显的健康分层结构。")
        print(f"  模型成功区分了不同的健康状态群体。")
    elif silhouette > 0.3:
        print(f"  表明聚类效果一般，健康状态存在一定的过渡性。")
        print(f"  符合医学实际：健康到疾病是一个渐进过程，")
        print(f"  亚健康状态与健康状态可能有部分重叠。")
    else:
        print(f"  表明聚类效果较弱，样本在特征空间分布相对混杂。")
        print(f"  这可能反映了个体差异较大，或健康状态的复杂性。")
    
    print(f"\n  调整兰德指数为 {ari:.4f}，")
    if ari > 0.7:
        print(f"  表明多模态聚类结果与真实健康状态高度一致，")
        print(f"  验证了四模态特征融合的有效性。")
        print(f"  模型成功捕捉到了跨模态的健康模式。")
    elif ari > 0.4:
        print(f"  表明聚类结果与真实健康状态部分一致，")
        print(f"  说明模型能够识别主要的健康状态模式，")
        print(f"  但在边界样本上存在混淆。")
    
    print(f"\n【跨模态关联强度分析】")
    print(f"  整体关联强度为 {avg_similarity:.4f}，")
    if avg_similarity > 0.3:
        print(f"  表明各模态之间存在较强的预测能力，")
        print(f"  可以通过一种模态的特征预测另一种模态的特征。")
        print(f"  例如：通过面部图像（图像）推断血压水平（传感器），")
        print(f"  通过运动习惯（行为）预测血糖变化（临床）。")
        print(f"  医学价值：支持了中医望诊的科学性，生理状态会反映在外观特征上。")
        print(f"  应用价值：可通过图像分析初步筛查健康异常。")
    else:
        print(f"  表明各模态相对独立，")
        print(f"  说明四种模态提供了互补的健康信息，")
        print(f"  融合分析可以获得更全面的健康评估。")
    
    print("\n" + "="*70)
    print("分析完成！所有图表已保存至 res/figures 目录")
    print("="*70)
    
    return ma, summary


if __name__ == "__main__":
    # 运行完整案例研究
    analyzer, summary = run_comprehensive_case_study()
    
    print("\n" + "="*70)
    print("使用说明")
    print("="*70)
    print("""
本模型提供了四模态关联分析的完整框架，主要功能包括：

1. 多模态典型相关分析(CCA)：研究不同模态组之间的线性关联
   - 用法：analyzer.canonical_correlation_analysis(modality1, modality2)
   - 返回：典型变量得分、典型载荷、典型相关系数
   - 应用：分析传感器-图像、临床-行为、传感器-临床等模态对

2. 特征融合：将四个模态的特征融合为统一表示
   - 用法：analyzer.fuse_modalities(fusion_method='concat')
   - 方法：concat(简单拼接), average(降维平均), weighted(加权融合)
   - 输出：融合后的统一特征表示

3. 聚类分析：在融合特征空间发现潜在健康模式
   - 用法：使用ljp_page库的KmeanCluster类
   - 评估：轮廓系数、惯性值、调整兰德指数
   - 应用：识别健康、亚健康、疾病风险群体

4. 跨模态相似度：量化不同模态间的相似程度
   - 用法：analyzer.compute_cross_modal_similarity(method='cosine')
   - 方法：cosine(余弦), euclidean(欧氏), pearson(皮尔逊)
   - 应用：评估模态间的预测能力

5. 多模态可视化分析：生成多种分析图表
   - 多模态典型相关系数对比：比较不同模态对的关联强度
   - 跨模态相关性热图：展示四个模态间的关联矩阵
   - 多模态融合聚类结果：PCA降维后的聚类可视化
   - 各模态特征重要性对比：评估各模态的贡献度

四模态说明：
- 模态1：传感器时序数据（心率变异性、血压、体温等10维）
- 模态2：图像视觉特征（皮肤颜色、纹理、气色等11维）
- 模态3：临床检验数据（血常规、血糖、血脂等8维）
- 模态4：行为活动数据（运动、睡眠等7维）

应用场景：
- 智能健康监测：综合评估个体健康状况
- 疾病风险预警：早期识别健康异常模式
- 个性化健康建议：基于多模态数据提供定制化建议
- 医学辅助诊断：辅助医生进行综合健康评估
""")
