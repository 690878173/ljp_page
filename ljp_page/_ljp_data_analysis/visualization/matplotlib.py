# 生成时间: 02-10-23-40-00
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class ThemeConfig:
    """主题配置类"""
    style: str = 'white'
    palette: Union[str, List[str]] = 'deep'
    figsize: Tuple[float, float] = (10, 6)
    title_fontsize: int = 14
    label_fontsize: int = 12
    tick_fontsize: int = 10
    legend_fontsize: int = 10
    title_fontweight: str = 'bold'
    grid: bool = False
    dpi: int = 300
    edgecolor: str = 'white'
    edge_linewidth: float = 0.5
    alpha: float = 0.7


class ThemeRegistry:
    """主题注册表，预定义主题配置"""
    
    THEMES = {
        'report': ThemeConfig(
            style='white',
            palette=['#4A90E2', '#50E3C2', '#F5A623', '#D0021B', '#9013FE'],
            figsize=(10, 6),
            title_fontsize=14,
            label_fontsize=12,
            tick_fontsize=10,
            legend_fontsize=10,
            title_fontweight='bold',
            grid=False,
            dpi=300
        ),
        'presentation': ThemeConfig(
            style='whitegrid',
            palette='husl',
            figsize=(12, 7),
            title_fontsize=18,
            label_fontsize=14,
            tick_fontsize=12,
            legend_fontsize=12,
            title_fontweight='bold',
            grid=True,
            dpi=150
        ),
        'minimal': ThemeConfig(
            style='ticks',
            palette=['#333333', '#666666', '#999999', '#CCCCCC', '#EEEEEE'],
            figsize=(8, 5),
            title_fontsize=12,
            label_fontsize=10,
            tick_fontsize=9,
            legend_fontsize=9,
            title_fontweight='normal',
            grid=False,
            dpi=200
        ),
        'dark': ThemeConfig(
            style='darkgrid',
            palette='flare',
            figsize=(10, 6),
            title_fontsize=14,
            label_fontsize=12,
            tick_fontsize=10,
            legend_fontsize=10,
            title_fontweight='bold',
            grid=True,
            dpi=300
        )
    }
    
    @classmethod
    def get_theme(cls, name: str) -> ThemeConfig:
        """获取主题配置"""
        return cls.THEMES.get(name, cls.THEMES['report'])
    
    @classmethod
    def register_theme(cls, name: str, config: ThemeConfig):
        """注册新主题"""
        cls.THEMES[name] = config
    
    @classmethod
    def list_themes(cls) -> List[str]:
        """列出所有可用主题"""
        return list(cls.THEMES.keys())


