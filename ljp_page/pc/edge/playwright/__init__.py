# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page.pc.edge.playwright.playwright import __all__ as __all__
from ljp_page.pc.edge.playwright.playwright import __getattr__ as __getattr__

if TYPE_CHECKING:
    from ljp_page.pc.edge.playwright.playwright import Playwright as Playwright
    from ljp_page.pc.edge.playwright.playwright import PlaywrightConfig as PlaywrightConfig
    from ljp_page.pc.edge.playwright.playwright import PlaywrightModuleBase as PlaywrightModuleBase
