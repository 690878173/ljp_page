# 05-19-16-20-00
from typing import TYPE_CHECKING

from ljp_page._core._lazy_import import bind_lazy_exports

if TYPE_CHECKING:
    from .accessibility_commands import *  # noqa: F403
    from .browser_commands import *  # noqa: F403
    from .dom_commands import *  # noqa: F403
    from .emulation_commands import *  # noqa: F403
    from .fetch_commands import *  # noqa: F403
    from .input_commands import *  # noqa: F403
    from .network_commands import *  # noqa: F403
    from .page_commands import *  # noqa: F403
    from .runtime_commands import *  # noqa: F403
    from .storage_commands import *  # noqa: F403
    from .target_commands import *  # noqa: F403

__getattr__, __all__ = bind_lazy_exports(__name__, __file__)
