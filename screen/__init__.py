"""
Screen module - capture, OCR, and region management.
"""

from .capture import ScreenCapture
from .ocr import OCREngine, OCRResult
from .regions import Region, RegionManager

__all__ = [
    "ScreenCapture",
    "OCREngine",
    "OCRResult",
    "Region",
    "RegionManager",
]
