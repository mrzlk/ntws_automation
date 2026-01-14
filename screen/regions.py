"""
Screen region definitions for NTWS UI elements.

Supports multiple resolutions with automatic scaling.
Regions are defined relative to NTWS window position.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, TYPE_CHECKING
import json
import logging

if TYPE_CHECKING:
    from ..core.window import NTWSWindow

logger = logging.getLogger(__name__)


@dataclass
class Region:
    """
    Screen region definition.

    Represents a rectangular area of the screen,
    typically containing a UI element or group.

    Attributes:
        name: Unique region identifier.
        x: Left coordinate.
        y: Top coordinate.
        width: Region width.
        height: Region height.
        description: Human-readable description.
    """
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Get bounds tuple (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    @property
    def center(self) -> Tuple[int, int]:
        """Get center point."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def right(self) -> int:
        """Get right edge X coordinate."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Get bottom edge Y coordinate."""
        return self.y + self.height

    def scale(self, factor: float) -> 'Region':
        """
        Scale region by factor.

        Args:
            factor: Scale multiplier.

        Returns:
            New scaled Region.
        """
        return Region(
            name=self.name,
            x=int(self.x * factor),
            y=int(self.y * factor),
            width=int(self.width * factor),
            height=int(self.height * factor),
            description=self.description
        )

    def offset(self, dx: int, dy: int) -> 'Region':
        """
        Create offset region.

        Args:
            dx: Horizontal offset.
            dy: Vertical offset.

        Returns:
            New offset Region.
        """
        return Region(
            name=self.name,
            x=self.x + dx,
            y=self.y + dy,
            width=self.width,
            height=self.height,
            description=self.description
        )

    def contains(self, x: int, y: int) -> bool:
        """Check if point is inside region."""
        return (
            self.x <= x < self.x + self.width and
            self.y <= y < self.y + self.height
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Region':
        """Create from dictionary."""
        return cls(**data)


class RegionManager:
    """
    Manages screen regions with resolution awareness.

    Regions are relative to NTWS main window.
    Supports automatic scaling for different resolutions.

    Attributes:
        BASE_RESOLUTION: Reference resolution for region definitions.
        PREDEFINED_REGIONS: Default region definitions.
    """

    BASE_RESOLUTION = (1920, 1080)

    # Predefined regions (relative to window, may need calibration)
    PREDEFINED_REGIONS = {
        'symbol_input': Region(
            'symbol_input', 100, 50, 200, 30,
            'Symbol search input field'
        ),
        'price_display': Region(
            'price_display', 400, 100, 150, 40,
            'Current price display'
        ),
        'bid_price': Region(
            'bid_price', 350, 150, 100, 30,
            'Bid price'
        ),
        'ask_price': Region(
            'ask_price', 450, 150, 100, 30,
            'Ask price'
        ),
        'order_quantity': Region(
            'order_quantity', 100, 200, 100, 30,
            'Order quantity input'
        ),
        'order_price': Region(
            'order_price', 220, 200, 100, 30,
            'Order price input'
        ),
        'order_side': Region(
            'order_side', 340, 200, 100, 30,
            'Order side (buy/sell)'
        ),
        'transmit_button': Region(
            'transmit_button', 500, 200, 80, 30,
            'Order transmit button'
        ),
        'portfolio_table': Region(
            'portfolio_table', 0, 300, 1920, 500,
            'Portfolio positions table'
        ),
        'order_list': Region(
            'order_list', 0, 300, 1920, 300,
            'Pending orders list'
        ),
        'status_bar': Region(
            'status_bar', 0, 1050, 1920, 30,
            'Status bar'
        ),
    }

    def __init__(
        self,
        window: 'NTWSWindow' = None,
        config_path: str = None
    ):
        """
        Initialize region manager.

        Args:
            window: NTWS window manager for position offset.
            config_path: Path to custom region config file.
        """
        self.window = window
        self.scale_factor = 1.0
        self.window_offset = (0, 0)

        # Copy predefined regions
        self.regions: Dict[str, Region] = dict(self.PREDEFINED_REGIONS)

        if config_path:
            self.load_config(config_path)

    def get(self, name: str, absolute: bool = True) -> Optional[Region]:
        """
        Get region by name.

        Args:
            name: Region name.
            absolute: If True, add window offset for absolute coords.

        Returns:
            Region with scaled/offset coordinates, or None.
        """
        region = self.regions.get(name)
        if not region:
            return None

        # Apply scale
        if self.scale_factor != 1.0:
            region = region.scale(self.scale_factor)

        # Apply window offset for absolute coordinates
        if absolute:
            dx, dy = self._get_window_offset()
            region = region.offset(dx, dy)

        return region

    def _get_window_offset(self) -> Tuple[int, int]:
        """Get window top-left offset."""
        if self.window:
            rect = self.window.get_window_rect()
            if rect:
                return (rect[0], rect[1])
        return self.window_offset

    def define(self, name: str, region: Region) -> None:
        """
        Define or update a region.

        Args:
            name: Region name.
            region: Region definition.
        """
        self.regions[name] = region
        logger.debug(f"Defined region: {name}")

    def remove(self, name: str) -> bool:
        """
        Remove a region.

        Args:
            name: Region name to remove.

        Returns:
            True if removed, False if not found.
        """
        if name in self.regions:
            del self.regions[name]
            return True
        return False

    def list_regions(self) -> Dict[str, Region]:
        """Get all defined regions."""
        return dict(self.regions)

    def calibrate(self) -> None:
        """
        Auto-calibrate regions based on window size.

        Calculates scale factor from current window size
        compared to base resolution.
        """
        if not self.window:
            return

        rect = self.window.get_window_rect()
        if not rect:
            return

        current_width = rect[2] - rect[0]
        current_height = rect[3] - rect[1]

        base_width, base_height = self.BASE_RESOLUTION

        # Calculate scale factor (use smaller dimension)
        width_scale = current_width / base_width
        height_scale = current_height / base_height
        self.scale_factor = min(width_scale, height_scale)

        logger.info(f"Calibrated scale factor: {self.scale_factor:.2f}")

    def save_config(self, path: str) -> None:
        """
        Save region configuration to file.

        Args:
            path: Output JSON file path.
        """
        config = {
            'base_resolution': self.BASE_RESOLUTION,
            'scale_factor': self.scale_factor,
            'regions': {
                name: region.to_dict()
                for name, region in self.regions.items()
            }
        }

        with open(path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved region config to {path}")

    def load_config(self, path: str) -> None:
        """
        Load region configuration from file.

        Args:
            path: Input JSON file path.
        """
        try:
            with open(path, 'r') as f:
                config = json.load(f)

            if 'scale_factor' in config:
                self.scale_factor = config['scale_factor']

            if 'regions' in config:
                for name, data in config['regions'].items():
                    self.regions[name] = Region.from_dict(data)

            logger.info(f"Loaded region config from {path}")

        except FileNotFoundError:
            logger.warning(f"Region config not found: {path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid region config: {e}")

    def interactive_define(self, name: str) -> Optional[Region]:
        """
        Interactively define a region via mouse selection.

        Prompts user to draw a rectangle on screen.

        Args:
            name: Name for the new region.

        Returns:
            Defined Region, or None if cancelled.
        """
        import pyautogui
        import time

        print(f"Defining region '{name}'...")
        print("Move mouse to top-left corner and press Enter...")

        input()
        x1, y1 = pyautogui.position()

        print("Move mouse to bottom-right corner and press Enter...")

        input()
        x2, y2 = pyautogui.position()

        # Create region
        region = Region(
            name=name,
            x=min(x1, x2),
            y=min(y1, y2),
            width=abs(x2 - x1),
            height=abs(y2 - y1),
            description=f"User-defined region: {name}"
        )

        self.define(name, region)
        print(f"Defined region: {region}")

        return region
