# 生成时间: 02-10-23-35-00
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import functools
from pathlib import Path
from typing import Optional, Literal, Union


def plot_handler(needs_colors_func=None):
    """
    绘图装饰器，统一处理前置后置操作
    
    :param needs_colors_func: 计算颜色数量的函数，接收 (self, *args, **kwargs)
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            self._init_figure()
            self.ax.clear()
            
            kwargs['title'] = kwargs.get('title', '图表')
            save_path = kwargs.get('save_path')
            show = kwargs.get('show', True)
            colors = kwargs.get('colors')
            
            if colors is None and needs_colors_func is not None:
                num_colors = needs_colors_func(self, *args, **kwargs)
                colors = self.get_color(num_colors)
                kwargs['colors'] = colors
            
            result = method(self, *args, **kwargs)
            
            self._init_plt(self.ax, **kwargs)
            
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                self.fig.savefig(save_path, dpi=self.theme['dpi'], bbox_inches='tight')
            
            if show:
                plt.show()
            
            return self.fig, self.ax
        
        return wrapper
    return decorator


class Matplotlib:
    """
    自定义画图类，集成Seaborn样式，支持主题系统
    """
    
    # 预设主题配置
    THEMES = {
        'report': {
            'style': 'white',
            'palette': ['#4A90E2', '#50E3C2', '#F5A623', '#D0021B', '#9013FE'],
            'figsize': (10, 6),
            'title_fontsize': 14,
            'label_fontsize': 12,
            'tick_fontsize': 10,
            'legend_fontsize': 10,
            'title_fontweight': 'bold',
            'grid': False,
            'dpi': 300,
        },
        'presentation': {
            'style': 'whitegrid',
            'palette': 'husl',
            'figsize': (12, 7),
            'title_fontsize': 18,
            'label_fontsize': 14,
            'tick_fontsize': 12,
            'legend_fontsize': 12,
            'title_fontweight': 'bold',
            'grid': True,
            'dpi': 150,
        },
        'minimal': {
            'style': 'ticks',
            'palette': ['#333333', '#666666', '#999999', '#CCCCCC', '#EEEEEE'],
            'figsize': (8, 5),
            'title_fontsize': 12,
            'label_fontsize': 10,
            'tick_fontsize': 9,
            'legend_fontsize': 9,
            'title_fontweight': 'normal',
            'grid': False,
            'dpi': 200,
        },
        'dark': {
            'style': 'darkgrid',
            'palette': 'flare',
            'figsize': (10, 6),
            'title_fontsize': 14,
            'label_fontsize': 12,
            'tick_fontsize': 10,
            'legend_fontsize': 10,
            'title_fontweight': 'bold',
            'grid': True,
            'dpi': 300,
        }
    }
    
    def __init__(self, theme: Union[str, dict] = 'report', auto_close: bool = True):
        """
        初始化画图类
        
        :param theme: 主题名称（'report', 'presentation', 'minimal', 'dark'）或自定义主题字典
        :param auto_close: 是否自动关闭图表（推荐True，避免内存泄漏）
        """
        self.fig = None
        self.ax = None
        self.auto_close = auto_close
        self._original_rc_params = plt.rcParams.copy()
        
        if isinstance(theme, str):
            self.theme_name = theme
            self.theme = self.THEMES.get(theme, self.THEMES['report']).copy()
        else:
            self.theme_name = 'custom'
            self.theme = {**self.THEMES['report'], **theme}
        
        self._apply_theme()
    
    def _apply_theme(self):
        """应用当前主题"""
        sns.set_theme(style=self.theme['style'], palette=self.theme['palette'])
        self.set_chinese(plt)
    
    def set_theme(self, theme: Union[str, dict]):
        """
        切换主题
        
        :param theme: 主题名称或自定义主题字典
        """
        self.__init__(theme=theme, auto_close=self.auto_close)
        return self
    
    @staticmethod
    def set_chinese(plt):
        """设置中文字体"""
        plt.rcParams.update({
            'font.sans-serif': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],
            'axes.unicode_minus': False
        })
        return plt
    
    @staticmethod
    def get_color(num: int, palette: Optional[Union[str, list]] = None, print_colors: bool = False):
        """
        获取颜色列表
        
        :param num: 需要的颜色数量
        :param palette: 调色板名称或颜色列表，为None时使用当前主题
        :param print_colors: 是否打印颜色列表
        :return: 颜色列表
        """
        if num <= 0:
            return []
        
        if isinstance(palette, list):
            if len(palette) >= num:
                return palette[:num]
            colors = palette * (num // len(palette) + 1)
            return colors[:num]
        
        if palette is None:
            current_palette = sns.color_palette()
            colors = current_palette[:num]
        else:
            colors = sns.color_palette(palette, n_colors=num)
        
        if print_colors:
            print(f'生成的颜色列表（{num}个）:')
            color_list_str = '[' + ', '.join([f'({c[0]:.3f}, {c[1]:.3f}, {c[2]:.3f})' for c in colors]) + ']'
            print(color_list_str)
        
        return colors

    def _init_plt(self, ax, **kwargs):
        """
        绘图默认配置
        
        :param ax: 坐标轴对象
        :param kwargs: 配置参数
        """
        theme = self.theme
        
        config_map = {
            'title': lambda p: ax.set_title(p, fontsize=theme['title_fontsize'], 
                                          fontweight=theme['title_fontweight']),
            'xlabel': lambda p: ax.set_xlabel(p, fontsize=theme['label_fontsize']),
            'ylabel': lambda p: ax.set_ylabel(p, fontsize=theme['label_fontsize']),
            'xlim': lambda p: ax.set_xlim(p),
            'ylim': lambda p: ax.set_ylim(p),
            'xticks': lambda p: ax.set_xticks(p),
            'yticks': lambda p: ax.set_yticks(p),
            'xlabel_rotation': lambda p: ax.tick_params(axis='x', rotation=p),
            'ylabel_rotation': lambda p: ax.tick_params(axis='y', rotation=p),
        }
        
        for key, value in kwargs.items():
            if key in config_map:
                config_map[key](value)
        
        if kwargs.get('grid', theme['grid']):
            ax.grid(True, alpha=0.3)
        else:
            ax.grid(False)
        
        if kwargs.get('show_legend', False):
            ax.legend(fontsize=theme['legend_fontsize'])

    def _init_figure(self):
        """初始化图形和坐标轴"""
        self.fig = plt.figure(figsize=self.theme['figsize'])
        self.ax = self.fig.add_subplot(111)

    @plot_handler(needs_colors_func=lambda self, x, y, **kwargs: len(x))
    def bar(self, x, y, colors=None, title=None, xlabel=None, ylabel=None, 
            save_path=None, show=True, grid=None, show_legend=False, **kwargs):
        """
        生成柱状图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :param grid: 是否显示网格线
        :param show_legend: 是否显示图例
        :return: (fig, ax) 元组
        """
        bars = self.ax.bar(x, y, color=colors, edgecolor='white', linewidth=0.5)
        if self.auto_close:
            self.close()
        return bars

    def _get_line_colors(self, x, y, **kwargs):
        if isinstance(y[0], (list, np.ndarray, pd.Series)):
            return len(y)
        return 1
    
    @plot_handler(needs_colors_func=_get_line_colors)
    def line(self, x, y, colors=None, title=None, xlabel=None, ylabel=None,
             save_path=None, show=True, grid=None, show_legend=False, **kwargs):
        """
        生成折线图
        
        :param x: X轴数据
        :param y: Y轴数据，支持多条线
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :param grid: 是否显示网格线
        :param show_legend: 是否显示图例
        :return: (fig, ax) 元组
        """
        if isinstance(y[0], (list, np.ndarray, pd.Series)):
            for i, yi in enumerate(y):
                self.ax.plot(x, yi, color=colors[i % len(colors)], 
                           linewidth=2, marker='o', markersize=4, label=f'系列{i+1}')
        else:
            self.ax.plot(x, y, color=colors[0], linewidth=2, marker='o', markersize=4)
        
        if self.auto_close:
            self.close()

    @plot_handler(needs_colors_func=lambda self, data, **kwargs: len(data))
    def pie(self, data, labels=None, colors=None, title=None, 
            save_path=None, show=True, **kwargs):
        """
        生成饼图
        
        :param data: 数据列表
        :param labels: 标签列表
        :param title: 图表标题
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        kwargs['autopct'] = kwargs.get('autopct', '%1.1f%%')
        kwargs['startangle'] = kwargs.get('startangle', 90)
        kwargs['textprops'] = {'fontsize': self.theme['tick_fontsize']}
        wedges, texts, autotexts = self.ax.pie(data, labels=labels, colors=colors, **kwargs)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        if self.auto_close:
            self.close()
        return wedges, texts, autotexts

    @plot_handler(needs_colors_func=lambda self, x, y, **kwargs: 1)
    def scatter(self, x, y, colors=None, title=None, xlabel=None, ylabel=None,
                save_path=None, show=True, grid=None, **kwargs):
        """
        生成散点图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色
        :param save_path: 保存路径
        :param show: 是否显示图表
        :param grid: 是否显示网格线
        :return: (fig, ax) 元组
        """
        self.ax.scatter(x, y, color=colors[0], alpha=0.6, s=50, 
                       edgecolors='white', linewidth=0.5)
        if self.auto_close:
            self.close()

    @plot_handler(needs_colors_func=lambda self, data, **kwargs: len(data))
    def box(self, data, labels=None, colors=None, title=None, xlabel=None, ylabel=None,
            save_path=None, show=True, grid=None, **kwargs):
        """
        生成箱线图
        
        :param data: 数据列表，支持多组数据
        :param labels: 每个箱子的标签
        :param title: 图表标题
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        bp = self.ax.boxplot(data, labels=labels, patch_artist=True)
        
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
            plt.setp(bp[element], color='gray', linewidth=1.5)
        
        if self.auto_close:
            self.close()
        return bp

    @plot_handler(needs_colors_func=lambda self, data, **kwargs: 1)
    def histogram(self, data, bins=10, colors=None, title=None, xlabel=None, ylabel=None,
                  save_path=None, show=True, grid=None, **kwargs):
        """
        生成直方图
        
        :param data: 数据列表
        :param bins: 分箱数量
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        self.ax.hist(data, bins=bins, color=colors[0], edgecolor='white', alpha=0.7)
        if self.auto_close:
            self.close()

    @plot_handler(needs_colors_func=lambda self, x, y, **kwargs: 1)
    def area(self, x, y, colors=None, title=None, xlabel=None, ylabel=None,
             save_path=None, show=True, grid=None, **kwargs):
        """
        生成面积图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        self.ax.fill_between(x, y, color=colors[0], alpha=0.6)
        self.ax.plot(x, y, color=colors[0], linewidth=2)
        if self.auto_close:
            self.close()

    @plot_handler(needs_colors_func=lambda self, x, y, **kwargs: len(y))
    def stacked_bar(self, x, y, colors=None, title=None, xlabel=None, ylabel=None,
                    save_path=None, show=True, grid=None, **kwargs):
        """
        生成堆叠柱状图
        
        :param x: X轴数据
        :param y: Y轴数据，二维数组
        :param title: 图表标题
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        bottom = np.zeros(len(x))
        for i, yi in enumerate(y):
            self.ax.bar(x, yi, bottom=bottom, color=colors[i], 
                       label=f'系列{i+1}', edgecolor='white', linewidth=0.5)
            bottom += yi
        kwargs['show_legend'] = True
        if self.auto_close:
            self.close()

    @plot_handler(needs_colors_func=lambda self, y, x, **kwargs: len(y))
    def horizontal_bar(self, y, x, colors=None, title=None, xlabel=None, ylabel=None,
                       save_path=None, show=True, grid=None, **kwargs):
        """
        生成水平柱状图
        
        :param y: Y轴数据
        :param x: X轴数据
        :param title: 图表标题
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        self.ax.barh(y, x, color=colors, edgecolor='white', linewidth=0.5)
        if self.auto_close:
            self.close()

    def _get_radar_colors(self, data, categories, **kwargs):
        return len(data)
    
    @plot_handler(needs_colors_func=_get_radar_colors)
    def radar(self, data, categories, colors=None, title=None,
              save_path=None, show=True, **kwargs):
        """
        生成雷达图
        
        :param data: 数据列表，支持多组数据
        :param categories: 分类标签
        :param title: 图表标题
        :param colors: 颜色列表
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        for i, d in enumerate(data):
            values = d + d[:1]
            self.ax.plot(angles, values, 'o-', linewidth=2, color=colors[i])
            self.ax.fill(angles, values, alpha=0.25, color=colors[i])
        
        self.ax.set_xticks(angles[:-1])
        self.ax.set_xticklabels(categories, fontsize=self.theme['tick_fontsize'])
        self.ax.grid(True, alpha=0.3)
        
        if self.auto_close:
            self.close()

    @plot_handler(needs_colors_func=None)
    def heatmap(self, data, xticklabels=None, yticklabels=None, cmap='YlOrRd',
                annot=True, fmt='.2f', title=None, xlabel=None, ylabel=None,
                save_path=None, show=True, **kwargs):
        """
        生成热力图
        
        :param data: 二维数据矩阵
        :param xticklabels: X轴刻度标签
        :param yticklabels: Y轴刻度标签
        :param cmap: 颜色映射
        :param annot: 是否显示数值
        :param fmt: 数值格式
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图表
        :return: (fig, ax) 元组
        """
        sns.heatmap(data, annot=annot, fmt=fmt, cmap=cmap, 
                   xticklabels=xticklabels, yticklabels=yticklabels,
                   ax=self.ax, cbar_kws={'label': '数值'},
                   linewidths=0.5, linecolor='white',
                   annot_kws={'size': self.theme['tick_fontsize']})
        
        if self.auto_close:
            self.close()

    def close(self):
        """关闭图表并重置"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动关闭图表"""
        self.close()
        return False
    
    @staticmethod
    def reset_theme():
        """重置为matplotlib默认样式"""
        plt.rcdefaults()
    
    @staticmethod
    def list_themes():
        """列出所有可用主题"""
        print("可用主题:")
        for name, config in Matplotlib.THEMES.items():
            print(f"  - {name}: style={config['style']}, figsize={config['figsize']}")


# 默认设置
Matplotlib.set_chinese(plt)
