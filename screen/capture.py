"""
Screenshot capture optimized for TWS windows.

Provides efficient screen capture with support for:
- Full screen capture
- Region-based capture
- Window-specific capture
- Element capture
"""

from typing import Tuple, Optional, TYPE_CHECKING
from PIL import Image
import logging

if TYPE_CHECKING:
    from ..core.window import TWSWindow
    from ..core.element import Element
    import numpy as np

logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Screenshot capture with window-specific support.

    Provides multiple capture methods optimized for
    trading application automation.

    Attributes:
        window: TWS window manager instance.
    """

    def __init__(self, window: 'TWSWindow' = None):
        """
        Initialize screen capture.

        Args:
            window: Optional TWS window manager for
                   window-specific captures.
        """
        self.window = window

    def capture_screen(self) -> Image.Image:
        """
        Capture entire screen.

        Returns:
            PIL Image of full screen.
        """
        import pyautogui
        return pyautogui.screenshot()

    def capture_region(
        self,
        region: Tuple[int, int, int, int]
    ) -> Image.Image:
        """
        Capture specific screen region.

        Args:
            region: Tuple (x, y, width, height).

        Returns:
            PIL Image of region.
        """
        import pyautogui

        x, y, width, height = region
        return pyautogui.screenshot(region=(x, y, width, height))

    def capture_window(self, hwnd: int = None) -> Optional[Image.Image]:
        """
        Capture specific window by handle.

        Uses Win32 API for window capture, which works
        even for partially obscured windows.

        Args:
            hwnd: Window handle (uses TWS window if None).

        Returns:
            PIL Image of window, or None on failure.
        """
        if hwnd is None:
            if self.window and self.window.hwnd:
                hwnd = self.window.hwnd
            else:
                logger.warning("No window handle available")
                return None

        try:
            import win32gui
            import win32ui
            import win32con

            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Create device contexts
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # Copy window to bitmap
            save_dc.BitBlt(
                (0, 0), (width, height),
                mfc_dc, (0, 0),
                win32con.SRCCOPY
            )

            # Convert to PIL Image
            bmpinfo = bitmap.GetInfo()
            bmpstr = bitmap.GetBitmapBits(True)

            image = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )

            # Cleanup
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            return image

        except ImportError:
            logger.warning("pywin32 not installed, falling back to region capture")
            if self.window:
                rect = self.window.get_window_rect()
                if rect:
                    left, top, right, bottom = rect
                    return self.capture_region((left, top, right - left, bottom - top))
            return None
        except Exception as e:
            logger.error(f"Window capture failed: {e}")
            return None

    def capture_element(self, element: 'Element') -> Optional[Image.Image]:
        """
        Capture UI element region.

        Args:
            element: Element to capture.

        Returns:
            PIL Image of element, or None if bounds unavailable.
        """
        bounds = element.bounds
        if bounds and bounds[2] > 0 and bounds[3] > 0:
            return self.capture_region(bounds)
        return None

    def capture_tws(self) -> Optional[Image.Image]:
        """
        Capture TWS main window.

        Returns:
            PIL Image of TWS window.
        """
        return self.capture_window()

    def save(self, image: Image.Image, path: str) -> None:
        """
        Save image to file.

        Args:
            image: PIL Image to save.
            path: Output file path.
        """
        image.save(path)
        logger.debug(f"Saved screenshot to {path}")

    def to_numpy(self, image: Image.Image) -> 'np.ndarray':
        """
        Convert PIL Image to numpy array.

        Useful for OpenCV processing.

        Args:
            image: PIL Image.

        Returns:
            Numpy array (BGR format for OpenCV).
        """
        import numpy as np

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to numpy and swap RGB to BGR for OpenCV
        arr = np.array(image)
        return arr[:, :, ::-1].copy()

    def from_numpy(self, array: 'np.ndarray') -> Image.Image:
        """
        Convert numpy array to PIL Image.

        Args:
            array: Numpy array (BGR or RGB format).

        Returns:
            PIL Image.
        """
        import numpy as np

        # Assume BGR, convert to RGB
        if len(array.shape) == 3 and array.shape[2] == 3:
            array = array[:, :, ::-1]

        return Image.fromarray(array)

    def compare_images(
        self,
        image1: Image.Image,
        image2: Image.Image,
        threshold: float = 0.95
    ) -> bool:
        """
        Compare two images for similarity.

        Args:
            image1: First image.
            image2: Second image.
            threshold: Similarity threshold (0-1).

        Returns:
            True if images are similar above threshold.
        """
        import numpy as np

        if image1.size != image2.size:
            return False

        arr1 = np.array(image1)
        arr2 = np.array(image2)

        # Calculate similarity
        diff = np.abs(arr1.astype(float) - arr2.astype(float))
        max_diff = 255.0 * arr1.size
        similarity = 1.0 - (np.sum(diff) / max_diff)

        return similarity >= threshold