class StyleManager:
    """样式管理器，负责全局样式设置"""
    
    @staticmethod
    def setup_chinese():
        """设置中文字体"""
        plt.rcParams.update({
            'font.sans-serif': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],
            'axes.unicode_minus': False
        })
    
    @staticmethod
    def apply_theme(theme: ThemeConfig):
        """应用主题到全局样式"""
        sns.set_theme(style=theme.style, palette=theme.palette)
        StyleManager.setup_chinese()
    
    @staticmethod
    def reset():
        """重置为默认样式"""
        sns.reset_defaults()
        plt.rcdefaults()
        StyleManager.setup_chinese()
    
    @staticmethod
    def get_colors(n: int, palette: Optional[Union[str, List[str]]] = None) -> List[str]:
        """
        获取颜色列表
        
        :param n: 颜色数量
        :param palette: 调色板名称或颜色列表
        :return: 颜色列表（RGB元组）
        """
        if n <= 0:
            return []
        
        if isinstance(palette, list):
            if len(palette) >= n:
                return palette[:n]
            return (palette * ((n // len(palette)) + 1))[:n]
        
        if palette is None:
            colors = sns.color_palette()[:n]
        else:
            colors = sns.color_palette(palette, n_colors=n)
        
        return [tuple(c) for c in colors]


class FigureManager:
    """图形管理器，负责图形的生命周期"""
    
    def __init__(self, theme: ThemeConfig):
        self.theme = theme
        self.fig = None
        self.ax = None
        self.axes = None
        self._is_active = False
        self._subplot_grid = (1, 1)
        self._current_position = 0
    
    def create_figure(self, nrows: int = 1, ncols: int = 1, figsize: Optional[Tuple[float, float]] = None):
        """
        创建新图形
        
        :param nrows: 子图行数
        :param ncols: 子图列数
        :param figsize: 图形大小，为None时使用主题默认大小
        """
        if self.fig is not None:
            self.close()
        
        if figsize is None:
            figsize = self.theme.figsize
        
        if nrows == 1 and ncols == 1:
            self.fig = plt.figure(figsize=figsize)
            self.ax = self.fig.add_subplot(111)
            self.axes = None
        else:
            self.fig, self.axes = plt.subplots(nrows, ncols, figsize=figsize)
            self.ax = None
            self._subplot_grid = (nrows, ncols)
            
            if nrows == 1 or ncols == 1:
                self.axes = self.axes.flatten() if hasattr(self.axes, 'flatten') else [self.axes]
        
        self._is_active = True
        self._current_position = 0
        return self.fig, self.ax or self.axes
    
    def get_ax(self, position: Optional[int] = None):
        """
        获取指定位置的子图坐标轴
        
        :param position: 子图位置索引（从0开始），为None时获取当前坐标轴
        :return: 子图坐标轴对象
        """
        if self.fig is None:
            raise RuntimeError("图形未创建，请先调用 create_figure()")
        
        if self.axes is None:
            return self.ax
        
        if position is None:
            position = self._current_position
        
        if isinstance(self.axes, np.ndarray):
            if self.axes.ndim == 1:
                return self.axes[position]
            else:
                row = position // self._subplot_grid[1]
                col = position % self._subplot_grid[1]
                return self.axes[row, col]
        
        return self.axes
    
    def set_position(self, position: int):
        """
        设置当前子图位置
        
        :param position: 子图位置索引（从0开始）
        """
        self._current_position = position
    
    def next_position(self):
        """移动到下一个子图位置"""
        self._current_position += 1
    
    def close(self):
        """关闭图形"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
            self.axes = None
            self._is_active = False
            self._current_position = 0
    
    def save(self, path: str, dpi: Optional[int] = None):
        """保存图形"""
        if self.fig is None:
            raise RuntimeError("没有可保存的图形，请先创建图形")
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        dpi = dpi or self.theme.dpi
        self.fig.savefig(path, dpi=dpi, bbox_inches='tight')
    
    def show(self):
        """显示图形"""
        if self.fig is not None:
            plt.tight_layout()
            plt.show()
    
    def __enter__(self):
        self.create_figure()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class Plotter:
    """绘图器类，负责各种图表的绘制"""
    
    def __init__(self, theme: Union[str, ThemeConfig] = 'report'):
        """
        初始化绘图器
        
        :param theme: 主题名称或ThemeConfig对象
        """
        if isinstance(theme, str):
            self.theme = ThemeRegistry.get_theme(theme)
        else:
            self.theme = theme
        
        self.style_manager = StyleManager()
        self.figure_manager = FigureManager(self.theme)
        self.style_manager.apply_theme(self.theme)
    
    def set_theme(self, theme: Union[str, ThemeConfig]):
        """
        切换主题
        
        :param theme: 主题名称或ThemeConfig对象
        :return: self，支持链式调用
        """
        if isinstance(theme, str):
            self.theme = ThemeRegistry.get_theme(theme)
        else:
            self.theme = theme
        
        self.style_manager.apply_theme(self.theme)
        self.figure_manager.theme = self.theme
        return self
    
    def _setup_axes(self, title: Optional[str] = None, xlabel: Optional[str] = None,
                    ylabel: Optional[str] = None, grid: Optional[bool] = None,
                    show_legend: bool = False, ax: Optional[Any] = None, **kwargs):
        """
        设置坐标轴样式
        
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param grid: 是否显示网格线
        :param show_legend: 是否显示图例
        :param ax: 坐标轴对象，为None时使用默认坐标轴
        :param kwargs: 其他参数
        """
        if ax is None:
            ax = self.figure_manager.ax
        
        theme = self.theme
        
        if title:
            ax.set_title(title, fontsize=theme.title_fontsize, fontweight=theme.title_fontweight)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=theme.label_fontsize)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=theme.label_fontsize)
        
        grid_on = grid if grid is not None else theme.grid
        if grid_on:
            ax.grid(True, alpha=0.3)
        else:
            ax.grid(False)
        
        if show_legend:
            ax.legend(fontsize=theme.legend_fontsize)
    
    def _get_colors(self, n: int, colors: Optional[List[str]] = None) -> List[str]:
        """获取颜色列表"""
        if colors is not None:
            return colors
        return self.style_manager.get_colors(n, self.theme.palette)
    
    def _ensure_figure(self, position: Optional[int] = None):
        """
        确保图形已创建
        
        :param position: 子图位置索引（仅用于多子图模式）
        """
        if self.figure_manager.fig is None:
            self.figure_manager.create_figure()
    
    def create_subplots(self, nrows: int = 1, ncols: int = 1, 
                        figsize: Optional[Tuple[float, float]] = None):
        """
        创建子图网格
        
        :param nrows: 子图行数
        :param ncols: 子图列数
        :param figsize: 图形大小，为None时自动计算
        :return: self，支持链式调用
        """
        if figsize is None:
            base_width, base_height = self.theme.figsize
            figsize = (base_width * ncols, base_height * nrows)
        
        self.figure_manager.create_figure(nrows, ncols, figsize)
        return self
    
    def set_subplot(self, position: int):
        """
        设置当前子图位置
        
        :param position: 子图位置索引（从0开始）
        :return: self，支持链式调用
        """
        self.figure_manager.set_position(position)
        return self
    
    def next_subplot(self):
        """
        移动到下一个子图位置
        
        :return: self，支持链式调用
        """
        self.figure_manager.next_position()
        return self
    
    def _get_current_ax(self):
        """获取当前坐标轴对象"""
        return self.figure_manager.get_ax()
    
    def bar(self, x: List[Any], y: List[float], colors: Optional[List[str]] = None,
            title: Optional[str] = None, xlabel: Optional[str] = None,
            ylabel: Optional[str] = None, save_path: Optional[str] = None,
            show: bool = True, grid: Optional[bool] = None,
            show_legend: bool = False, **kwargs) -> Tuple[Any, Any]:
        """
        绘制柱状图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param colors: 颜色列表
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param show_legend: 是否显示图例
        :param kwargs: 传递给matplotlib bar方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        colors = self._get_colors(len(x), colors)
        bars = ax.bar(x, y, color=colors, edgecolor=self.theme.edgecolor, 
                     linewidth=self.theme.edge_linewidth, **kwargs)
        
        self._setup_axes(title, xlabel, ylabel, grid, show_legend, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def line(self, x: List[Any], y: Union[List[float], List[List[float]]],
             colors: Optional[List[str]] = None, title: Optional[str] = None,
             xlabel: Optional[str] = None, ylabel: Optional[str] = None,
             save_path: Optional[str] = None, show: bool = True,
             grid: Optional[bool] = None, show_legend: bool = False,
             **kwargs) -> Tuple[Any, Any]:
        """
        绘制折线图
        
        :param x: X轴数据
        :param y: Y轴数据，支持多条线
        :param colors: 颜色列表
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param show_legend: 是否显示图例
        :param kwargs: 传递给matplotlib plot方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        if isinstance(y[0], (list, np.ndarray, pd.Series)):
            n_lines = len(y)
            colors = self._get_colors(n_lines, colors)
            for i, yi in enumerate(y):
                ax.plot(x, yi, color=colors[i], linewidth=2, marker='o', 
                       markersize=4, label=f'系列{i+1}', **kwargs)
        else:
            colors = self._get_colors(1, colors)
            ax.plot(x, y, color=colors[0], linewidth=2, marker='o', markersize=4, **kwargs)
        
        self._setup_axes(title, xlabel, ylabel, grid, show_legend or isinstance(y[0], (list, np.ndarray, pd.Series)), ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def scatter(self, x: List[float], y: List[float], color: Optional[str] = None,
                title: Optional[str] = None, xlabel: Optional[str] = None,
                ylabel: Optional[str] = None, save_path: Optional[str] = None,
                show: bool = True, grid: Optional[bool] = None,
                **kwargs) -> Tuple[Any, Any]:
        """
        绘制散点图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param color: 颜色
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib scatter方法的其他参数（包括c, cmap等）
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        alpha = kwargs.pop('alpha', self.theme.alpha)
        s = kwargs.pop('s', 50)
        
        # 只有在没有传入c或color参数时，才使用自动生成的颜色
        if 'c' not in kwargs and 'color' not in kwargs:
            if color is None:
                color = self._get_colors(1)[0]
            kwargs['c'] = color
        
        # 设置scatter参数
        scatter_kwargs = {'alpha': alpha, 's': s}
        
        # 处理edgecolor：当使用颜色数组时，避免edgecolor覆盖颜色映射
        if 'c' in kwargs and hasattr(kwargs['c'], '__iter__') and not isinstance(kwargs['c'], str):
            # 颜色数组的情况，不设置edgecolor
            if 'edgecolor' not in kwargs and 'edgecolors' not in kwargs:
                scatter_kwargs['edgecolor'] = 'none'
        else:
            # 单一颜色的情况，使用默认edgecolor
            if 'edgecolor' not in kwargs and 'edgecolors' not in kwargs:
                scatter_kwargs['edgecolor'] = self.theme.edgecolor
            if 'linewidth' not in kwargs and 'linewidths' not in kwargs:
                scatter_kwargs['linewidth'] = self.theme.edge_linewidth
        
        scatter_kwargs.update(kwargs)
        
        # 调试信息
        print(f"  [SCATTER DEBUG] scatter_kwargs: {scatter_kwargs}")
        if 'c' in scatter_kwargs:
            c_param = scatter_kwargs['c']
            print(f"  [SCATTER DEBUG] c参数类型: {type(c_param)}")
            print(f"  [SCATTER DEBUG] c参数长度: {len(c_param) if hasattr(c_param, '__len__') else 'N/A'}")
            print(f"  [SCATTER DEBUG] c参数前5个值: {list(c_param)[:5] if hasattr(c_param, '__iter__') and not isinstance(c_param, str) else c_param}")
        
        ax.scatter(x, y, **scatter_kwargs)
        
        # 检查scatter对象
        if len(ax.collections) > 0:
            scatter_obj = ax.collections[-1]
            print(f"  [SCATTER DEBUG] scatter对象创建成功")
            print(f"  [SCATTER DEBUG] scatter.get_facecolors().shape: {scatter_obj.get_facecolors().shape}")
            print(f"  [SCATTER DEBUG] scatter.get_offsets().shape: {scatter_obj.get_offsets().shape}")
        else:
            print(f"  [SCATTER DEBUG] 警告：ax.collections为空！")
        
        self._setup_axes(title, xlabel, ylabel, grid, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def pie(self, data: List[float], labels: Optional[List[str]] = None,
            colors: Optional[List[str]] = None, title: Optional[str] = None,
            save_path: Optional[str] = None, show: bool = True,
            autopct: str = '%1.1f%%', **kwargs) -> Tuple[Any, Any]:
        """
        绘制饼图
        
        :param data: 数据列表
        :param labels: 标签列表
        :param colors: 颜色列表
        :param title: 图表标题
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param autopct: 百分比格式
        :param kwargs: 传递给matplotlib pie方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        colors = self._get_colors(len(data), colors)
        wedges, texts, autotexts = ax.pie(
            data, labels=labels, colors=colors, autopct=autopct,
            startangle=90, textprops={'fontsize': self.theme.tick_fontsize},
            **kwargs
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        if title:
            ax.set_title(title, fontsize=self.theme.title_fontsize, 
                        fontweight=self.theme.title_fontweight)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def box(self, data: Union[List[List[float]], List[float]], 
            labels: Optional[List[str]] = None, colors: Optional[List[str]] = None,
            title: Optional[str] = None, xlabel: Optional[str] = None,
            ylabel: Optional[str] = None, save_path: Optional[str] = None,
            show: bool = True, grid: Optional[bool] = None,
            **kwargs) -> Tuple[Any, Any]:
        """
        绘制箱线图
        
        :param data: 数据列表
        :param labels: 标签列表
        :param colors: 颜色列表
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib boxplot方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        if not isinstance(data[0], (list, np.ndarray)):
            data = [data]
        
        colors = self._get_colors(len(data), colors)
        bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, **kwargs)
        
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(self.theme.alpha)
        
        for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
            plt.setp(bp[element], color='gray', linewidth=1.5)
        
        self._setup_axes(title, xlabel, ylabel, grid, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def histogram(self, data: List[float], bins: int = 10,
                  color: Optional[str] = None, title: Optional[str] = None,
                  xlabel: Optional[str] = None, ylabel: Optional[str] = None,
                  save_path: Optional[str] = None, show: bool = True,
                  grid: Optional[bool] = None, **kwargs) -> Tuple[Any, Any]:
        """
        绘制直方图
        
        :param data: 数据列表
        :param bins: 分箱数量
        :param color: 颜色
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib hist方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        if color is None:
            colors = self._get_colors(1)
            color = colors[0]
        
        ax.hist(data, bins=bins, color=color, edgecolor=self.theme.edgecolor,
               alpha=self.theme.alpha, **kwargs)
        
        self._setup_axes(title, xlabel, ylabel, grid, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def heatmap(self, data: np.ndarray, xticklabels: Optional[List[str]] = None,
                yticklabels: Optional[List[str]] = None, cmap: str = 'YlOrRd',
                annot: bool = True, fmt: str = '.2f', title: Optional[str] = None,
                xlabel: Optional[str] = None, ylabel: Optional[str] = None,
                save_path: Optional[str] = None, show: bool = True,
                **kwargs) -> Tuple[Any, Any]:
        """
        绘制热力图
        
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
        :param show: 是否显示图形
        :param kwargs: 传递给seaborn heatmap方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        sns.heatmap(data, annot=annot, fmt=fmt, cmap=cmap,
                   xticklabels=xticklabels, yticklabels=yticklabels,
                   ax=ax, cbar_kws={'label': '数值'},
                   linewidths=0.5, linecolor=self.theme.edgecolor,
                   annot_kws={'size': self.theme.tick_fontsize},
                   **kwargs)
        
        self._setup_axes(title, xlabel, ylabel, None, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def stacked_bar(self, x: List[Any], y: List[List[float]],
                    colors: Optional[List[str]] = None, title: Optional[str] = None,
                    xlabel: Optional[str] = None, ylabel: Optional[str] = None,
                    save_path: Optional[str] = None, show: bool = True,
                    grid: Optional[bool] = None, **kwargs) -> Tuple[Any, Any]:
        """
        绘制堆叠柱状图
        
        :param x: X轴数据
        :param y: Y轴数据（二维数组）
        :param colors: 颜色列表
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib bar方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        colors = self._get_colors(len(y), colors)
        bottom = np.zeros(len(x))
        
        for i, yi in enumerate(y):
            ax.bar(x, yi, bottom=bottom, color=colors[i], label=f'系列{i+1}',
                  edgecolor=self.theme.edgecolor, linewidth=self.theme.edge_linewidth, **kwargs)
            bottom += yi
        
        self._setup_axes(title, xlabel, ylabel, grid, True, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def area(self, x: List[Any], y: List[float], color: Optional[str] = None,
             title: Optional[str] = None, xlabel: Optional[str] = None,
             ylabel: Optional[str] = None, save_path: Optional[str] = None,
             show: bool = True, grid: Optional[bool] = None,
             **kwargs) -> Tuple[Any, Any]:
        """
        绘制面积图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param color: 颜色
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib fill_between方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        if color is None:
            colors = self._get_colors(1)
            color = colors[0]
        
        ax.fill_between(x, y, color=color, alpha=self.theme.alpha, **kwargs)
        ax.plot(x, y, color=color, linewidth=2)
        
        self._setup_axes(title, xlabel, ylabel, grid, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def horizontal_bar(self, y: List[Any], x: List[float],
                       colors: Optional[List[str]] = None, title: Optional[str] = None,
                       xlabel: Optional[str] = None, ylabel: Optional[str] = None,
                       save_path: Optional[str] = None, show: bool = True,
                       grid: Optional[bool] = None, **kwargs) -> Tuple[Any, Any]:
        """
        绘制水平柱状图
        
        :param y: Y轴数据
        :param x: X轴数据
        :param colors: 颜色列表
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib barh方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        colors = self._get_colors(len(y), colors)
        ax.barh(y, x, color=colors, edgecolor=self.theme.edgecolor,
               linewidth=self.theme.edge_linewidth, **kwargs)
        
        self._setup_axes(title, xlabel, ylabel, grid, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def radar(self, data: Union[List[List[float]], List[float]], categories: List[str],
              colors: Optional[List[str]] = None, title: Optional[str] = None,
              save_path: Optional[str] = None, show: bool = True,
              **kwargs) -> Tuple[Any, Any]:
        """
        绘制雷达图
        
        :param data: 数据列表，支持多组数据
        :param categories: 分类标签
        :param colors: 颜色列表
        :param title: 图表标题
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param kwargs: 传递给matplotlib plot和fill方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        if not isinstance(data[0], (list, np.ndarray)):
            data = [data]
        
        colors = self._get_colors(len(data), colors)
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        for i, d in enumerate(data):
            values = list(d) + [d[0]]
            ax.plot(angles, values, 'o-', linewidth=2, color=colors[i], **kwargs)
            ax.fill(angles, values, alpha=0.25, color=colors[i], **kwargs)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=self.theme.tick_fontsize)
        ax.grid(True, alpha=0.3)
        
        if title:
            ax.set_title(title, fontsize=self.theme.title_fontsize,
                        fontweight=self.theme.title_fontweight)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def violin(self, data: List[List[float]], labels: Optional[List[str]] = None,
               colors: Optional[List[str]] = None, title: Optional[str] = None,
               xlabel: Optional[str] = None, ylabel: Optional[str] = None,
               save_path: Optional[str] = None, show: bool = True,
               grid: Optional[bool] = None, **kwargs) -> Tuple[Any, Any]:
        """
        绘制小提琴图
        
        :param data: 数据列表
        :param labels: 标签列表
        :param colors: 颜色列表
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param kwargs: 传递给matplotlib violinplot方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        colors = self._get_colors(len(data), colors)
        parts = ax.violinplot(data, positions=range(len(data)), 
                              showmeans=True, showmedians=True, **kwargs)
        
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(colors[i])
            pc.set_alpha(self.theme.alpha)
        
        for element in ['cbars', 'cmins', 'cmaxes', 'cmeans', 'cmedians']:
            if element in parts:
                plt.setp(parts[element], color='gray', linewidth=1.5)
        
        if labels:
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, fontsize=self.theme.tick_fontsize)
        
        self._setup_axes(title, xlabel, ylabel, grid, False, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def scatter_with_regression(self, x: List[float], y: List[float],
                                 color: Optional[str] = None,
                                 title: Optional[str] = None,
                                 xlabel: Optional[str] = None,
                                 ylabel: Optional[str] = None,
                                 save_path: Optional[str] = None,
                                 show: bool = True, grid: Optional[bool] = None,
                                 show_regression: bool = True,
                                 **kwargs) -> Tuple[Any, Any]:
        """
        绘制带回归线的散点图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param color: 颜色
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param grid: 是否显示网格线
        :param show_regression: 是否显示回归线
        :param kwargs: 传递给matplotlib方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        alpha = kwargs.pop('alpha', self.theme.alpha)
        s = kwargs.pop('s', 50)
        
        if color is None:
            colors = self._get_colors(1)
            color = colors[0]
        
        ax.scatter(x, y, color=color, alpha=alpha, s=s,
                  edgecolor=self.theme.edgecolor, 
                  linewidth=self.theme.edge_linewidth, **kwargs)
        
        if show_regression:
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(x), max(x), 100)
            ax.plot(x_line, p(x_line), color=color, linewidth=2, 
                   linestyle='--', alpha=0.8, label='回归线')
        
        self._setup_axes(title, xlabel, ylabel, grid, show_regression, ax)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def parallel_coordinates(self, data: pd.DataFrame, class_column: str,
                            colors: Optional[List[str]] = None,
                            title: Optional[str] = None,
                            save_path: Optional[str] = None,
                            show: bool = True, **kwargs) -> Tuple[Any, Any]:
        """
        绘制平行坐标图
        
        :param data: 数据框
        :param class_column: 分类列名
        :param colors: 颜色列表
        :param title: 图表标题
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param kwargs: 传递给plotly方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        from pandas.plotting import parallel_coordinates
        
        if colors is None:
            classes = data[class_column].unique()
            colors = self._get_colors(len(classes), colors)
        
        parallel_coordinates(data, class_column, ax=ax, color=colors, **kwargs)
        
        if title:
            ax.set_title(title, fontsize=self.theme.title_fontsize,
                        fontweight=self.theme.title_fontweight)
        
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=self.theme.legend_fontsize)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def corr_heatmap(self, data: Union[pd.DataFrame, np.ndarray],
                     cmap: str = 'coolwarm', annot: bool = True,
                     title: Optional[str] = None,
                     save_path: Optional[str] = None,
                     show: bool = True, **kwargs) -> Tuple[Any, Any]:
        """
        绘制相关性热力图
        
        :param data: 数据框或数组
        :param cmap: 颜色映射
        :param annot: 是否显示数值
        :param title: 图表标题
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param kwargs: 传递给seaborn heatmap方法的其他参数
        :return: (fig, ax) 元组
        """
        self._ensure_figure()
        ax = self._get_current_ax()
        
        if isinstance(data, pd.DataFrame):
            corr_matrix = data.corr()
            xticklabels = data.columns
            yticklabels = data.columns
        else:
            corr_matrix = np.corrcoef(data)
            xticklabels = None
            yticklabels = None
        
        sns.heatmap(corr_matrix, annot=annot, cmap=cmap, ax=ax,
                   xticklabels=xticklabels, yticklabels=yticklabels,
                   cbar_kws={'label': '相关系数'}, **kwargs)
        
        if title:
            ax.set_title(title, fontsize=self.theme.title_fontsize,
                        fontweight=self.theme.title_fontweight)
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return self.figure_manager.fig, ax
    
    def joint_plot(self, x: List[float], y: List[float],
                   kind: str = 'scatter', color: Optional[str] = None,
                   title: Optional[str] = None,
                   xlabel: Optional[str] = None,
                   ylabel: Optional[str] = None,
                   save_path: Optional[str] = None,
                   show: bool = True, **kwargs) -> Tuple[Any, Any]:
        """
        绘制联合分布图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param kind: 图表类型 ('scatter', 'hex', 'kde', 'reg')
        :param color: 颜色
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param save_path: 保存路径
        :param show: 是否显示图形
        :param kwargs: 传递给seaborn jointplot方法的其他参数
        :return: (fig, ax) 元组
        """
        if self.figure_manager.fig is not None:
            self.figure_manager.close()
        
        if color is None:
            colors = self._get_colors(1)
            color = colors[0]
        
        g = sns.jointplot(x=x, y=y, kind=kind, color=color, **kwargs)
        
        if xlabel:
            g.ax_joint.set_xlabel(xlabel, fontsize=self.theme.label_fontsize)
        if ylabel:
            g.ax_joint.set_ylabel(ylabel, fontsize=self.theme.label_fontsize)
        if title:
            g.fig.suptitle(title, fontsize=self.theme.title_fontsize,
                          fontweight=self.theme.title_fontweight, y=1.02)
        
        self.figure_manager.fig = g.fig
        self.figure_manager.ax = g.ax_joint
        self.figure_manager._is_active = True
        
        if save_path:
            self.figure_manager.save(save_path)
        if show:
            self.figure_manager.show()
        
        return g.fig, g.ax_joint
    
    def close(self):
        """关闭当前图形"""
        self.figure_manager.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.figure_manager.create_figure()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.figure_manager.close()
        return False


class QuickPlot:
    """快捷绘图类，提供简化的静态接口"""
    
    @staticmethod
    def bar(x, y, theme='report', **kwargs):
        """
        快速绘制柱状图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param theme: 主题名称或ThemeConfig对象
        :param kwargs: 传递给Plotter.bar方法的其他参数
        :return: (fig, ax) 元组
        """
        plotter = Plotter(theme)
        return plotter.bar(x, y, **kwargs)
    
    @staticmethod
    def line(x, y, theme='report', **kwargs):
        """
        快速绘制折线图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param theme: 主题名称或ThemeConfig对象
        :param kwargs: 传递给Plotter.line方法的其他参数
        :return: (fig, ax) 元组
        """
        plotter = Plotter(theme)
        return plotter.line(x, y, **kwargs)
    
    @staticmethod
    def scatter(x, y, theme='report', **kwargs):
        """
        快速绘制散点图
        
        :param x: X轴数据
        :param y: Y轴数据
        :param theme: 主题名称或ThemeConfig对象
        :param kwargs: 传递给Plotter.scatter方法的其他参数
        :return: (fig, ax) 元组
        """
        plotter = Plotter(theme)
        return plotter.scatter(x, y, **kwargs)
    
    @staticmethod
    def heatmap(data, theme='report', **kwargs):
        """
        快速绘制热力图
        
        :param data: 二维数据矩阵
        :param theme: 主题名称或ThemeConfig对象
        :param kwargs: 传递给Plotter.heatmap方法的其他参数
        :return: (fig, ax) 元组
        """
        plotter = Plotter(theme)
        return plotter.heatmap(data, **kwargs)
    
    @staticmethod
    def box(data, theme='report', **kwargs):
        """
        快速绘制箱线图
        
        :param data: 数据列表
        :param theme: 主题名称或ThemeConfig对象
        :param kwargs: 传递给Plotter.box方法的其他参数
        :return: (fig, ax) 元组
        """
        plotter = Plotter(theme)
        return plotter.box(data, **kwargs)


# 保留向后兼容的别名
Matplotlib = Plotter

# 初始化全局样式
StyleManager.setup_chinese()
