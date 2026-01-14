"""
OCR module using EasyOCR with fallback options.

Optimized for trading application text recognition:
- Prices, quantities, percentages
- Stock symbols
- Table data extraction
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, TYPE_CHECKING
from abc import ABC, abstractmethod
import re
import logging

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """
    OCR detection result.

    Attributes:
        text: Recognized text.
        confidence: Recognition confidence (0-1).
        bbox: Bounding box (x, y, width, height).
    """
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]

    @property
    def center(self) -> Tuple[int, int]:
        """Get center point of detected text."""
        x, y, w, h = self.bbox
        return (x + w // 2, y + h // 2)


class OCRBackend(ABC):
    """Abstract OCR backend interface."""

    @abstractmethod
    def read(self, image: 'Image') -> List[OCRResult]:
        """Read all text from image."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass


class EasyOCRBackend(OCRBackend):
    """EasyOCR backend implementation."""

    def __init__(self, languages: List[str], use_gpu: bool):
        self.languages = languages
        self.use_gpu = use_gpu
        self._reader = None

    @property
    def reader(self):
        """Lazy initialization of EasyOCR reader."""
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(
                self.languages,
                gpu=self.use_gpu
            )
        return self._reader

    def read(self, image: 'Image') -> List[OCRResult]:
        import numpy as np

        # Convert PIL to numpy
        img_array = np.array(image)

        results = []
        detections = self.reader.readtext(img_array)

        for detection in detections:
            bbox_points, text, confidence = detection

            # Convert polygon to bounding box
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            x = int(min(x_coords))
            y = int(min(y_coords))
            w = int(max(x_coords) - x)
            h = int(max(y_coords) - y)

            results.append(OCRResult(
                text=text,
                confidence=confidence,
                bbox=(x, y, w, h)
            ))

        return results

    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False


