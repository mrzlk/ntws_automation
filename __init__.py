"""
NTWS Automation Toolkit

GUI automation for IBKR Trader Workstation without official API.
Provides Python API and MCP server for Claude integration.
"""

from .core.window import NTWSWindow
from .core.element import ElementFinder, Element, ElementSpec
from .core.exceptions import (
    NTWSAutomationError,
    WindowNotFoundError,
    ElementNotFoundError,
    TimeoutError,
    ActionFailedError,
)
from .config.settings import ConfigManager, ToolkitConfig

__version__ = "0.1.0"
__all__ = [
    "NTWSToolkit",
    "NTWSWindow",
    "ElementFinder",
    "Element",
    "ElementSpec",
    "ConfigManager",
    "ToolkitConfig",
    "NTWSAutomationError",
    "WindowNotFoundError",
    "ElementNotFoundError",
    "TimeoutError",
    "ActionFailedError",
]


class NTWSToolkit:
    """
    Main entry point for NTWS automation.

    Provides unified access to all automation capabilities:
    - Window connection and management
    - Keyboard/mouse input
    - Screen reading (OCR)
    - High-level trading actions

    Usage:
        toolkit = NTWSToolkit()
        toolkit.connect()

        # Search for symbol
        toolkit.actions.search_symbol('AAPL')

        # Create order (paper trading only by default)
        toolkit.actions.create_order(
            symbol='AAPL',
            side='BUY',
            quantity=100,
            order_type='LMT',
            limit_price=150.00
        )

    Attributes:
        config: Toolkit configuration
        window: NTWS window manager
        keyboard: Keyboard automation
        mouse: Mouse automation
        hotkeys: NTWS hotkey integration
        capture: Screen capture
        ocr: OCR engine
        finder: Element finder
        actions: High-level action registry
    """

    def __init__(self, config_path: str = None):
        """
        Initialize NTWS Automation Toolkit.

        Args:
            config_path: Optional path to config file.
                        Uses default location if not specified.
        """
        from .config.settings import ConfigManager
        from .core.window import NTWSWindow
        from .core.element import ElementFinder
        from .input.keyboard import Keyboard
        from .input.mouse import Mouse
        from .input.hotkeys import NTWSHotkeys
        from .screen.capture import ScreenCapture
        from .screen.ocr import OCREngine
        from .screen.regions import RegionManager
        from .actions import ActionRegistry
        from .utils.logging import setup_logging, get_logger

        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        # Setup logging
        setup_logging(self.config.logging)
        self._logger = get_logger('NTWSToolkit')

        # Initialize components
        self.window = NTWSWindow(timeout=self.config.timing.window_timeout)
        self.keyboard = Keyboard(
            typing_interval=self.config.timing.typing_interval
        )
        self.mouse = Mouse(
            fail_safe=self.config.safety.fail_safe_enabled
        )
        self.hotkeys = NTWSHotkeys(
            self.keyboard,
            self.config.custom_hotkeys
        )
        self.capture = ScreenCapture(self.window)
        self.ocr = OCREngine(
            languages=self.config.ocr.languages,
            use_gpu=self.config.ocr.use_gpu
        )
        self.regions = RegionManager(self.window)
        self.finder = ElementFinder(self.window)

        # Initialize action registry
        self.actions = ActionRegistry(self)

        self._logger.info("NTWS Automation Toolkit initialized")

    def connect(self) -> bool:
        """
        Connect to running NTWS instance.

        Returns:
            True if connected successfully, False otherwise.

        Raises:
            WindowNotFoundError: If NTWS window not found.
        """
        self._logger.info("Connecting to NTWS...")

        if not self.window.connect():
            self._logger.error("Failed to connect to NTWS")
            return False

        self._logger.info("Connected to NTWS successfully")

        # Safety check for paper trading
        if self.config.safety.paper_trading_only:
            if not self._verify_paper_trading():
                self._logger.error(
                    "Safety: Paper trading mode required but "
                    "live trading detected. Aborting."
                )
                return False

        return True

    def _verify_paper_trading(self) -> bool:
        """
        Verify NTWS is in paper trading mode.

        Checks jts.ini for tradingMode=p setting.

        Returns:
            True if paper trading mode, False otherwise.
        """
        import os

        jts_ini_path = os.path.join(self.config.ntws_path, 'jts.ini')

        try:
            with open(jts_ini_path, 'r') as f:
                content = f.read()
                return 'tradingMode=p' in content
        except FileNotFoundError:
            self._logger.warning(f"jts.ini not found at {jts_ini_path}")
            return False

    def disconnect(self) -> None:
        """Cleanup and disconnect from NTWS."""
        self._logger.info("Disconnecting from NTWS")
        # Cleanup resources if needed

    def is_connected(self) -> bool:
        """Check if connected to NTWS."""
        return self.window.is_ready()
