"""
Mouse automation with precise control and safety features.

Provides mouse control for TWS automation with:
- Smooth movement
- Click variations
- Scroll support
- Fail-safe mechanisms
"""

from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Mouse:
    """
    Mouse automation with safety features.

    Implements PyAutoGUI-based mouse control with
    additional safety mechanisms for trading applications.

    Attributes:
        move_duration: Default duration for mouse movements.
        click_delay: Delay after clicks.
        fail_safe: Enable corner fail-safe.
    """

    def __init__(
        self,
        move_duration: float = 0.1,
        click_delay: float = 0.05,
        fail_safe: bool = True
    ):
        """
        Initialize mouse automation.

        Args:
            move_duration: Default movement animation duration.
            click_delay: Pause after each click.
            fail_safe: If True, moving to screen corner aborts.
        """
        import pyautogui

        self.move_duration = move_duration
        self.click_delay = click_delay

        pyautogui.FAILSAFE = fail_safe
        pyautogui.PAUSE = click_delay

    @property
    def position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        import pyautogui
        return pyautogui.position()

    @property
    def screen_size(self) -> Tuple[int, int]:
        """Get screen size (width, height)."""
        import pyautogui
        return pyautogui.size()

    def move_to(
        self,
        x: int,
        y: int,
        duration: float = None
    ) -> None:
        """
        Move mouse to absolute position.

        Args:
            x: Target X coordinate.
            y: Target Y coordinate.
            duration: Movement duration (uses default if None).
        """
        import pyautogui

        duration = duration if duration is not None else self.move_duration
        pyautogui.moveTo(x, y, duration=duration)

    def move_relative(self, dx: int, dy: int) -> None:
        """
        Move mouse relative to current position.

        Args:
            dx: Horizontal offset.
            dy: Vertical offset.
        """
        import pyautogui
        pyautogui.moveRel(dx, dy, duration=self.move_duration)

    def click(
        self,
        x: int = None,
        y: int = None,
        button: str = 'left',
        clicks: int = 1
    ) -> None:
        """
        Click at position.

        Args:
            x: X coordinate (current position if None).
            y: Y coordinate (current position if None).
            button: 'left', 'right', or 'middle'.
            clicks: Number of clicks.
        """
        import pyautogui

        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)
        else:
            pyautogui.click(clicks=clicks, button=button)

    def double_click(self, x: int = None, y: int = None) -> None:
        """
        Double-click at position.

        Args:
            x: X coordinate (current position if None).
            y: Y coordinate (current position if None).
        """
        import pyautogui

        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()

    def right_click(self, x: int = None, y: int = None) -> None:
        """
        Right-click at position.

        Args:
            x: X coordinate (current position if None).
            y: Y coordinate (current position if None).
        """
        import pyautogui

        if x is not None and y is not None:
            pyautogui.rightClick(x, y)
        else:
            pyautogui.rightClick()

    def triple_click(self, x: int = None, y: int = None) -> None:
        """
        Triple-click at position (select line/paragraph).

        Args:
            x: X coordinate.
            y: Y coordinate.
        """
        self.click(x, y, clicks=3)

    def drag_to(
        self,
        x: int,
        y: int,
        duration: float = 0.5,
        button: str = 'left'
    ) -> None:
        """
        Drag from current position to target.

        Args:
            x: Target X coordinate.
            y: Target Y coordinate.
            duration: Drag duration.
            button: Mouse button to use.
        """
        import pyautogui
        pyautogui.drag(
            x - self.position[0],
            y - self.position[1],
            duration=duration,
            button=button
        )

    def drag_relative(
        self,
        dx: int,
        dy: int,
        duration: float = 0.5,
        button: str = 'left'
    ) -> None:
        """
        Drag relative to current position.

        Args:
            dx: Horizontal offset.
            dy: Vertical offset.
            duration: Drag duration.
            button: Mouse button.
        """
        import pyautogui
        pyautogui.drag(dx, dy, duration=duration, button=button)

    def scroll(
        self,
        clicks: int,
        x: int = None,
        y: int = None
    ) -> None:
        """
        Scroll wheel at position.

        Args:
            clicks: Scroll amount (positive=up, negative=down).
            x: X coordinate (current position if None).
            y: Y coordinate (current position if None).
        """
        import pyautogui

        if x is not None and y is not None:
            pyautogui.scroll(clicks, x, y)
        else:
            pyautogui.scroll(clicks)

    def scroll_horizontal(
        self,
        clicks: int,
        x: int = None,
        y: int = None
    ) -> None:
        """
        Horizontal scroll at position.

        Args:
            clicks: Scroll amount (positive=right, negative=left).
            x: X coordinate.
            y: Y coordinate.
        """
        import pyautogui

        if x is not None and y is not None:
            pyautogui.hscroll(clicks, x, y)
        else:
            pyautogui.hscroll(clicks)

    def mouse_down(self, button: str = 'left') -> None:
        """
        Press and hold mouse button.

        Args:
            button: Button to press ('left', 'right', 'middle').
        """
        import pyautogui
        pyautogui.mouseDown(button=button)

    def mouse_up(self, button: str = 'left') -> None:
        """
        Release mouse button.

        Args:
            button: Button to release.
        """
        import pyautogui
        pyautogui.mouseUp(button=button)

    def locate_on_screen(
        self,
        image_path: str,
        confidence: float = 0.9
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Locate image on screen.

        Args:
            image_path: Path to template image.
            confidence: Match confidence threshold.

        Returns:
            Bounding box (x, y, width, height) or None.
        """
        import pyautogui

        try:
            location = pyautogui.locateOnScreen(
                image_path,
                confidence=confidence
            )
            if location:
                return (location.left, location.top, location.width, location.height)
        except Exception as e:
            logger.debug(f"Image not found: {e}")

        return None

    def click_image(
        self,
        image_path: str,
        confidence: float = 0.9
    ) -> bool:
        """
        Find and click on image.

        Args:
            image_path: Path to template image.
            confidence: Match confidence threshold.

        Returns:
            True if image found and clicked.
        """
        location = self.locate_on_screen(image_path, confidence)
        if location:
            x, y, w, h = location
            self.click(x + w // 2, y + h // 2)
            return True
        return False
