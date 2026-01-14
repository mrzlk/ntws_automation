"""
Input module - keyboard, mouse, and hotkey automation.
"""

from .keyboard import Keyboard
from .mouse import Mouse
from .hotkeys import NTWSHotkeys, NTWSAction, HotkeyBinding

__all__ = [
    "Keyboard",
    "Mouse",
    "NTWSHotkeys",
    "NTWSAction",
    "HotkeyBinding",
]
