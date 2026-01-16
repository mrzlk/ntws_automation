"""
TWS Automation Toolkit

GUI automation for IBKR Trader Workstation (TWS) without official API.
Provides Python API and MCP server for Claude integration.
"""

from .core.window import TWSWindow
from .core.element import ElementFinder, Element, ElementSpec
from .core.exceptions import (
    TWSAutomationError,
    WindowNotFoundError,
    ElementNotFoundError,
    TimeoutError,
    ActionFailedError,
)
from .config.settings import ConfigManager, ToolkitConfig

__version__ = "0.2.0"
__all__ = [
    "TWSToolkit",
    "TWSWindow",
    "ElementFinder",
    "Element",
    "ElementSpec",
    "ConfigManager",
    "ToolkitConfig",
    "TWSAutomationError",
    "WindowNotFoundError",
    "ElementNotFoundError",
    "TimeoutError",
    "ActionFailedError",
]


class TWSToolkit:
    """
    Main entry point for TWS automation.

    Provides unified access to all automation capabilities:
    - Window connection and management
    - Keyboard/mouse input
    - Screen reading (OCR)
    - High-level trading actions

    Usage:
        toolkit = TWSToolkit()
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
        window: TWS window manager
        keyboard: Keyboard automation
        mouse: Mouse automation
        hotkeys: TWS hotkey integration
        capture: Screen capture
        ocr: OCR engine
        finder: Element finder
        actions: High-level action registry
    """

    def __init__(self, config_path: str = None):
        """
        Initialize TWS Automation Toolkit.

        Args:
            config_path: Optional path to config file.
                        Uses default location if not specified.
        """
        from .config.settings import ConfigManager
        from .core.window import TWSWindow
        from .core.element import ElementFinder
        from .input.keyboard import Keyboard
        from .input.mouse import Mouse
        from .input.hotkeys import TWSHotkeys
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
        self._logger = get_logger('TWSToolkit')

        # Initialize components
        self.window = TWSWindow(timeout=self.config.timing.window_timeout)
        self.keyboard = Keyboard(
            typing_interval=self.config.timing.typing_interval
        )
        self.mouse = Mouse(
            fail_safe=self.config.safety.fail_safe_enabled
        )
        self.hotkeys = TWSHotkeys(
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

        self._logger.info("TWS Automation Toolkit initialized")

    def connect(self) -> bool:
        """
        Connect to running TWS instance.

        Returns:
            True if connected successfully, False otherwise.

        Raises:
            WindowNotFoundError: If TWS window not found.
        """
        self._logger.info("Connecting to TWS...")

        if not self.window.connect():
            self._logger.error("Failed to connect to TWS")
            return False

        self._logger.info("Connected to TWS successfully")

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
        Verify TWS is in paper trading mode.

        Checks jts.ini for tradingMode=p setting.

        Returns:
            True if paper trading mode, False otherwise.
        """
        import os

        jts_ini_path = os.path.join(self.config.tws_path, 'jts.ini')

        try:
            with open(jts_ini_path, 'r') as f:
                content = f.read()
                return 'tradingMode=p' in content
        except FileNotFoundError:
            self._logger.warning(f"jts.ini not found at {jts_ini_path}")
            return False

    def disconnect(self) -> None:
        """Cleanup and disconnect from TWS."""
        self._logger.info("Disconnecting from TWS")
        # Cleanup resources if needed

    def is_connected(self) -> bool:
        """Check if connected to TWS."""
        return self.window.is_ready()
