"""
Core module - window connection and element finding.
"""

from .exceptions import (
    NTWSAutomationError,
    WindowNotFoundError,
    ElementNotFoundError,
    TimeoutError,
    ActionFailedError,
    OCRError,
)
from .window import NTWSWindow
from .element import ElementFinder, Element, ElementSpec, FindStrategy

__all__ = [
    "NTWSAutomationError",
    "WindowNotFoundError",
    "ElementNotFoundError",
    "TimeoutError",
    "ActionFailedError",
    "OCRError",
    "NTWSWindow",
    "ElementFinder",
    "Element",
    "ElementSpec",
    "FindStrategy",
]
