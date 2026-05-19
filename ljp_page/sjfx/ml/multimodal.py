# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import proxy_module_exports

if TYPE_CHECKING:
    from ljp_page._data_analysis.ml.multimodal import ModalityData as ModalityData
    from ljp_page._data_analysis.ml.multimodal import Multimodal as Multimodal

__getattr__, __all__ = proxy_module_exports(
    "ljp_page._data_analysis.ml.multimodal",
    ["Multimodal", "ModalityData"],
)
