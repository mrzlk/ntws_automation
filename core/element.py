"""
Element finding and interaction for Qt6/QML controls.

Provides multiple strategies for finding UI elements:
- UI Automation tree (for accessible elements)
- OCR text search (for custom QML elements)
- Image template matching (fallback)
- Fixed position (last resort)

Strategies can be combined for maximum reliability.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable, Any, TYPE_CHECKING
from enum import Enum
from abc import ABC, abstractmethod
import logging

if TYPE_CHECKING:
    from .window import NTWSWindow
    from pywinauto.controls.uiawrapper import UIAWrapper

logger = logging.getLogger(__name__)


class FindStrategy(Enum):
    """
    Element finding strategy.

    Different strategies have different trade-offs:
    - UIA: Fast, reliable for accessible elements
    - OCR: Works for any visible text, slower
    - IMAGE: Template matching, resolution-dependent
    - POSITION: Fixed coordinates, fragile
    - HYBRID: Combines multiple strategies
    """
    UIA = "uia"
    OCR = "ocr"
    IMAGE = "image"
    POSITION = "position"
    HYBRID = "hybrid"


@dataclass
class ElementSpec:
    """
    Specification for finding an element.

    Defines search criteria that can be used by
    different finding strategies.

    Attributes:
        name: Element name (accessibility name).
        automation_id: UI Automation ID.
        control_type: Control type (Button, Edit, etc.).
        class_name: Window class name.
        text_pattern: Text to find via OCR.
        image_template: Path to template image.
        region: Screen region to search (x, y, width, height).
        strategy: Preferred finding strategy.
        timeout: Search timeout in seconds.
    """
    name: Optional[str] = None
    automation_id: Optional[str] = None
    control_type: Optional[str] = None
    class_name: Optional[str] = None
    text_pattern: Optional[str] = None
    image_template: Optional[str] = None
    region: Optional[Tuple[int, int, int, int]] = None
    strategy: FindStrategy = FindStrategy.UIA
    timeout: int = 10

    def __str__(self) -> str:
        parts = []
        if self.name:
            parts.append(f"name='{self.name}'")
        if self.automation_id:
            parts.append(f"id='{self.automation_id}'")
        if self.control_type:
            parts.append(f"type='{self.control_type}'")
        if self.text_pattern:
            parts.append(f"text='{self.text_pattern}'")
        return f"ElementSpec({', '.join(parts)})"


class Element:
    """
    Wrapper for UI element with unified interface.

    Abstracts the underlying element representation
    (UIA wrapper, OCR result, etc.) providing consistent
    interaction methods.

    Attributes:
        bounds: Element bounding rectangle.
        center: Element center point.
        text: Element text content.
    """

    def __init__(
        self,
        uia_element: Optional['UIAWrapper'] = None,
        rect: Optional[Tuple[int, int, int, int]] = None,
        text: Optional[str] = None
    ):
        """
        Initialize element wrapper.

        Args:
            uia_element: PyWinAuto UIA element wrapper.
            rect: Bounding rectangle (x, y, width, height).
            text: Element text (from OCR or accessibility).
        """
        self._uia = uia_element
        self._rect = rect
        self._text = text

    @property
    def text(self) -> str:
        """Get element text content."""
        if self._text:
            return self._text
        if self._uia:
            try:
                return self._uia.window_text()
            except:
                pass
        return ""

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """
        Get element bounding rectangle.

        Returns:
            Tuple (x, y, width, height).
        """
        if self._rect:
            return self._rect
        if self._uia:
            try:
                r = self._uia.rectangle()
                return (r.left, r.top, r.width(), r.height())
            except:
                pass
        return (0, 0, 0, 0)

    @property
    def center(self) -> Tuple[int, int]:
        """Get element center point."""
        x, y, w, h = self.bounds
        return (x + w // 2, y + h // 2)

    @property
    def is_enabled(self) -> bool:
        """Check if element is enabled."""
        if self._uia:
            try:
                return self._uia.is_enabled()
            except:
                pass
        return True

    @property
    def is_visible(self) -> bool:
        """Check if element is visible."""
        if self._uia:
            try:
                return self._uia.is_visible()
            except:
                pass
        return True

    def click(self) -> None:
        """
        Click element.

        Uses UIA click if available, falls back to
        coordinate-based click.
        """
        if self._uia:
            try:
                self._uia.click_input()
                return
            except:
                pass

        # Fallback to mouse click at center
        import pyautogui
        x, y = self.center
        pyautogui.click(x, y)

    def double_click(self) -> None:
        """Double-click element."""
        if self._uia:
            try:
                self._uia.double_click_input()
                return
            except:
                pass

        import pyautogui
        x, y = self.center
        pyautogui.doubleClick(x, y)

    def right_click(self) -> None:
        """Right-click element."""
        if self._uia:
            try:
                self._uia.right_click_input()
                return
            except:
                pass

        import pyautogui
        x, y = self.center
        pyautogui.rightClick(x, y)

    def type_text(self, text: str, clear_first: bool = True) -> None:
        """
        Type text into element.

        Args:
            text: Text to type.
            clear_first: Clear existing text before typing.
        """
        self.click()  # Focus element

        if clear_first:
            import pyautogui
            pyautogui.hotkey('ctrl', 'a')

        if self._uia:
            try:
                self._uia.type_keys(text, with_spaces=True)
                return
            except:
                pass

        import pyautogui
        pyautogui.typewrite(text, interval=0.02)

    def get_value(self) -> str:
        """
        Get element value (for inputs, etc.).

        Returns:
            Element value or text.
        """
        if self._uia:
            try:
                # Try value pattern first
                value = self._uia.legacy_properties().get('Value', '')
                if value:
                    return value
            except:
                pass
        return self.text


class ElementFinder:
    """
    Multi-strategy element finder.

    Combines multiple finding strategies to locate
    UI elements reliably in Qt6/QML applications.

    Supports:
    - Caching of found elements
    - Automatic strategy fallback
    - Configurable timeouts
    """

    def __init__(self, window: 'NTWSWindow'):
        """
        Initialize element finder.

        Args:
            window: NTWS window manager instance.
        """
        self.window = window
        self._cache: dict = {}
        self._strategies: dict = {}
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """Register default finding strategies."""
        self._strategies[FindStrategy.UIA] = self._find_by_uia
        self._strategies[FindStrategy.POSITION] = self._find_by_position

    def register_strategy(
        self,
        strategy: FindStrategy,
        finder: Callable[[ElementSpec], Optional[Element]]
    ) -> None:
        """
        Register custom finding strategy.

        Args:
            strategy: Strategy enum value.
            finder: Callable that returns Element or None.
        """
        self._strategies[strategy] = finder

    def find(
        self,
        spec: ElementSpec,
        timeout: int = None,
        use_cache: bool = True
    ) -> Optional[Element]:
        """
        Find element using specified strategy.

        Args:
            spec: Element specification.
            timeout: Search timeout (uses spec.timeout if None).
            use_cache: Use cached element if available.

        Returns:
            Element if found, None otherwise.
        """
        cache_key = str(spec)

        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached.is_visible:
                return cached

        strategy_fn = self._strategies.get(spec.strategy)
        if not strategy_fn:
            logger.warning(f"Unknown strategy: {spec.strategy}")
            return None

        element = strategy_fn(spec)

        if element and use_cache:
            self._cache[cache_key] = element

        return element

    def find_all(self, spec: ElementSpec) -> List[Element]:
        """
        Find all matching elements.

        Args:
            spec: Element specification.

        Returns:
            List of matching elements.
        """
        elements = []

        if spec.strategy == FindStrategy.UIA and self.window.main_window:
            try:
                criteria = {}
                if spec.name:
                    criteria['title'] = spec.name
                if spec.control_type:
                    criteria['control_type'] = spec.control_type
                if spec.automation_id:
                    criteria['auto_id'] = spec.automation_id

                if criteria:
                    children = self.window.main_window.descendants(**criteria)
                    elements = [Element(uia_element=child) for child in children]
            except Exception as e:
                logger.debug(f"find_all error: {e}")

        return elements

    def wait_for(
        self,
        spec: ElementSpec,
        timeout: int = None
    ) -> Element:
        """
        Wait for element to appear.

        Args:
            spec: Element specification.
            timeout: Maximum wait time.

        Returns:
            Element when found.

        Raises:
            TimeoutError: If element not found within timeout.
        """
        import time
        from .exceptions import TimeoutError, ElementNotFoundError

        timeout = timeout or spec.timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            element = self.find(spec, use_cache=False)
            if element:
                return element
            time.sleep(0.5)

        raise TimeoutError(f"Element {spec}", timeout)

    def exists(self, spec: ElementSpec) -> bool:
        """
        Check if element exists without waiting.

        Args:
            spec: Element specification.

        Returns:
            True if element exists, False otherwise.
        """
        return self.find(spec, timeout=1, use_cache=False) is not None

    def clear_cache(self) -> None:
        """Clear element cache."""
        self._cache.clear()

    def _find_by_uia(self, spec: ElementSpec) -> Optional[Element]:
        """Find element using UI Automation."""
        if not self.window.main_window:
            return None

        try:
            criteria = {}
            if spec.name:
                criteria['title'] = spec.name
            if spec.control_type:
                criteria['control_type'] = spec.control_type
            if spec.automation_id:
                criteria['auto_id'] = spec.automation_id
            if spec.class_name:
                criteria['class_name'] = spec.class_name

            if not criteria:
                return None

            child = self.window.main_window.child_window(**criteria)
            if child.exists():
                return Element(uia_element=child)

        except Exception as e:
            logger.debug(f"UIA find error: {e}")

        return None

    def _find_by_position(self, spec: ElementSpec) -> Optional[Element]:
        """Find element by fixed position."""
        if spec.region:
            x, y, w, h = spec.region
            return Element(rect=(x, y, w, h))
        return None
