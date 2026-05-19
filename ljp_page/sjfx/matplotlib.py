# 05-19-16-20-00
"""Public matplotlib helper exports."""

from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    from ljp_page._data_analysis.visualization.matplotlib import ArrayLike as ArrayLike
    from ljp_page._data_analysis.visualization.matplotlib import FigureManager as FigureManager
    from ljp_page._data_analysis.visualization.matplotlib import Matplotlib as Matplotlib
    from ljp_page._data_analysis.visualization.matplotlib import Number as Number
    from ljp_page._data_analysis.visualization.matplotlib import Plotter as Plotter
    from ljp_page._data_analysis.visualization.matplotlib import QuickPlot as QuickPlot
    from ljp_page._data_analysis.visualization.matplotlib import StyleManager as StyleManager
    from ljp_page._data_analysis.visualization.matplotlib import ThemeConfig as ThemeConfig
    from ljp_page._data_analysis.visualization.matplotlib import ThemeRegistry as ThemeRegistry

__getattr__, __all__ = proxy_module_exports(
    "ljp_page._data_analysis.visualization.matplotlib",
    [
        "ArrayLike",
        "FigureManager",
        "Matplotlib",
        "Number",
        "Plotter",
        "QuickPlot",
        "StyleManager",
        "ThemeConfig",
        "ThemeRegistry",
    ],
)
