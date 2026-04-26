#全球进口
from .accessibility_commands import AccessibilityCommands
from .browser_commands import BrowserCommands
from .dom_commands import DomCommands
from .emulation_commands import EmulationCommands
from .fetch_commands import FetchCommands
from .input_commands import InputCommands
from .network_commands import NetworkCommands
from .page_commands import PageCommands
from .runtime_commands import RuntimeCommands
from .storage_commands import StorageCommands
from .target_commands import TargetCommands

__all__ = [
    'AccessibilityCommands',
    'DomCommands',
    'EmulationCommands',
    'FetchCommands',
    'InputCommands',
    'NetworkCommands',
    'PageCommands',
    'RuntimeCommands',
    'StorageCommands',
    'BrowserCommands',
    'TargetCommands',
]
