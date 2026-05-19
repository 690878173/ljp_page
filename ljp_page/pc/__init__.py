# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page.pc.pc import __all__ as __all__
from ljp_page.pc.pc import __getattr__ as __getattr__

if TYPE_CHECKING:
    from ljp_page.pc.pc import BaseManage as BaseManage
    from ljp_page.pc.pc import BasePc as BasePc
    from ljp_page.pc.pc import Config as Config
    from ljp_page.pc.pc import Mode as Mode
    from ljp_page.pc.pc import ModeType as ModeType
    from ljp_page.pc.pc import P1Item as P1Item
    from ljp_page.pc.pc import P1Result as P1Result
    from ljp_page.pc.pc import P2Item as P2Item
    from ljp_page.pc.pc import P2Result as P2Result
    from ljp_page.pc.pc import P3Item as P3Item
    from ljp_page.pc.pc import PcConfig as PcConfig
    from ljp_page.pc.pc import Xs as Xs
    from ljp_page.pc.pc import XsManager as XsManager
    from ljp_page.pc.pc import Ys as Ys
    from ljp_page.pc.pc import YsConfig as YsConfig
