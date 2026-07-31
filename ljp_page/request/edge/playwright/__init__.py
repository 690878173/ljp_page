# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page.request.edge.playwright.playwright import __all__ as __all__
from ljp_page.request.edge.playwright.playwright import __getattr__ as __getattr__

if TYPE_CHECKING:
    from ljp_page.request.edge.playwright.playwright import *
