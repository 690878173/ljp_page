"""Novel collection framework."""

from .pipeline import NovelPipeline
from .transport import BrowserHttpConfig, BrowserHttpTransport, ImageStore
from .xs import Xs, XsManager

__all__ = [
    "BrowserHttpConfig", "BrowserHttpTransport", "ImageStore",
    "NovelPipeline", "Xs", "XsManager",
]
