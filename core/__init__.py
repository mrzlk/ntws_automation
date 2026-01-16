"""
Core module - window connection and element finding.
"""

from .exceptions import (
    TWSAutomationError,
    WindowNotFoundError,
    ElementNotFoundError,
    TimeoutError,
    ActionFailedError,
    OCRError,
)
from .window import TWSWindow
from .element import ElementFinder, Element, ElementSpec, FindStrategy

__all__ = [
    "TWSAutomationError",
    "WindowNotFoundError",
    "ElementNotFoundError",
    "TimeoutError",
    "ActionFailedError",
    "OCRError",
    "TWSWindow",
    "ElementFinder",
    "Element",
    "ElementSpec",
    "FindStrategy",
]
