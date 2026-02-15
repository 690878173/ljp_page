from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie, Scatter, Boxplot, Graph, Radar, HeatMap as PyechartsHeatMap
import numpy as np
import pandas as pd
import random

class Pyecharts:
    def __init__(self):
        pass

    @staticmethod
    def set_theme(theme='light'):
        '''
        设置图表主题
        :param theme: 主题类型，如 'light', 'dark', 'vintage' 等
        '''
        return theme

    @staticmethod
    def get_color(num, print_colors=True):
        '''
        获取颜色列表（完全随机）
        :param num: 颜色数量
        :param print_colors: 是否打印颜色列表
        :return: 颜色列表
        '''
        colors = []
        for _ in range(num):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            color = f'rgb({r}, {g}, {b})'
            colors.append(color)
        
        if print_colors:
            print(f'生成的颜色列表: {colors}')
        
        return colors

    def _init_global_opts(self, chart, title=None, xlabel=None, ylabel=None, **kwargs):
        '''
        初始化全局配置选项
        :param chart: 图表对象
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param kwargs: 其他全局配置选项
        '''
        global_opts = {}
        
        if title is not None:
            global_opts['title_opts'] = opts.TitleOpts(title=title)
        if xlabel is not None:
            global_opts['xaxis_opts'] = opts.AxisOpts(name=xlabel)
        if ylabel is not None:
            global_opts['yaxis_opts'] = opts.AxisOpts(name=ylabel)
        
        global_opts['toolbox_opts'] = kwargs.get('toolbox_opts', opts.ToolboxOpts(is_show=True))
        
        for key, value in kwargs.items():
            if key not in ['toolbox_opts'] and not key.endswith('_opts'):
                global_opts[key] = value
        
        chart.set_global_opts(**global_opts)
        
        return chart

    def _init_data_opts(self, chart, **kwargs):
        '''
        初始化数据配置选项
        :param chart: 图表对象
        :param kwargs: 数据配置选项
        '''
        for key, value in kwargs.items():
            if hasattr(chart, key):
                setattr(chart, key, value)
        
        return chart

    def bar(self, x, y, title='柱状图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, horizontal=False, **kwargs):
        '''
        生成柱状图
        :param x: X轴数据
        :param y: Y轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param horizontal: 是否为水平柱状图
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(x))
        
        c = Bar(init_opts=opts.InitOpts(theme='light'))
        
        if horizontal:
            c.add_xaxis(list(y))
            c.add_yaxis(xlabel, list(x), color=colors[0])
        else:
            c.add_xaxis(list(x))
            c.add_yaxis(ylabel, list(y), color=colors[0])
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def line(self, x, y, title='折线图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, smooth=False, **kwargs):
        '''
        生成折线图
        :param x: X轴数据
        :param y: Y轴数据，支持多条线
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param smooth: 是否平滑曲线
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        c = Line(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis(list(x))
        
        if colors is None:
            if isinstance(y[0], (list, np.ndarray, pd.Series)):
                colors = self.get_color(len(y))
            else:
                colors = self.get_color(1)
        
        if isinstance(y[0], (list, np.ndarray, pd.Series)):
            for i, yi in enumerate(y):
                c.add_yaxis(f'系列{i+1}', list(yi), color=colors[i % len(colors)], is_smooth=smooth)
        else:
            c.add_yaxis(ylabel, list(y), color=colors[0], is_smooth=smooth)
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def pie(self, data, labels=None, title='饼图', colors=None, save_path=None, radius='60%', is_pie=True, **kwargs):
        '''
        生成饼图
        :param data: 数据列表
        :param labels: 标签列表
        :param title: 图表标题
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param radius: 饼图半径
        :param is_pie: 是否为饼图，False则为环形图
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(data))
        
        c = Pie(init_opts=opts.InitOpts(theme='light'))
        
        data_pairs = []
        for i, (label, value) in enumerate(zip(labels, data)):
            data_pairs.append((label, value))
        
        c.add(
            series_name='',
            data_pair=data_pairs,
            radius=radius if is_pie else ['40%', '70%'],
            label_opts=opts.LabelOpts(formatter="{b}: {d}%")
        )
        
        legend_opts = kwargs.pop('legend_opts', opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"))
        c = self._init_global_opts(c, title=title, legend_opts=legend_opts, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def scatter(self, x, y, title='散点图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, size=10, **kwargs):
        '''
        生成散点图
        :param x: X轴数据
        :param y: Y轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param size: 散点大小
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(1)
        
        data = [[float(xi), float(yi)] for xi, yi in zip(x, y)]
        
        c = Scatter(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis([str(xi) for xi in x])
        c.add_yaxis('', data, symbol_size=size, color=colors[0])
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def box(self, data, labels=None, title='箱线图', colors=None, save_path=None, **kwargs):
        '''
        生成箱线图
        :param data: 数据列表，支持多组数据
        :param labels: 标签列表
        :param title: 图表标题
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(data))
        
        c = Boxplot(init_opts=opts.InitOpts(theme='light'))
        
        x_data = labels if labels else [f'系列{i+1}' for i in range(len(data))]
        y_data = [Boxplot.prepare_data(d) for d in data]
        
        c.add_xaxis(x_data)
        for i, d in enumerate(y_data):
            c.add_yaxis(f'系列{i+1}', d)
        
        c = self._init_global_opts(c, title=title, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def histogram(self, data, bins=10, title='直方图', xlabel='数值', ylabel='频数', color=None, save_path=None, **kwargs):
        '''
        生成直方图
        :param data: 数据列表
        :param bins: 分箱数量
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param color: 颜色，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if color is None:
            color = self.get_color(1)[0]
        
        hist, bin_edges = np.histogram(data, bins=bins)
        bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
        
        c = Bar(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis([f'{edge:.2f}' for edge in bin_centers])
        c.add_yaxis(ylabel, hist.tolist(), color=color)
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def area(self, x, y, title='面积图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, smooth=False, **kwargs):
        '''
        生成面积图
        :param x: X轴数据
        :param y: Y轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param smooth: 是否平滑曲线
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(1)
        
        c = Line(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis(list(x))
        c.add_yaxis(ylabel, list(y), color=colors[0], is_smooth=smooth, areastyle_opts=opts.AreaStyleOpts(opacity=0.6))
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def stacked_bar(self, x, y, title='堆叠柱状图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, **kwargs):
        '''
        生成堆叠柱状图
        :param x: X轴数据
        :param y: Y轴数据，二维数组
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(y))
        
        c = Bar(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis(list(x))
        
        for i, yi in enumerate(y):
            c.add_yaxis(f'系列{i+1}', list(yi), color=colors[i], stack='stack1')
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def grouped_bar(self, x, y, group_labels=None, title='分组柱状图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, **kwargs):
        '''
        生成分组柱状图
        :param x: X轴数据
        :param y: Y轴数据，二维数组
        :param group_labels: 分组标签
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(y))
        
        c = Bar(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis(list(x))
        
        for i, yi in enumerate(y):
            label = group_labels[i] if group_labels else f'系列{i+1}'
            c.add_yaxis(label, list(yi), color=colors[i])
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def horizontal_bar(self, y, x, title='水平柱状图', xlabel='X轴', ylabel='Y轴', colors=None, save_path=None, **kwargs):
        '''
        生成水平柱状图
        :param y: Y轴数据
        :param x: X轴数据
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(y))
        
        c = Bar(init_opts=opts.InitOpts(theme='light'))
        c.add_xaxis(list(y))
        c.add_yaxis(xlabel, list(x), color=colors[0])
        c.reversal_axis()
        
        c = self._init_global_opts(c, title=title, xlabel=xlabel, ylabel=ylabel, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def radar(self, data, categories, title='雷达图', colors=None, save_path=None, **kwargs):
        '''
        生成雷达图
        :param data: 数据列表，支持多组数据
        :param categories: 分类标签
        :param title: 图表标题
        :param colors: 颜色列表，为None时自动获取
        :param save_path: 保存路径，为None时在Jupyter中显示
        :param kwargs: 其他配置选项，支持所有pyecharts全局配置参数
        '''
        if colors is None:
            colors = self.get_color(len(data))
        
        c = Radar(init_opts=opts.InitOpts(theme='light'))
        
        schema = [opts.RadarIndicatorItem(name=cat, max_=100) for cat in categories]
        c.add_schema(schema=schema)
        
        for i, d in enumerate(data):
            c.add(f'系列{i+1}', [list(d)], color=colors[i])
        
        legend_opts = kwargs.pop('legend_opts', opts.LegendOpts(pos_left="center", pos_top="top"))
        c = self._init_global_opts(c, title=title, legend_opts=legend_opts, **kwargs)
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c

    def heatmap(self, data, title='热力图', xlabel='X轴', ylabel='Y轴', 
                xticklabels=None, yticklabels=None, save_path=None, **kwargs):
        '''
        生成热力图
        :param data: 二维数据矩阵
        :param title: 图表标题
        :param xlabel: X轴标签
        :param ylabel: Y轴标签
        :param xticklabels: X轴刻度标签列表
        :param yticklabels: Y轴刻度标签列表
        :param save_path: 保存路径
        :param kwargs: 其他配置选项
        '''
        c = PyechartsHeatMap(init_opts=opts.InitOpts(theme='light'))
        
        # 准备热力图数据格式：[x, y, value]
        heatmap_data = []
        rows, cols = data.shape[0], data.shape[1]
        
        for i in range(rows):
            for j in range(cols):
                heatmap_data.append([j, i, float(data[i, j])])
        
        # 设置X轴刻度标签
        if xticklabels is None:
            xticklabels = [str(i) for i in range(cols)]
        
        # 设置Y轴刻度标签
        if yticklabels is None:
            yticklabels = [str(i) for i in range(rows)]
        
        c.add_xaxis(xticklabels)
        c.add_yaxis(
            series_name='',
            yaxis_data=yticklabels,
            value=heatmap_data,
            label_opts=opts.LabelOpts(is_show=False)
        )
        
        # 设置视觉映射组件
        c.set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(name=xlabel, type_='category'),
            yaxis_opts=opts.AxisOpts(name=ylabel, type_='category'),
            visualmap_opts=opts.VisualMapOpts(
                min_=np.min(data),
                max_=np.max(data),
                is_show=True,
                orient='horizontal',
                pos_left='center',
                pos_bottom='5%'
            ),
            **kwargs
        )
        
        if save_path:
            c.render(save_path)
        else:
            c.render_notebook()
        
        return c