class TesseractBackend(OCRBackend):
    """Tesseract OCR backend implementation."""

    def read(self, image: 'Image') -> List[OCRResult]:
        import pytesseract

        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        results = []
        for i, text in enumerate(data['text']):
            if text.strip():
                conf = float(data['conf'][i])
                if conf > 0:
                    results.append(OCRResult(
                        text=text,
                        confidence=conf / 100.0,
                        bbox=(
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        )
                    ))

        return results

    def is_available(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            return False


class OCREngine:
    """
    OCR engine optimized for trading applications.

    Uses EasyOCR as primary backend with Tesseract fallback.
    Provides specialized methods for reading financial data.

    Attributes:
        languages: Supported languages.
        confidence_threshold: Minimum confidence for results.
    """

    # Patterns for financial data
    PRICE_PATTERN = re.compile(r'\d+\.?\d*')
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}$')
    PERCENT_PATTERN = re.compile(r'[+-]?\d+\.?\d*%')
    QUANTITY_PATTERN = re.compile(r'^\d+$')

    def __init__(
        self,
        languages: List[str] = None,
        use_gpu: bool = True,
        confidence_threshold: float = 0.5,
        backend: str = 'easyocr'
    ):
        """
        Initialize OCR engine.

        Args:
            languages: Languages to recognize (default: ['en']).
            use_gpu: Use GPU acceleration if available.
            confidence_threshold: Minimum confidence threshold.
            backend: OCR backend ('easyocr' or 'tesseract').
        """
        self.languages = languages or ['en']
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold

        # Initialize backend
        if backend == 'easyocr':
            self._backend = EasyOCRBackend(self.languages, use_gpu)
        else:
            self._backend = TesseractBackend()

        # Fallback backend
        self._fallback = TesseractBackend() if backend == 'easyocr' else None

    def read_text(
        self,
        image: 'Image',
        detail: bool = True
    ) -> List[OCRResult]:
        """
        Extract all text from image.

        Args:
            image: PIL Image to process.
            detail: If True, return OCRResult with positions.
                   If False, return just text strings.

        Returns:
            List of OCRResult objects.
        """
        try:
            results = self._backend.read(image)
        except Exception as e:
            logger.warning(f"Primary OCR failed: {e}")
            if self._fallback and self._fallback.is_available():
                results = self._fallback.read(image)
            else:
                return []

        # Filter by confidence
        results = [r for r in results if r.confidence >= self.confidence_threshold]

        return results

    def read_region(
        self,
        image: 'Image',
        region: Tuple[int, int, int, int]
    ) -> List[OCRResult]:
        """
        Extract text from specific image region.

        Args:
            image: PIL Image.
            region: Region (x, y, width, height).

        Returns:
            List of OCRResult objects.
        """
        x, y, w, h = region
        cropped = image.crop((x, y, x + w, y + h))
        results = self.read_text(cropped)

        # Adjust coordinates to original image
        for result in results:
            bx, by, bw, bh = result.bbox
            result.bbox = (bx + x, by + y, bw, bh)

        return results

    def find_text(
        self,
        image: 'Image',
        pattern: str,
        regex: bool = False
    ) -> Optional[OCRResult]:
        """
        Find specific text in image.

        Args:
            image: PIL Image.
            pattern: Text or regex pattern to find.
            regex: Treat pattern as regex.

        Returns:
            First matching OCRResult, or None.
        """
        results = self.read_text(image)

        for result in results:
            if regex:
                if re.search(pattern, result.text, re.IGNORECASE):
                    return result
            else:
                if pattern.lower() in result.text.lower():
                    return result

        return None

    def find_all_text(
        self,
        image: 'Image',
        pattern: str,
        regex: bool = False
    ) -> List[OCRResult]:
        """
        Find all matching text in image.

        Args:
            image: PIL Image.
            pattern: Text or regex pattern.
            regex: Treat pattern as regex.

        Returns:
            List of matching OCRResult objects.
        """
        results = self.read_text(image)
        matches = []

        for result in results:
            if regex:
                if re.search(pattern, result.text, re.IGNORECASE):
                    matches.append(result)
            else:
                if pattern.lower() in result.text.lower():
                    matches.append(result)

        return matches

    def read_price(
        self,
        image: 'Image',
        region: Tuple[int, int, int, int] = None
    ) -> Optional[float]:
        """
        Extract price value from image.

        Args:
            image: PIL Image.
            region: Optional region to search.

        Returns:
            Price as float, or None.
        """
        if region:
            results = self.read_region(image, region)
        else:
            results = self.read_text(image)

        for result in results:
            match = self.PRICE_PATTERN.search(result.text)
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    continue

        return None

    def read_symbol(
        self,
        image: 'Image',
        region: Tuple[int, int, int, int] = None
    ) -> Optional[str]:
        """
        Extract stock symbol from image.

        Args:
            image: PIL Image.
            region: Optional region to search.

        Returns:
            Symbol string, or None.
        """
        if region:
            results = self.read_region(image, region)
        else:
            results = self.read_text(image)

        for result in results:
            text = result.text.strip().upper()
            if self.SYMBOL_PATTERN.match(text):
                return text

        return None

    def read_table(
        self,
        image: 'Image',
        columns: List[str] = None
    ) -> List[Dict]:
        """
        Extract tabular data from image.

        Args:
            image: PIL Image containing table.
            columns: Expected column names.

        Returns:
            List of row dictionaries.
        """
        results = self.read_text(image)

        if not results:
            return []

        # Sort by Y coordinate to group rows
        results.sort(key=lambda r: r.bbox[1])

        rows = []
        current_row = []
        last_y = -1
        row_threshold = 20  # Pixels

        for result in results:
            y = result.bbox[1]
            if last_y < 0 or abs(y - last_y) < row_threshold:
                current_row.append(result)
            else:
                if current_row:
                    # Sort row by X coordinate
                    current_row.sort(key=lambda r: r.bbox[0])
                    rows.append([r.text for r in current_row])
                current_row = [result]
            last_y = y

        if current_row:
            current_row.sort(key=lambda r: r.bbox[0])
            rows.append([r.text for r in current_row])

        # Convert to dictionaries if columns provided
        if columns and rows:
            header = rows[0] if not columns else columns
            return [
                dict(zip(header, row))
                for row in rows[1:] if len(row) == len(header)
            ]

        return [{'values': row} for row in rows]
