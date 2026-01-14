"""
Window management for NTWS automation.

Uses pywinauto with UIA backend for Qt6 application support.
Provides window connection, discovery, and lifecycle management.
"""

from typing import Optional, List, TYPE_CHECKING
from abc import ABC, abstractmethod
import re
import logging

if TYPE_CHECKING:
    from pywinauto.controls.uiawrapper import UIAWrapper
    from pywinauto import Application

logger = logging.getLogger(__name__)


class WindowManager(ABC):
    """
    Abstract base class for window management.

    Allows different implementations:
    - PyWinAuto-based (default)
    - Win32 API direct
    - Custom implementations
    """

    @abstractmethod
    def connect(self) -> bool:
        """Connect to application window."""
        pass

    @abstractmethod
    def find_window(self, title_pattern: str) -> Optional[object]:
        """Find window by title pattern."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if window is ready for interaction."""
        pass

    @abstractmethod
    def bring_to_front(self) -> None:
        """Bring window to foreground."""
        pass


class NTWSWindow(WindowManager):
    """
    NTWS window connection and management.

    Uses pywinauto with UIA (UI Automation) backend for
    Qt6/QML application support.

    Attributes:
        WINDOW_TITLE_PATTERN: Regex pattern to match NTWS window titles.
        PROCESS_NAME: Expected process name.
        timeout: Connection timeout in seconds.
    """

    WINDOW_TITLE_PATTERN = r".*IBKR.*|.*Trader Workstation.*|.*TWS.*|.*Paper Trading.*"
    PROCESS_NAME = "ntws.exe"

    def __init__(self, timeout: int = 30):
        """
        Initialize NTWS window manager.

        Args:
            timeout: Maximum time to wait for window operations.
        """
        self.timeout = timeout
        self._app: Optional['Application'] = None
        self._main_window: Optional['UIAWrapper'] = None
        self._hwnd: Optional[int] = None

    @property
    def app(self) -> Optional['Application']:
        """Get pywinauto Application instance."""
        return self._app

    @property
    def main_window(self) -> Optional['UIAWrapper']:
        """Get main NTWS window wrapper."""
        return self._main_window

    @property
    def hwnd(self) -> Optional[int]:
        """Get window handle (HWND)."""
        return self._hwnd

    def connect(self) -> bool:
        """
        Connect to running NTWS instance.

        Attempts to find and connect to NTWS window using
        title pattern matching.

        Returns:
            True if connection successful, False otherwise.

        Note:
            Requires NTWS to be running and visible.
        """
        try:
            from pywinauto import Application, Desktop

            # Try connecting by window title
            desktop = Desktop(backend='uia')
            windows = desktop.windows()

            for win in windows:
                try:
                    title = win.window_text()
                    if re.match(self.WINDOW_TITLE_PATTERN, title, re.IGNORECASE):
                        self._app = Application(backend='uia').connect(handle=win.handle)
                        self._main_window = win
                        self._hwnd = win.handle
                        logger.info(f"Connected to NTWS window: {title}")
                        return True
                except Exception as e:
                    logger.debug(f"Skipping window: {e}")
                    continue

            logger.warning("NTWS window not found")
            return False

        except ImportError:
            logger.error("pywinauto not installed. Run: pip install pywinauto")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to NTWS: {e}")
            return False

    def find_window(self, title_pattern: str) -> Optional['UIAWrapper']:
        """
        Find window by title regex pattern.

        Args:
            title_pattern: Regex pattern to match window title.

        Returns:
            Window wrapper if found, None otherwise.
        """
        if not self._app:
            return None

        try:
            from pywinauto import Desktop

            desktop = Desktop(backend='uia')
            for win in desktop.windows():
                try:
                    if re.match(title_pattern, win.window_text(), re.IGNORECASE):
                        return win
                except:
                    continue
            return None
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return None

    def get_all_windows(self) -> List['UIAWrapper']:
        """
        Get all NTWS-related windows including dialogs.

        Returns:
            List of window wrappers.
        """
        windows = []
        if not self._app:
            return windows

        try:
            from pywinauto import Desktop

            desktop = Desktop(backend='uia')
            for win in desktop.windows():
                try:
                    title = win.window_text()
                    if re.match(self.WINDOW_TITLE_PATTERN, title, re.IGNORECASE):
                        windows.append(win)
                except:
                    continue
        except Exception as e:
            logger.error(f"Error getting windows: {e}")

        return windows

    def wait_for_window(self, title_pattern: str, timeout: int = None) -> 'UIAWrapper':
        """
        Wait for window to appear.

        Args:
            title_pattern: Regex pattern to match window title.
            timeout: Maximum wait time (uses default if None).

        Returns:
            Window wrapper when found.

        Raises:
            TimeoutError: If window not found within timeout.
        """
        import time
        from .exceptions import TimeoutError

        timeout = timeout or self.timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            window = self.find_window(title_pattern)
            if window:
                return window
            time.sleep(0.5)

        raise TimeoutError(f"Window matching '{title_pattern}'", timeout)

    def is_ready(self) -> bool:
        """
        Check if NTWS is ready for interaction.

        Verifies:
        - Window exists
        - Window is visible
        - Window is enabled

        Returns:
            True if ready, False otherwise.
        """
        if not self._main_window:
            return False

        try:
            return (
                self._main_window.is_visible() and
                self._main_window.is_enabled()
            )
        except:
            return False

    def bring_to_front(self) -> None:
        """
        Bring NTWS main window to foreground.

        Makes NTWS the active window and ensures
        it's visible for automation.
        """
        if self._main_window:
            try:
                self._main_window.set_focus()
            except Exception as e:
                logger.warning(f"Could not bring window to front: {e}")

    def get_window_rect(self) -> Optional[tuple]:
        """
        Get window bounding rectangle.

        Returns:
            Tuple (left, top, right, bottom) or None if unavailable.
        """
        if not self._main_window:
            return None

        try:
            rect = self._main_window.rectangle()
            return (rect.left, rect.top, rect.right, rect.bottom)
        except:
            return None

    def minimize(self) -> None:
        """Minimize NTWS window."""
        if self._main_window:
            try:
                self._main_window.minimize()
            except Exception as e:
                logger.warning(f"Could not minimize window: {e}")

    def restore(self) -> None:
        """Restore NTWS window from minimized state."""
        if self._main_window:
            try:
                self._main_window.restore()
            except Exception as e:
                logger.warning(f"Could not restore window: {e}")
