"""基于 matplotlib 的项目级绘图封装。"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap, to_hex
from matplotlib.figure import Figure

try:
    import seaborn as sns
except ModuleNotFoundError:  # pragma: no cover - seaborn 缺失时走降级逻辑
    sns = None


Number = Union[int, float, np.number]
ArrayLike = Union[Sequence[Number], np.ndarray, pd.Series]
DEFAULT_COLOR_PALETTE = sns.color_palette("Set2")[:5]
# ["#2F5B8A", "#D47F3B", "#4B7F52", "#C04343", "#7A5C99"]


# === config ===


@dataclass(slots=True)
class ChartStyle:
    """单类图表的默认样式配置。"""

    figsize: Optional[tuple[float, float]] = None
    colors: Optional[list[str]] = None
    color: Optional[str] = None
    linewidth: Optional[float] = None
    marker: Optional[str] = None
    markersize: Optional[float] = None
    alpha: Optional[float] = None
    size: Optional[float] = None
    bins: Optional[int] = None
    cmap: Optional[str] = None
    annot: Optional[bool] = None
    fmt: Optional[str] = None
    edgecolor: Optional[str] = None
    edge_linewidth: Optional[float] = None
    grid: Optional[bool] = None
    autopct: Optional[str] = None
    startangle: Optional[float] = None
    bar_width: Optional[float] = None
    rotation: Optional[float] = None
    value_labels: Optional[bool] = None
    value_fontsize: Optional[int] = None
    value_fontweight: Optional[str] = None
    value_color: Optional[str] = None
    value_fmt: Optional[str] = None
    style_kwargs: dict[str, Any] = field(default_factory=dict)

    def merged(self, **overrides: Any) -> "ChartStyle":
        """返回合并后的图型样式副本。"""
        merged_data = asdict(self)
        style_kwargs = dict(merged_data.pop("style_kwargs", {}))

        extra_style_kwargs = overrides.pop("style_kwargs", None)
        for key, value in overrides.items():
            if key in merged_data and value is not None:
                merged_data[key] = value

        if isinstance(extra_style_kwargs, Mapping):
            style_kwargs.update(extra_style_kwargs)
        merged_data["style_kwargs"] = style_kwargs
        return ChartStyle(**merged_data)


@dataclass(slots=True)
class ThemeConfig:
    """全局主题配置。"""

    style: str = "white"
    palette: list[str] = field(
        default_factory=lambda: sns.color_palette("Set2")[:5]
    )
    figsize: tuple[float, float] = (10.0, 6.0)
    dpi: int = 150
    title_fontsize: int = 14
    label_fontsize: int = 12
    tick_fontsize: int = 10
    legend_fontsize: int = 10
    title_fontweight: str = "bold"
    title_pad: int = 12
    axis_labelpad: int = 8
    grid: bool = False
    alpha: float = 0.9
    edgecolor: str = "white"
    edge_linewidth: float = 0.8
    value_fontsize: int = 10
    value_fontweight: str = "semibold"
    value_color: str = "#243447"
    chart_styles: dict[str, ChartStyle] = field(default_factory=dict)

    def get_chart_style(self, chart_type: str) -> ChartStyle:
        """获取图型默认样式。不存在时返回空样式。"""
        return copy.deepcopy(self.chart_styles.get(chart_type, ChartStyle()))


def _build_chart_styles(
    *,
    line_color: str,
    bar_color: str,
    scatter_color: str,
    heatmap_cmap: str,
) -> dict[str, ChartStyle]:
    """构建主题对应的图型级默认样式。"""
    return {
        "line": ChartStyle(
            figsize=(10, 6),
            color=line_color,
            linewidth=2.2,
            marker="o",
            markersize=5.0,
            grid=False,
            value_labels=True,
            value_fmt=".2f",
        ),
        "scatter": ChartStyle(
            figsize=(10, 6),
            color=scatter_color,
            alpha=0.78,
            size=65.0,
            edgecolor="white",
            edge_linewidth=0.6,
            grid=False,
        ),
        "bar": ChartStyle(
            figsize=(10, 6),
            color=bar_color,
            alpha=0.92,
            edgecolor="white",
            edge_linewidth=0.8,
            bar_width=0.72,
            rotation=25.0,
            grid=False,
            value_labels=True,
            value_fmt=".2f",
        ),
        "grouped_bar": ChartStyle(
            figsize=(10, 6),
            color=bar_color,
            alpha=0.92,
            edgecolor="white",
            edge_linewidth=0.8,
            bar_width=0.72,
            rotation=25.0,
            grid=False,
            value_labels=True,
            value_fmt=".2f",
        ),
        "horizontal_bar": ChartStyle(
            figsize=(10, 6),
            color=bar_color,
            alpha=0.92,
            edgecolor="white",
            edge_linewidth=0.8,
            grid=False,
            value_labels=True,
            value_fmt=".2f",
        ),
        "area": ChartStyle(
            figsize=(10, 6),
            color=line_color,
            alpha=0.35,
            linewidth=1.8,
            grid=False,
        ),
        "histogram": ChartStyle(
            figsize=(10, 6),
            color=bar_color,
            bins=20,
            alpha=0.75,
            edgecolor="white",
            edge_linewidth=0.8,
            grid=False,
            value_labels=True,
            value_fmt=".0f",
        ),
        "box": ChartStyle(figsize=(10, 6), grid=False),
        "violin": ChartStyle(figsize=(10, 6), grid=False),
        "heatmap": ChartStyle(
            figsize=(10, 8),
            cmap=heatmap_cmap,
            annot=True,
            fmt=".2f",
            grid=False,
        ),
        "pie": ChartStyle(
            figsize=(9, 7),
            autopct="%1.1f%%",
            startangle=90.0,
            grid=False,
            value_labels=True,
            value_fmt=".2f",
            value_color="white",
            value_fontweight="bold",
        ),
        "radar": ChartStyle(figsize=(8, 8), alpha=0.22, grid=False),
        "joint_plot": ChartStyle(figsize=(9, 9), grid=False),
    }


# === managers ===


class ThemeRegistry:
    """主题注册中心。"""

    _themes: dict[str, ThemeConfig] = {}

    @classmethod
    def register_theme(cls, name: str, config: ThemeConfig) -> None:
        cls._themes[name] = copy.deepcopy(config)

    @classmethod
    def get_theme(cls, name: str) -> ThemeConfig:
        if name not in cls._themes:
            raise ValueError(f"未找到主题：{name}。可用主题：{', '.join(cls.list_themes())}")
        return copy.deepcopy(cls._themes[name])

    @classmethod
    def list_themes(cls) -> list[str]:
        return sorted(cls._themes.keys())


class StyleManager:
    """处理 matplotlib / seaborn 的全局风格设置。"""

    @classmethod
    def setup_chinese(cls) -> None:
        """配置常见中文字体，避免中文标题乱码。"""
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Noto Sans CJK SC",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False

    @staticmethod
    def apply_theme(theme: ThemeConfig) -> None:
        """应用主题到当前 matplotlib 环境。"""
        if sns is not None:
            sns.set_theme(style=theme.style, palette=theme.palette)
        else:
            style_mapping = {
                "whitegrid": "seaborn-v0_8-whitegrid",
                "darkgrid": "seaborn-v0_8-darkgrid",
                "white": "seaborn-v0_8-white",
                "ticks": "seaborn-v0_8-ticks",
            }
            plt.style.use(style_mapping.get(theme.style, "default"))

        StyleManager.setup_chinese()
        plt.rcParams["figure.dpi"] = theme.dpi
        plt.rcParams["axes.titlesize"] = theme.title_fontsize
        plt.rcParams["axes.labelsize"] = theme.label_fontsize
        plt.rcParams["xtick.labelsize"] = theme.tick_fontsize
        plt.rcParams["ytick.labelsize"] = theme.tick_fontsize
        plt.rcParams["legend.fontsize"] = theme.legend_fontsize
        plt.rcParams["axes.titleweight"] = theme.title_fontweight
        plt.rcParams["axes.grid"] = theme.grid
        plt.rcParams["axes.prop_cycle"] = cycler(color=theme.palette)


class FigureManager:
    """管理 figure / axes 生命周期，避免脚本中散落式操作。"""

    def __init__(self, figsize: tuple[float, float] = (10, 6), dpi: int = 150):
        self.default_figsize = figsize
        self.default_dpi = dpi
        self.figure: Optional[Figure] = None
        self.axes: list[Axes] = []
        self.axes_array: Any = None
        self.current_index = 0
        self.is_subplot_mode = False

    def _figure_invalid(self) -> bool:
        if self.figure is None:
            return True
        return not plt.fignum_exists(self.figure.number)

    def create_figure(
        self,
        figsize: Optional[tuple[float, float]] = None,
        dpi: Optional[int] = None,
    ) -> tuple[Figure, Axes]:
        """创建单图 figure。"""
        self.close()
        fig, ax = plt.subplots(figsize=figsize or self.default_figsize, dpi=dpi or self.default_dpi)
        self.figure = fig
        self.axes = [ax]
        self.axes_array = ax
        self.current_index = 0
        self.is_subplot_mode = False
        return fig, ax

    def create_subplots(
        self,
        nrows: int = 1,
        ncols: int = 1,
        figsize: Optional[tuple[float, float]] = None,
        dpi: Optional[int] = None,
        sharex: bool = False,
        sharey: bool = False,
    ) -> tuple[Figure, Any]:
        """创建子图布局。"""
        self.close()
        fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=figsize or self.default_figsize,
            dpi=dpi or self.default_dpi,
            sharex=sharex,
            sharey=sharey,
        )
        flat_axes = np.atleast_1d(axes).ravel().tolist()
        self.figure = fig
        self.axes = flat_axes
        self.axes_array = axes
        self.current_index = 0
        self.is_subplot_mode = len(flat_axes) > 1
        return fig, axes

    def ensure_single_axes(
        self,
        figsize: Optional[tuple[float, float]] = None,
        dpi: Optional[int] = None,
    ) -> tuple[Figure, Axes]:
        """确保存在单图 axes。"""
        if self._figure_invalid() or not self.axes:
            return self.create_figure(figsize=figsize, dpi=dpi)

        if self.is_subplot_mode:
            ax = self.get_ax()
            ax.clear()
            return self.figure, ax

        ax = self.axes[0]
        ax.clear()
        return self.figure, ax

    def get_ax(self, position: Optional[int] = None) -> Axes:
        """获取当前或指定位置的子图。"""
        if self._figure_invalid() or not self.axes:
            _, ax = self.create_figure()
            return ax

        if position is None:
            position = self.current_index
        if not (0 <= position < len(self.axes)):
            raise IndexError(f"子图索引越界：{position}，当前共有 {len(self.axes)} 个子图")

        self.current_index = position
        return self.axes[position]

    def set_position(self, position: int) -> Axes:
        """切换当前子图。"""
        return self.get_ax(position=position)

    def next_ax(self) -> Axes:
        """切换到下一个子图。"""
        if not self.axes:
            _, ax = self.create_figure()
            return ax
        self.current_index = (self.current_index + 1) % len(self.axes)
        return self.axes[self.current_index]

    def save(
        self,
        save_path: Union[str, Path],
        dpi: Optional[int] = None,
        bbox_inches: str = "tight",
        **kwargs: Any,
    ) -> Path:
        """保存当前图像。"""
        if self._figure_invalid():
            raise RuntimeError("当前没有可保存的图像，请先完成绘图")

        path = Path(save_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.figure.savefig(path, dpi=dpi or self.default_dpi, bbox_inches=bbox_inches, **kwargs)
        return path

    def close(self) -> None:
        """关闭当前 figure。"""
        if self.figure is not None:
            plt.close(self.figure)
        self.figure = None
        self.axes = []
        self.axes_array = None
        self.current_index = 0
        self.is_subplot_mode = False

def _normalize_sequence(data: Optional[ArrayLike]) -> Optional[np.ndarray]:
    """将输入转为一维 numpy 数组。"""
    if data is None:
        return None
    if isinstance(data, pd.Series):
        array = data.to_numpy()
    else:
        array = np.asarray(data)
    return np.ravel(array)


def _normalize_matrix(data: Union[pd.DataFrame, np.ndarray, Sequence[Sequence[Any]]]) -> np.ndarray:
    """将输入转为二维矩阵。"""
    if isinstance(data, pd.DataFrame):
        array = data.to_numpy()
    else:
        array = np.asarray(data)
    if array.ndim != 2:
        raise ValueError(f"输入数据必须是二维矩阵，当前维度为 {array.ndim}")
    return array


def _iter_series(y: Union[ArrayLike, Sequence[ArrayLike], np.ndarray]) -> list[np.ndarray]:
    """将单序列或多序列统一转换为列表。"""
    array = np.asarray(y, dtype=object)
    if array.ndim == 1 and len(array) > 0 and isinstance(array[0], (list, tuple, np.ndarray, pd.Series)):
        return [_normalize_sequence(item) for item in y]  # type: ignore[arg-type]
    if np.asarray(y).ndim == 2:
        return [np.asarray(row) for row in np.asarray(y)]
    return [_normalize_sequence(y)]  # type: ignore[arg-type]


def _resolve_labels(labels: Optional[Sequence[str]], count: int, prefix: str = "序列") -> list[str]:
    """为多序列场景补齐标签。"""
    if labels is None:
        return [f"{prefix}{idx + 1}" for idx in range(count)]
    label_list = list(labels)
    if len(label_list) != count:
        raise ValueError(f"标签数量与序列数量不一致：{len(label_list)} != {count}")
    return label_list


# === plotter ===


class Plotter:
    """项目主绘图入口。"""

    def __init__(
        self,
        theme: Union[str, ThemeConfig] = "report",
        figsize: Optional[tuple[float, float]] = None,
        dpi: Optional[int] = None,
    ):
        self.theme = ThemeRegistry.get_theme(theme) if isinstance(theme, str) else copy.deepcopy(theme)
        if figsize is not None:
            self.theme.figsize = figsize
        if dpi is not None:
            self.theme.dpi = dpi

        StyleManager.apply_theme(self.theme)
        self.figure_manager = FigureManager(figsize=self.theme.figsize, dpi=self.theme.dpi)

    def update_theme(self, **kwargs: Any) -> "Plotter":
        """更新全局主题配置。"""
        for key, value in kwargs.items():
            if not hasattr(self.theme, key):
                raise AttributeError(f"ThemeConfig 不存在字段：{key}")
            setattr(self.theme, key, value)

        self.figure_manager.default_figsize = self.theme.figsize
        self.figure_manager.default_dpi = self.theme.dpi
        StyleManager.apply_theme(self.theme)
        return self

    def update_chart_style(self, chart_type: str, **kwargs: Any) -> "Plotter":
        """更新某类图表的默认样式。"""
        base_style = self.theme.get_chart_style(chart_type)
        self.theme.chart_styles[chart_type] = base_style.merged(**kwargs)
        return self

    @staticmethod
    def get_colors(
        count: int,
        palette: Optional[Sequence[str]] = None,
        start_index: int = 0,
        randomize: bool = False,
        seed: Optional[int] = None,
    ) -> list[str]:
        """
        按数量返回颜色列表。

        - `randomize=False` 时，基于调色板循环或插值补齐颜色
        - `randomize=True` 时，直接生成随机颜色
        """
        if count < 0:
            raise ValueError("count 不能小于 0")
        if count == 0:
            return []

        if randomize:
            rng = np.random.default_rng(seed)
            rgb_values = rng.integers(0, 256, size=(count, 3))
            return [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in rgb_values]

        base_palette = list(palette) if palette else DEFAULT_COLOR_PALETTE
        if len(base_palette) == 1:
            return [base_palette[0]] * count

        if count <= len(base_palette):
            offset = start_index % len(base_palette)
            return [base_palette[(offset + idx) % len(base_palette)] for idx in range(count)]

        cmap = LinearSegmentedColormap.from_list("ljp_plot_palette", base_palette)
        colors = [to_hex(cmap(position)) for position in np.linspace(0, 1, count)]
        if start_index:
            offset = start_index % count
            colors = colors[offset:] + colors[:offset]
        return colors

    def _chart_style(self, chart_type: str) -> ChartStyle:
        return self.theme.get_chart_style(chart_type)

    def _ensure_axes(
        self,
        chart_type: str,
        figsize: Optional[tuple[float, float]] = None,
    ) -> tuple[Figure, Axes, ChartStyle]:
        """根据图型样式确保 figure/axes 已准备好。"""
        chart_style = self._chart_style(chart_type)
        target_figsize = figsize or chart_style.figsize or self.theme.figsize
        fig, ax = self.figure_manager.ensure_single_axes(figsize=target_figsize, dpi=self.theme.dpi)
        return fig, ax, chart_style

    def _get_active_ax(
        self,
        chart_type: str,
        position: Optional[int] = None,
    ) -> tuple[Figure, Axes, ChartStyle]:
        """在已有子图布局中获取当前子图。"""
        chart_style = self._chart_style(chart_type)
        ax = self.figure_manager.get_ax(position=position)
        ax.clear()
        if self.figure_manager.figure is None:
            raise RuntimeError("当前 figure 不存在")
        return self.figure_manager.figure, ax, chart_style

    def _setup_axes(
        self,
        ax: Axes,
        chart_style: ChartStyle,
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        grid: Optional[bool] = None,
        xrotation: Optional[float] = None,
    ) -> None:
        """统一处理坐标轴标题、标签和网格。"""
        if title:
            ax.set_title(
                title,
                fontsize=self.theme.title_fontsize,
                fontweight=self.theme.title_fontweight,
                pad=self.theme.title_pad,
            )
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=self.theme.label_fontsize, labelpad=self.theme.axis_labelpad)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=self.theme.label_fontsize, labelpad=self.theme.axis_labelpad)

        ax.tick_params(axis="both", labelsize=self.theme.tick_fontsize)
        if "top" in ax.spines:
            ax.spines["top"].set_visible(False)
        if "right" in ax.spines:
            ax.spines["right"].set_visible(False)

        resolved_grid = chart_style.grid if grid is None else grid
        if resolved_grid is None:
            resolved_grid = self.theme.grid
        if resolved_grid:
            ax.grid(True, alpha=0.25)
        else:
            ax.grid(False)

        rotation = chart_style.rotation if xrotation is None else xrotation
        if rotation:
            for label in ax.get_xticklabels():
                label.set_rotation(rotation)
                label.set_ha("right")

    def _value_text_kwargs(
        self,
        chart_style: ChartStyle,
        *,
        color: Optional[str] = None,
    ) -> dict[str, Any]:
        """解析数值标注文本样式。"""
        return {
            "fontsize": chart_style.value_fontsize or self.theme.value_fontsize,
            "fontweight": chart_style.value_fontweight or self.theme.value_fontweight,
            "color": color or chart_style.value_color or self.theme.value_color,
        }

    @staticmethod
    def _format_value(value: Any, value_fmt: Optional[str] = None) -> str:
        """将数值格式化为更紧凑的显示文本。"""
        numeric_value = float(value)
        if value_fmt:
            return format(numeric_value, value_fmt)
        if np.isclose(numeric_value, round(numeric_value)):
            return str(int(round(numeric_value)))
        return f"{numeric_value:.2f}".rstrip("0").rstrip(".")

    def _annotate_line_points(
        self,
        ax: Axes,
        x_values: np.ndarray,
        y_values: np.ndarray,
        chart_style: ChartStyle,
        value_fmt: Optional[str] = None,
    ) -> None:
        """为折线图点位添加数值标注。"""
        text_kwargs = self._value_text_kwargs(chart_style)
        for x_value, y_value in zip(x_values, y_values):
            if pd.isna(y_value):
                continue
            vertical_alignment = "bottom" if float(y_value) >= 0 else "top"
            y_offset = 6 if float(y_value) >= 0 else -8
            ax.annotate(
                self._format_value(y_value, value_fmt),
                xy=(x_value, y_value),
                xytext=(0, y_offset),
                textcoords="offset points",
                ha="center",
                va=vertical_alignment,
                clip_on=False,
                **text_kwargs,
            )

    def _annotate_vertical_bars(
        self,
        ax: Axes,
        bars: Sequence[Any],
        chart_style: ChartStyle,
        value_fmt: Optional[str] = None,
    ) -> None:
        """为纵向柱体添加居中数值标注。"""
        text_kwargs = self._value_text_kwargs(chart_style)
        for bar in bars:
            height = float(bar.get_height())
            if pd.isna(height):
                continue
            top_value = float(bar.get_y()) + height
            vertical_alignment = "bottom" if height >= 0 else "top"
            y_offset = 5 if height >= 0 else -7
            ax.annotate(
                self._format_value(height, value_fmt),
                xy=(bar.get_x() + bar.get_width() / 2, top_value),
                xytext=(0, y_offset),
                textcoords="offset points",
                ha="center",
                va=vertical_alignment,
                clip_on=False,
                **text_kwargs,
            )

    def _annotate_horizontal_bars(
        self,
        ax: Axes,
        bars: Sequence[Any],
        chart_style: ChartStyle,
        value_fmt: Optional[str] = None,
    ) -> None:
        """为横向柱体添加数值标注。"""
        text_kwargs = self._value_text_kwargs(chart_style)
        for bar in bars:
            width = float(bar.get_width())
            if pd.isna(width):
                continue
            end_value = float(bar.get_x()) + width
            horizontal_alignment = "left" if width >= 0 else "right"
            x_offset = 5 if width >= 0 else -7
            ax.annotate(
                self._format_value(width, value_fmt),
                xy=(end_value, bar.get_y() + bar.get_height() / 2),
                xytext=(x_offset, 0),
                textcoords="offset points",
                ha=horizontal_alignment,
                va="center",
                clip_on=False,
                **text_kwargs,
            )

    def _build_pie_autopct(
        self,
        sizes: np.ndarray,
        chart_style: ChartStyle,
        value_fmt: Optional[str] = None,
    ):
        """构建同时显示占比和原值的饼图标注函数。"""
        total = float(np.sum(sizes))
        percent_fmt = chart_style.autopct or "%1.1f%%"

        def _autopct(percent: float) -> str:
            raw_value = total * percent / 100
            percent_text = percent_fmt % percent
            value_text = self._format_value(raw_value, value_fmt)
            return f"{percent_text}\n{value_text}"

        return _autopct

    def _apply_legend(self, ax: Axes, legend: Optional[bool]) -> None:
        """按需显示图例。"""
        if legend is False:
            return
        handles, labels = ax.get_legend_handles_labels()
        if handles and any(label and not label.startswith("_") for label in labels):
            ax.legend(loc="best", fontsize=self.theme.legend_fontsize)

    def _finalize(
        self,
        *,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        tight_layout: bool = True,
        legend: Optional[bool] = None,
        ax: Optional[Axes] = None,
    ) -> Optional[Path]:
        """统一处理保存、展示和图例。"""
        if ax is not None:
            self._apply_legend(ax, legend)
        if tight_layout and self.figure_manager.figure is not None:
            self.figure_manager.figure.tight_layout()

        saved_path: Optional[Path] = None

        if save_path is not None:
            saved_path = self.figure_manager.save(save_path)
        if show and self.figure_manager.figure is not None:
            plt.show()
        return saved_path

    def create_subplots(
        self,
        nrows: int = 1,
        ncols: int = 1,
        figsize: Optional[tuple[float, float]] = None,
        sharex: bool = False,
        sharey: bool = False,
    ) -> tuple[Figure, Any]:
        """创建子图布局。"""
        return self.figure_manager.create_subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=figsize or self.theme.figsize,
            dpi=self.theme.dpi,
            sharex=sharex,
            sharey=sharey,
        )

    def set_subplot(self, position: int) -> Axes:
        """切换到指定子图。"""
        return self.figure_manager.set_position(position)

    def next_subplot(self) -> Axes:
        """切换到下一个子图。"""
        return self.figure_manager.next_ax()

    def close(self) -> None:
        """关闭当前图像。"""
        self.figure_manager.close()

    def line(
        self,
        x: ArrayLike,
        y: Union[ArrayLike, Sequence[ArrayLike], np.ndarray],
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
        labels: Optional[Sequence[str]] = None,
        label: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        legend: Optional[bool] = None,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制折线图。"""
        if self.figure_manager.is_subplot_mode:
            fig, ax, chart_style = self._get_active_ax("line", position=position)
        else:
            fig, ax, chart_style = self._ensure_axes("line", figsize=figsize)

        x_values = _normalize_sequence(x)
        y_series = _iter_series(y)
        series_labels = [label] if label is not None and len(y_series) == 1 else _resolve_labels(labels, len(y_series))
        color_list = list(colors) if colors is not None else chart_style.colors or self.theme.palette

        line_kwargs = dict(chart_style.style_kwargs)
        line_kwargs.setdefault("linewidth", chart_style.linewidth or 2.0)
        line_kwargs.setdefault("marker", chart_style.marker)
        line_kwargs.setdefault("markersize", chart_style.markersize)
        line_kwargs.setdefault("alpha", chart_style.alpha or self.theme.alpha)
        line_kwargs.update(kwargs)
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate

        for idx, series in enumerate(y_series):
            if len(series) != len(x_values):
                raise ValueError(f"x 与第 {idx + 1} 条序列长度不一致：{len(x_values)} != {len(series)}")
            series_kwargs = dict(line_kwargs)
            series_kwargs["color"] = color_list[idx % len(color_list)]
            series_kwargs["label"] = series_labels[idx]
            ax.plot(x_values, series, **series_kwargs)
            if should_annotate:
                self._annotate_line_points(
                    ax=ax,
                    x_values=np.asarray(x_values),
                    y_values=np.asarray(series, dtype=float),
                    chart_style=chart_style,
                    value_fmt=value_fmt or chart_style.value_fmt,
                )

        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def bar(
        self,
        x: Sequence[Any],
        y: ArrayLike,
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
        color: Optional[str] = None,
        label: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        legend: Optional[bool] = None,
        rotation: Optional[float] = None,
        width: Optional[float] = None,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制柱状图。"""
        if self.figure_manager.is_subplot_mode:
            fig, ax, chart_style = self._get_active_ax("bar", position=position)
        else:
            fig, ax, chart_style = self._ensure_axes("bar", figsize=figsize)

        y_values = _normalize_sequence(y)
        if len(x) != len(y_values):
            raise ValueError(f"x 与 y 长度不一致：{len(x)} != {len(y_values)}")

        bar_kwargs = dict(chart_style.style_kwargs)
        bar_kwargs.setdefault("alpha", chart_style.alpha or self.theme.alpha)
        bar_kwargs.setdefault("edgecolor", chart_style.edgecolor or self.theme.edgecolor)
        bar_kwargs.setdefault("linewidth", chart_style.edge_linewidth or self.theme.edge_linewidth)
        bar_kwargs.update(kwargs)

        if colors is not None:
            bar_kwargs["color"] = list(colors)
        elif color is not None:
            bar_kwargs["color"] = color
        elif chart_style.colors:
            bar_kwargs["color"] = self.get_colors(len(x), palette=chart_style.colors)
        else:
            bar_kwargs["color"] = self.get_colors(len(x))
        if label is not None:
            bar_kwargs["label"] = label

        bars = ax.bar(x, y_values, width=width or chart_style.bar_width or 0.72, **bar_kwargs)
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate
        if should_annotate:
            self._annotate_vertical_bars(ax, bars, chart_style, value_fmt or chart_style.value_fmt)
        self._setup_axes(
            ax,
            chart_style,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            grid=grid,
            xrotation=rotation,
        )
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def grouped_bar(
        self,
        x: Sequence[Any],
        data: Sequence[ArrayLike],
        *,
        labels: Sequence[str],
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        legend: Optional[bool] = None,
        rotation: Optional[float] = None,
        width: Optional[float] = None,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制并排多组柱状图。"""
        if self.figure_manager.is_subplot_mode:
            fig, ax, chart_style = self._get_active_ax("grouped_bar", position=position)
        else:
            fig, ax, chart_style = self._ensure_axes("grouped_bar", figsize=figsize)

        if len(data) == 0:
            raise ValueError("data 不能为空，至少需要一组柱状图数据")
        if len(labels) != len(data):
            raise ValueError(f"labels 数量与数据组数不一致：{len(labels)} != {len(data)}")

        category_positions = np.arange(len(x), dtype=float)
        series_count = len(data)
        bar_width = width or min(0.8 / series_count, 0.35)
        if colors is not None:
            color_list = list(colors)
        elif chart_style.colors:
            color_list = self.get_colors(series_count, palette=chart_style.colors)
        else:
            color_list = self.get_colors(series_count, palette=self.theme.palette)

        base_kwargs = dict(chart_style.style_kwargs)
        base_kwargs.setdefault("alpha", chart_style.alpha or self.theme.alpha)
        base_kwargs.setdefault("edgecolor", chart_style.edgecolor or self.theme.edgecolor)
        base_kwargs.setdefault("linewidth", chart_style.edge_linewidth or self.theme.edge_linewidth)
        base_kwargs.update(kwargs)
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate

        for idx, values in enumerate(data):
            value_array = _normalize_sequence(values)
            if len(value_array) != len(x):
                raise ValueError(f"第 {idx + 1} 组数据长度与 x 不一致：{len(value_array)} != {len(x)}")

            offset = (idx - (series_count - 1) / 2) * bar_width
            series_kwargs = dict(base_kwargs)
            series_kwargs["color"] = color_list[idx % len(color_list)]
            series_kwargs["label"] = labels[idx]
            bars = ax.bar(category_positions + offset, value_array, width=bar_width, **series_kwargs)

            if should_annotate:
                self._annotate_vertical_bars(ax, bars, chart_style, value_fmt or chart_style.value_fmt)

        ax.set_xticks(category_positions)
        ax.set_xticklabels(list(x))
        self._setup_axes(
            ax,
            chart_style,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            grid=grid,
            xrotation=rotation,
        )
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def horizontal_bar(
        self,
        y: Sequence[Any],
        x: ArrayLike,
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
        color: Optional[str] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        legend: Optional[bool] = None,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制横向柱状图。"""
        if self.figure_manager.is_subplot_mode:
            fig, ax, chart_style = self._get_active_ax("horizontal_bar", position=position)
        else:
            fig, ax, chart_style = self._ensure_axes("horizontal_bar")

        x_values = _normalize_sequence(x)
        if len(y) != len(x_values):
            raise ValueError(f"x 与 y 长度不一致：{len(x_values)} != {len(y)}")

        bar_kwargs = dict(chart_style.style_kwargs)
        bar_kwargs.setdefault("alpha", chart_style.alpha or self.theme.alpha)
        bar_kwargs.setdefault("edgecolor", chart_style.edgecolor or self.theme.edgecolor)
        bar_kwargs.setdefault("linewidth", chart_style.edge_linewidth or self.theme.edge_linewidth)
        bar_kwargs.update(kwargs)
        if colors is not None:
            bar_kwargs["color"] = list(colors)
        elif color is not None:
            bar_kwargs["color"] = color
        elif chart_style.colors:
            bar_kwargs["color"] = self.get_colors(len(y), palette=chart_style.colors)
        else:
            bar_kwargs["color"] = self.get_colors(len(y))

        bars = ax.barh(y, x_values, **bar_kwargs)
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate
        if should_annotate:
            self._annotate_horizontal_bars(ax, bars, chart_style, value_fmt or chart_style.value_fmt)
        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def scatter(
        self,
        x: ArrayLike,
        y: ArrayLike,
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        color: Optional[str] = None,
        label: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        legend: Optional[bool] = None,
        position: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制散点图。"""
        if self.figure_manager.is_subplot_mode:
            fig, ax, chart_style = self._get_active_ax("scatter", position=position)
        else:
            fig, ax, chart_style = self._ensure_axes("scatter", figsize=figsize)

        x_values = _normalize_sequence(x)
        y_values = _normalize_sequence(y)
        if len(x_values) != len(y_values):
            raise ValueError(f"x 与 y 长度不一致：{len(x_values)} != {len(y_values)}")

        scatter_kwargs = dict(chart_style.style_kwargs)
        scatter_kwargs.setdefault("alpha", chart_style.alpha or self.theme.alpha)
        scatter_kwargs.setdefault("s", chart_style.size or 50.0)
        scatter_kwargs.setdefault("edgecolors", chart_style.edgecolor or self.theme.edgecolor)
        scatter_kwargs.setdefault("linewidths", chart_style.edge_linewidth or self.theme.edge_linewidth)
        scatter_kwargs.update(kwargs)

        if "c" not in scatter_kwargs and color is not None:
            scatter_kwargs["color"] = color
        elif "c" not in scatter_kwargs and "color" not in scatter_kwargs:
            scatter_kwargs["color"] = chart_style.color or self.theme.palette[0]
        if label is not None:
            scatter_kwargs["label"] = label

        ax.scatter(x_values, y_values, **scatter_kwargs)
        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def area(
        self,
        x: ArrayLike,
        y: Union[ArrayLike, Sequence[ArrayLike], np.ndarray],
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
        labels: Optional[Sequence[str]] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        legend: Optional[bool] = None,
        stacked: bool = False,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制面积图。"""
        fig, ax, chart_style = self._ensure_axes("area", figsize=figsize)
        x_values = _normalize_sequence(x)
        y_series = _iter_series(y)
        color_list = list(colors) if colors is not None else chart_style.colors or self.theme.palette
        series_labels = _resolve_labels(labels, len(y_series))

        if stacked and len(y_series) > 1:
            ax.stackplot(x_values, *y_series, labels=series_labels, colors=color_list, alpha=chart_style.alpha or 0.35, **kwargs)
        else:
            for idx, series in enumerate(y_series):
                ax.fill_between(
                    x_values,
                    series,
                    color=color_list[idx % len(color_list)],
                    alpha=chart_style.alpha or 0.35,
                    label=series_labels[idx],
                    **kwargs,
                )

        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def stacked_bar(
        self,
        x: Sequence[Any],
        data: Sequence[ArrayLike],
        *,
        labels: Sequence[str],
        colors: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制堆叠柱状图。"""
        fig, ax, chart_style = self._ensure_axes("bar")
        color_list = list(colors) if colors is not None else self.theme.palette
        bottom = np.zeros(len(x), dtype=float)
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate

        for idx, values in enumerate(data):
            value_array = _normalize_sequence(values)
            if len(value_array) != len(x):
                raise ValueError(f"第 {idx + 1} 组数据长度与 x 不一致")
            bars = ax.bar(
                x,
                value_array,
                bottom=bottom,
                label=labels[idx],
                color=color_list[idx % len(color_list)],
                alpha=chart_style.alpha or self.theme.alpha,
                edgecolor=chart_style.edgecolor or self.theme.edgecolor,
                linewidth=chart_style.edge_linewidth or self.theme.edge_linewidth,
                **kwargs,
            )
            if should_annotate:
                self._annotate_vertical_bars(ax, bars, chart_style, value_fmt or chart_style.value_fmt)
            bottom = bottom + value_array

        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, legend=True, ax=ax)
        return fig, ax

    def histogram(
        self,
        data: ArrayLike,
        *,
        bins: Optional[int] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: str = "频数",
        color: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        density: bool = False,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制直方图。"""
        fig, ax, chart_style = self._ensure_axes("histogram", figsize=figsize)
        values = _normalize_sequence(data)
        hist_kwargs = dict(chart_style.style_kwargs)
        hist_kwargs.setdefault("alpha", chart_style.alpha or 0.75)
        hist_kwargs.setdefault("edgecolor", chart_style.edgecolor or self.theme.edgecolor)
        hist_kwargs.setdefault("linewidth", chart_style.edge_linewidth or self.theme.edge_linewidth)
        hist_kwargs.update(kwargs)

        _, _, patches = ax.hist(
            values,
            bins=bins or chart_style.bins or 20,
            density=density,
            color=color or chart_style.color or self.theme.palette[0],
            **hist_kwargs,
        )
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate
        if should_annotate:
            resolved_fmt = value_fmt or (".3f" if density else chart_style.value_fmt)
            self._annotate_vertical_bars(ax, patches, chart_style, resolved_fmt)
        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, ax=ax)
        return fig, ax

    def hist(self, *args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        """直方图别名。"""
        return self.histogram(*args, **kwargs)

    def pie(
        self,
        labels: Sequence[str],
        sizes: ArrayLike,
        *,
        title: Optional[str] = None,
        colors: Optional[Sequence[str]] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        legend: Optional[bool] = None,
        annotate: Optional[bool] = None,
        value_fmt: Optional[str] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制饼图。"""
        fig, ax, chart_style = self._ensure_axes("pie", figsize=figsize)
        size_values = _normalize_sequence(sizes)
        if len(labels) != len(size_values):
            raise ValueError(f"labels 与 sizes 长度不一致：{len(labels)} != {len(size_values)}")

        pie_kwargs = dict(chart_style.style_kwargs)
        pie_kwargs.setdefault("startangle", chart_style.startangle or 90.0)
        pie_kwargs.update(kwargs)
        should_annotate = bool(chart_style.value_labels) if annotate is None else annotate
        if should_annotate and pie_kwargs.get("autopct") is None:
            pie_kwargs["autopct"] = self._build_pie_autopct(
                size_values.astype(float),
                chart_style,
                value_fmt or chart_style.value_fmt,
            )
        else:
            pie_kwargs.pop("autopct", None)

        pie_result = ax.pie(
            size_values,
            labels=labels,
            colors=list(colors) if colors is not None else self.get_colors(len(labels), palette=self.theme.palette),
            **pie_kwargs,
        )
        if len(pie_result) == 3:
            _, text_objects, autotexts = pie_result
        else:
            _, text_objects = pie_result
            autotexts = []
        for text_object in text_objects:
            text_object.set_fontsize(self.theme.label_fontsize)
        for autotext in autotexts:
            autotext.set_fontsize(chart_style.value_fontsize or self.theme.value_fontsize)
            autotext.set_color(chart_style.value_color or "white")
            autotext.set_fontweight(chart_style.value_fontweight or self.theme.value_fontweight)
            autotext.set_ha("center")
            autotext.set_va("center")
        ax.axis("equal")
        self._setup_axes(ax, chart_style, title=title, grid=False)
        self._finalize(show=show, save_path=save_path, legend=legend, ax=ax)
        return fig, ax

    def box(
        self,
        data: Union[Sequence[ArrayLike], np.ndarray, pd.DataFrame],
        *,
        labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制箱线图。"""
        fig, ax, chart_style = self._ensure_axes("box", figsize=figsize)
        if isinstance(data, pd.DataFrame):
            series_data = [data[col].dropna().to_numpy() for col in data.columns]
            plot_labels = list(data.columns) if labels is None else list(labels)
        else:
            data_array = np.asarray(data, dtype=object)
            if data_array.ndim == 1 and data_array.size > 0 and not isinstance(data_array[0], (list, tuple, np.ndarray, pd.Series)):
                series_data = [data_array.astype(float)]
            elif data_array.ndim == 2:
                series_data = [data_array[:, idx] for idx in range(data_array.shape[1])]
            else:
                series_data = [np.asarray(item, dtype=float) for item in data]
            plot_labels = list(labels) if labels is not None else None

        box_result = ax.boxplot(series_data, labels=plot_labels, patch_artist=True, **kwargs)
        for idx, patch in enumerate(box_result["boxes"]):
            patch.set_facecolor(self.theme.palette[idx % len(self.theme.palette)])
            patch.set_alpha(0.72)

        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, ax=ax)
        return fig, ax

    def violin(
        self,
        data: Union[Sequence[ArrayLike], np.ndarray, pd.DataFrame],
        *,
        labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制小提琴图。"""
        fig, ax, chart_style = self._ensure_axes("violin", figsize=figsize)
        if isinstance(data, pd.DataFrame):
            series_data = [data[col].dropna().to_numpy() for col in data.columns]
            plot_labels = list(data.columns) if labels is None else list(labels)
        else:
            data_array = np.asarray(data, dtype=object)
            if data_array.ndim == 2:
                series_data = [data_array[:, idx] for idx in range(data_array.shape[1])]
            else:
                series_data = [np.asarray(item, dtype=float) for item in data]
            plot_labels = list(labels) if labels is not None else None

        parts = ax.violinplot(series_data, showmeans=True, showextrema=True, **kwargs)
        for idx, body in enumerate(parts["bodies"]):
            body.set_facecolor(self.theme.palette[idx % len(self.theme.palette)])
            body.set_edgecolor("white")
            body.set_alpha(0.72)

        if plot_labels is not None:
            ax.set_xticks(np.arange(1, len(plot_labels) + 1))
            ax.set_xticklabels(plot_labels)

        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, ax=ax)
        return fig, ax

    def heatmap(
        self,
        data: Union[pd.DataFrame, np.ndarray, Sequence[Sequence[Any]]],
        *,
        xticklabels: Optional[Sequence[Any]] = None,
        yticklabels: Optional[Sequence[Any]] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        cmap: Optional[str] = None,
        annot: Optional[bool] = None,
        fmt: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        grid: Optional[bool] = None,
        cbar: bool = True,
        square: bool = False,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制热力图。"""
        fig, ax, chart_style = self._ensure_axes("heatmap", figsize=figsize)
        matrix = _normalize_matrix(data)
        actual_xticklabels = list(xticklabels) if xticklabels is not None else None
        actual_yticklabels = list(yticklabels) if yticklabels is not None else None

        resolved_cmap = cmap or chart_style.cmap or "YlGnBu"
        resolved_annot = chart_style.annot if annot is None else annot
        resolved_fmt = fmt or chart_style.fmt or ".2f"

        if sns is not None:
            sns.heatmap(
                matrix,
                ax=ax,
                cmap=resolved_cmap,
                annot=bool(resolved_annot),
                fmt=resolved_fmt,
                cbar=cbar,
                square=square,
                xticklabels=actual_xticklabels,
                yticklabels=actual_yticklabels,
                **kwargs,
            )
        else:
            image = ax.imshow(matrix, cmap=resolved_cmap, aspect="equal" if square else "auto", **kwargs)
            if cbar:
                fig.colorbar(image, ax=ax)
            if actual_xticklabels is not None:
                ax.set_xticks(np.arange(len(actual_xticklabels)))
                ax.set_xticklabels(actual_xticklabels)
            if actual_yticklabels is not None:
                ax.set_yticks(np.arange(len(actual_yticklabels)))
                ax.set_yticklabels(actual_yticklabels)
            if resolved_annot:
                for row_idx in range(matrix.shape[0]):
                    for col_idx in range(matrix.shape[1]):
                        ax.text(col_idx, row_idx, format(matrix[row_idx, col_idx], resolved_fmt), ha="center", va="center")

        self._setup_axes(ax, chart_style, title=title, xlabel=xlabel, ylabel=ylabel, grid=grid)
        self._finalize(show=show, save_path=save_path, ax=ax)
        return fig, ax

    def corr_heatmap(
        self,
        data: Union[pd.DataFrame, np.ndarray, Sequence[Sequence[Number]]],
        *,
        columns: Optional[Sequence[str]] = None,
        method: str = "pearson",
        title: str = "相关性热力图",
        annot: bool = True,
        fmt: str = ".2f",
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """计算并绘制相关性热力图。"""
        if isinstance(data, pd.DataFrame):
            frame = data.copy()
        else:
            matrix = _normalize_matrix(data)
            frame = pd.DataFrame(matrix, columns=list(columns) if columns is not None else None)

        corr = frame.corr(method=method)
        return self.heatmap(
            corr,
            xticklabels=corr.columns.tolist(),
            yticklabels=corr.index.tolist(),
            title=title,
            annot=annot,
            fmt=fmt,
            show=show,
            save_path=save_path,
            **kwargs,
        )

    def scatter_with_regression(
        self,
        x: ArrayLike,
        y: ArrayLike,
        *,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        scatter_kwargs: Optional[dict[str, Any]] = None,
        line_kwargs: Optional[dict[str, Any]] = None,
    ) -> tuple[Figure, Axes]:
        """绘制散点图并叠加回归线。"""
        fig, ax = self.scatter(
            x,
            y,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=False,
            grid=False,
            **(scatter_kwargs or {}),
        )
        x_values = _normalize_sequence(x).astype(float)
        y_values = _normalize_sequence(y).astype(float)
        coef = np.polyfit(x_values, y_values, deg=1)
        x_line = np.linspace(float(x_values.min()), float(x_values.max()), 200)
        y_line = coef[0] * x_line + coef[1]
        fit_kwargs = {
            "color": self.theme.palette[1],
            "linewidth": self._chart_style("line").linewidth or 2.2,
            "label": "回归线",
        }
        if line_kwargs:
            fit_kwargs.update(line_kwargs)
        ax.plot(x_line, y_line, **fit_kwargs)

        self._finalize(show=show, save_path=save_path, legend=True, ax=ax)
        return fig, ax

    def parallel_coordinates(
        self,
        data: pd.DataFrame,
        class_column: str,
        *,
        title: str = "平行坐标图",
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制平行坐标图。"""
        if class_column not in data.columns:
            raise ValueError(f"DataFrame 中不存在类别列：{class_column}")

        fig, ax, chart_style = self._ensure_axes("line")
        pd.plotting.parallel_coordinates(
            data,
            class_column=class_column,
            ax=ax,
            color=self.theme.palette,
            alpha=chart_style.alpha or 0.7,
            **kwargs,
        )
        self._setup_axes(ax, chart_style, title=title, grid=True)
        self._finalize(show=show, save_path=save_path, legend=True, ax=ax)
        return fig, ax

    def radar(
        self,
        categories: Sequence[str],
        values: Union[ArrayLike, Sequence[ArrayLike]],
        *,
        labels: Optional[Sequence[str]] = None,
        title: str = "雷达图",
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
    ) -> tuple[Figure, Axes]:
        """绘制雷达图。"""
        chart_style = self._chart_style("radar")
        self.close()
        fig = plt.figure(figsize=chart_style.figsize or self.theme.figsize, dpi=self.theme.dpi)
        ax = fig.add_subplot(111, polar=True)
        self.figure_manager.figure = fig
        self.figure_manager.axes = [ax]
        self.figure_manager.axes_array = ax

        value_series = _iter_series(values)
        series_labels = _resolve_labels(labels, len(value_series))

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]

        for idx, series in enumerate(value_series):
            series_array = _normalize_sequence(series).astype(float)
            if len(series_array) != len(categories):
                raise ValueError(f"第 {idx + 1} 组数据长度与 categories 不一致")
            closed_values = np.concatenate([series_array, [series_array[0]]])
            color = self.theme.palette[idx % len(self.theme.palette)]
            ax.plot(angles, closed_values, color=color, linewidth=2.0, label=series_labels[idx])
            ax.fill(angles, closed_values, color=color, alpha=chart_style.alpha or 0.22)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=self.theme.label_fontsize)
        ax.set_title(
            title,
            fontsize=self.theme.title_fontsize,
            fontweight=self.theme.title_fontweight,
            pad=self.theme.title_pad,
        )
        self._finalize(show=show, save_path=save_path, legend=True, ax=ax)
        return fig, ax

    def joint_plot(
        self,
        x: ArrayLike,
        y: ArrayLike,
        *,
        kind: str = "scatter",
        title: str = "联合分布图",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """绘制联合分布图。"""
        x_values = _normalize_sequence(x)
        y_values = _normalize_sequence(y)
        if len(x_values) != len(y_values):
            raise ValueError(f"x 与 y 长度不一致：{len(x_values)} != {len(y_values)}")

        if sns is not None:
            grid = sns.jointplot(x=x_values, y=y_values, kind=kind, color=self.theme.palette[0], **kwargs)
            grid.ax_joint.set_title(
                title,
                fontsize=self.theme.title_fontsize,
                fontweight=self.theme.title_fontweight,
                pad=self.theme.title_pad,
            )
            if xlabel:
                grid.ax_joint.set_xlabel(xlabel, fontsize=self.theme.label_fontsize, labelpad=self.theme.axis_labelpad)
            if ylabel:
                grid.ax_joint.set_ylabel(ylabel, fontsize=self.theme.label_fontsize, labelpad=self.theme.axis_labelpad)
            for sub_ax in (grid.ax_joint, grid.ax_marg_x, grid.ax_marg_y):
                if "top" in sub_ax.spines:
                    sub_ax.spines["top"].set_visible(False)
                if "right" in sub_ax.spines:
                    sub_ax.spines["right"].set_visible(False)
                sub_ax.grid(False)
            grid.ax_joint.tick_params(axis="both", labelsize=self.theme.tick_fontsize)
            self.figure_manager.figure = grid.fig
            self.figure_manager.axes = [grid.ax_joint]
            self.figure_manager.axes_array = grid.ax_joint
            self._finalize(show=show, save_path=save_path, ax=grid.ax_joint)
            return grid.fig, grid.ax_joint

        self.close()
        fig = plt.figure(figsize=self._chart_style("joint_plot").figsize or (9, 9), dpi=self.theme.dpi)
        gs = fig.add_gridspec(4, 4)
        ax_joint = fig.add_subplot(gs[1:4, 0:3])
        ax_top = fig.add_subplot(gs[0, 0:3], sharex=ax_joint)
        ax_right = fig.add_subplot(gs[1:4, 3], sharey=ax_joint)

        ax_joint.scatter(x_values, y_values, color=self.theme.palette[0], alpha=0.75, s=45)
        ax_top.hist(x_values, bins=20, color=self.theme.palette[0], alpha=0.7)
        ax_right.hist(y_values, bins=20, orientation="horizontal", color=self.theme.palette[1], alpha=0.7)
        ax_joint.set_title(
            title,
            fontsize=self.theme.title_fontsize,
            fontweight=self.theme.title_fontweight,
            pad=self.theme.title_pad,
        )
        if xlabel:
            ax_joint.set_xlabel(xlabel, fontsize=self.theme.label_fontsize, labelpad=self.theme.axis_labelpad)
        if ylabel:
            ax_joint.set_ylabel(ylabel, fontsize=self.theme.label_fontsize, labelpad=self.theme.axis_labelpad)
        ax_joint.tick_params(axis="both", labelsize=self.theme.tick_fontsize)
        ax_top.tick_params(axis="x", labelbottom=False)
        ax_right.tick_params(axis="y", labelleft=False)
        for sub_ax in (ax_joint, ax_top, ax_right):
            if "top" in sub_ax.spines:
                sub_ax.spines["top"].set_visible(False)
            if "right" in sub_ax.spines:
                sub_ax.spines["right"].set_visible(False)
            sub_ax.grid(False)

        self.figure_manager.figure = fig
        self.figure_manager.axes = [ax_joint]
        self.figure_manager.axes_array = ax_joint
        self._finalize(show=show, save_path=save_path, ax=ax_joint)
        return fig, ax_joint

    def quick_timeseries(
        self,
        y: Union[ArrayLike, Sequence[ArrayLike], np.ndarray],
        *,
        x: Optional[ArrayLike] = None,
        labels: Optional[Sequence[str]] = None,
        title: str = "时间序列图",
        xlabel: str = "时间",
        ylabel: str = "数值",
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """快速绘制时间序列图。"""
        series_list = _iter_series(y)
        x_values = np.arange(len(series_list[0])) if x is None else _normalize_sequence(x)
        return self.line(
            x=x_values,
            y=series_list,
            labels=labels,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=show,
            save_path=save_path,
            **kwargs,
        )

    def quick_compare_bar(
        self,
        categories: Sequence[str],
        values: ArrayLike,
        *,
        title: str = "对比柱状图",
        xlabel: str = "类别",
        ylabel: str = "数值",
        sort: bool = False,
        horizontal: bool = False,
        annotate: bool = True,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """快速绘制对比柱状图。"""
        value_array = _normalize_sequence(values).astype(float)
        pairs = list(zip(categories, value_array.tolist()))
        if sort:
            pairs.sort(key=lambda item: item[1], reverse=True)
        labels_sorted, values_sorted = zip(*pairs)

        if horizontal:
            fig, ax = self.horizontal_bar(
                y=list(labels_sorted),
                x=np.asarray(values_sorted),
                title=title,
                xlabel=ylabel,
                ylabel=xlabel,
                show=False,
                save_path=None,
                annotate=annotate,
                **kwargs,
            )
        else:
            fig, ax = self.bar(
                x=list(labels_sorted),
                y=np.asarray(values_sorted),
                title=title,
                xlabel=xlabel,
                ylabel=ylabel,
                show=False,
                save_path=None,
                annotate=annotate,
                **kwargs,
            )

        self._finalize(show=show, save_path=save_path, ax=ax)
        return fig, ax

    def quick_grouped_bar(
        self,
        categories: Sequence[str],
        data: Sequence[ArrayLike],
        *,
        labels: Sequence[str],
        title: str = "多组柱状图",
        xlabel: str = "类别",
        ylabel: str = "数值",
        annotate: bool = True,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """快速绘制并排多组柱状图。"""
        return self.grouped_bar(
            x=categories,
            data=data,
            labels=labels,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            annotate=annotate,
            show=show,
            save_path=save_path,
            **kwargs,
        )

    def quick_distribution(
        self,
        data: Union[ArrayLike, Sequence[ArrayLike], np.ndarray, pd.DataFrame],
        *,
        kind: str = "hist",
        labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """快速绘制分布图。"""
        if kind == "hist":
            return self.histogram(
                data,  # type: ignore[arg-type]
                title=title or "分布直方图",
                show=show,
                save_path=save_path,
                **kwargs,
            )
        if kind == "box":
            return self.box(
                data,  # type: ignore[arg-type]
                labels=labels,
                title=title or "分布箱线图",
                show=show,
                save_path=save_path,
                **kwargs,
            )
        if kind == "violin":
            return self.violin(
                data,  # type: ignore[arg-type]
                labels=labels,
                title=title or "分布小提琴图",
                show=show,
                save_path=save_path,
                **kwargs,
            )
        raise ValueError(f"不支持的分布图类型：{kind}")

    def quick_corr_heatmap(
        self,
        data: Union[pd.DataFrame, np.ndarray, Sequence[Sequence[Number]]],
        *,
        columns: Optional[Sequence[str]] = None,
        method: str = "pearson",
        title: str = "相关性热力图",
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """快速绘制相关性热力图。"""
        return self.corr_heatmap(
            data,
            columns=columns,
            method=method,
            title=title,
            show=show,
            save_path=save_path,
            **kwargs,
        )

    def quick_cluster_result(
        self,
        data: Union[np.ndarray, pd.DataFrame, Sequence[Sequence[Number]]],
        labels: ArrayLike,
        *,
        centers: Optional[Union[np.ndarray, Sequence[Sequence[Number]]]] = None,
        feature_indices: tuple[int, int] = (0, 1),
        feature_names: Optional[Sequence[str]] = None,
        title: str = "聚类结果图",
        show: bool = True,
        save_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> tuple[Figure, Axes]:
        """快速绘制二维聚类结果图。"""
        matrix = _normalize_matrix(data)
        label_values = _normalize_sequence(labels)
        if matrix.shape[0] != len(label_values):
            raise ValueError(f"数据样本数与标签数量不一致：{matrix.shape[0]} != {len(label_values)}")

        x_idx, y_idx = feature_indices
        if not (0 <= x_idx < matrix.shape[1] and 0 <= y_idx < matrix.shape[1]):
            raise ValueError("feature_indices 超出特征维度范围")

        xlabel = feature_names[x_idx] if feature_names is not None else f"特征 {x_idx}"
        ylabel = feature_names[y_idx] if feature_names is not None else f"特征 {y_idx}"

        fig, ax = self.scatter(
            x=matrix[:, x_idx],
            y=matrix[:, y_idx],
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show=False,
            grid=False,
            c=label_values,
            cmap=kwargs.pop("cmap", "tab10"),
            **kwargs,
        )

        if centers is not None:
            center_matrix = _normalize_matrix(centers)
            ax.scatter(
                center_matrix[:, x_idx],
                center_matrix[:, y_idx],
                c="red",
                marker="X",
                s=220,
                linewidths=1.2,
                edgecolors="black",
                label="聚类中心",
                zorder=10,
            )

        self._finalize(show=show, save_path=save_path, legend=True, ax=ax)
        return fig, ax

    def __enter__(self) -> "Plotter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()


# === quickplot ===


class QuickPlot:
    """一次性快速出图入口。"""

    @staticmethod
    def _dispatch(method_name: str, *args: Any, theme: Union[str, ThemeConfig] = "report", **kwargs: Any) -> Any:
        plotter = Plotter(theme=theme)
        method = getattr(plotter, method_name)
        return method(*args, **kwargs)

    @staticmethod
    def get_colors(
        count: int,
        *,
        palette: Optional[Sequence[str]] = None,
        start_index: int = 0,
        randomize: bool = False,
        seed: Optional[int] = None,
    ) -> list[str]:
        """按数量快速生成颜色列表。"""
        return Plotter.get_colors(
            count=count,
            palette=palette,
            start_index=start_index,
            randomize=randomize,
            seed=seed,
        )

    @staticmethod
    def line(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("line", *args, **kwargs)

    @staticmethod
    def bar(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("bar", *args, **kwargs)

    @staticmethod
    def grouped_bar(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("grouped_bar", *args, **kwargs)

    @staticmethod
    def scatter(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("scatter", *args, **kwargs)

    @staticmethod
    def heatmap(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("heatmap", *args, **kwargs)

    @staticmethod
    def histogram(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("histogram", *args, **kwargs)

    @staticmethod
    def hist(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("hist", *args, **kwargs)

    @staticmethod
    def pie(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("pie", *args, **kwargs)

    @staticmethod
    def box(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("box", *args, **kwargs)

    @staticmethod
    def corr_heatmap(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("corr_heatmap", *args, **kwargs)

    @staticmethod
    def quick_timeseries(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("quick_timeseries", *args, **kwargs)

    @staticmethod
    def quick_compare_bar(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("quick_compare_bar", *args, **kwargs)

    @staticmethod
    def quick_grouped_bar(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("quick_grouped_bar", *args, **kwargs)

    @staticmethod
    def quick_distribution(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("quick_distribution", *args, **kwargs)

    @staticmethod
    def quick_corr_heatmap(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("quick_corr_heatmap", *args, **kwargs)

    @staticmethod
    def quick_cluster_result(*args: Any, **kwargs: Any) -> tuple[Figure, Axes]:
        return QuickPlot._dispatch("quick_cluster_result", *args, **kwargs)


# === theme registry ===


def _register_default_themes() -> None:
    """注册项目默认主题。"""
    ThemeRegistry.register_theme(
        "report",
        ThemeConfig(
            style="white",
            palette=["#2F5B8A", "#D47F3B", "#4B7F52", "#C04343", "#7A5C99", "#2F8F9D"],
            figsize=(10, 6),
            dpi=150,
            grid=False,
            chart_styles=_build_chart_styles(
                line_color="#2F5B8A",
                bar_color="#D47F3B",
                scatter_color="#2F5B8A",
                heatmap_cmap="YlGnBu",
            ),
        ),
    )
    ThemeRegistry.register_theme(
        "presentation",
        ThemeConfig(
            style="white",
            palette=["#0B6E4F", "#C84C09", "#445E93", "#A61E4D", "#847577", "#E1B000"],
            figsize=(12, 7),
            dpi=180,
            title_fontsize=16,
            label_fontsize=13,
            grid=False,
            chart_styles=_build_chart_styles(
                line_color="#0B6E4F",
                bar_color="#C84C09",
                scatter_color="#445E93",
                heatmap_cmap="BuGn",
            ),
        ),
    )
    ThemeRegistry.register_theme(
        "minimal",
        ThemeConfig(
            style="white",
            palette=["#334E68", "#829AB1", "#9FB3C8", "#BCCCDC", "#486581"],
            figsize=(9, 5.5),
            dpi=150,
            grid=False,
            chart_styles=_build_chart_styles(
                line_color="#334E68",
                bar_color="#486581",
                scatter_color="#334E68",
                heatmap_cmap="Blues",
            ),
        ),
    )
    ThemeRegistry.register_theme(
        "dark",
        ThemeConfig(
            style="dark",
            palette=["#61AFEF", "#E5C07B", "#98C379", "#E06C75", "#C678DD", "#56B6C2"],
            figsize=(10, 6),
            dpi=150,
            grid=False,
            chart_styles=_build_chart_styles(
                line_color="#61AFEF",
                bar_color="#E5C07B",
                scatter_color="#61AFEF",
                heatmap_cmap="magma",
            ),
        ),
    )


_register_default_themes()
StyleManager.setup_chinese()

Matplotlib = Plotter

__all__ = [
    "ArrayLike",
    "ChartStyle",
    "FigureManager",
    "Matplotlib",
    "Number",
    "Plotter",
    "QuickPlot",
    "StyleManager",
    "ThemeConfig",
    "ThemeRegistry",
]
