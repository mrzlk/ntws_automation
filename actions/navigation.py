"""
TWS navigation actions.
"""

from typing import Optional, List
import time

from .base import Action, ActionResult

import logging

logger = logging.getLogger(__name__)


class SearchSymbolAction(Action):
    """Search for a symbol."""

    def validate(self, symbol: str = None, **kwargs) -> Optional[str]:
        """Validate symbol."""
        if not symbol:
            return "Symbol required"
        if len(symbol) > 10:
            return "Symbol too long"
        return None

    def execute(
        self,
        symbol: str,
        select: bool = True
    ) -> ActionResult:
        """
        Search for symbol and optionally select it.

        Steps:
        1. Press Ctrl+F or search hotkey
        2. Type symbol
        3. Wait for suggestions
        4. Select first match if select=True

        Args:
            symbol: Stock symbol to search.
            select: If True, select the first result.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        error = self.validate(symbol=symbol)
        if error:
            return ActionResult.fail(error=error)

        self._log_action('search_symbol', {'symbol': symbol, 'select': select})

        try:
            # 1. Open search
            self.hotkeys.search()
            self._delay(0.3)

            # 2. Clear existing text and type symbol
            self.keyboard.hotkey('ctrl', 'a')
            self.keyboard.type_text(symbol.upper())
            self._delay(0.5)

            # 3. Select first result if requested
            if select:
                self.keyboard.press('enter')
                self._delay(0.3)

            return ActionResult.ok(
                message=f"Symbol searched: {symbol}",
                data={'symbol': symbol, 'selected': select},
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Symbol search failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Search failed",
                duration=time.time() - start_time
            )


class OpenWindowAction(Action):
    """Open specific TWS window/panel."""

    # Window name to menu path mapping
    WINDOWS = {
        'portfolio': ('View', 'Portfolio'),
        'orders': ('View', 'Orders'),
        'trades': ('View', 'Trades'),
        'watchlist': ('View', 'Watchlist'),
        'news': ('View', 'News'),
        'scanner': ('Tools', 'Option Scanner'),
        'chart': ('View', 'Chart'),
        'settings': ('Edit', 'Global Configuration'),
        'account': ('Account', 'Account Window'),
    }

    def validate(self, window_name: str = None, **kwargs) -> Optional[str]:
        """Validate window name."""
        if not window_name:
            return "Window name required"
        if window_name.lower() not in self.WINDOWS:
            valid = ', '.join(self.WINDOWS.keys())
            return f"Unknown window. Valid: {valid}"
        return None

    def execute(self, window_name: str) -> ActionResult:
        """
        Open window by name.

        Args:
            window_name: Window name (portfolio, orders, etc.).

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        error = self.validate(window_name=window_name)
        if error:
            return ActionResult.fail(error=error)

        self._log_action('open_window', {'window': window_name})

        try:
            window_key = window_name.lower()
            menu_path = self.WINDOWS[window_key]

            # Navigate through menu
            result = NavigateMenuAction(self.toolkit).execute(
                menu_path=list(menu_path)
            )

            if result.success:
                return ActionResult.ok(
                    message=f"Opened window: {window_name}",
                    data={'window': window_name},
                    duration=time.time() - start_time
                )
            else:
                return result

        except Exception as e:
            logger.error(f"Open window failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Failed to open window",
                duration=time.time() - start_time
            )


class NavigateMenuAction(Action):
    """Navigate through menu system."""

    def execute(self, menu_path: List[str]) -> ActionResult:
        """
        Navigate menu path.

        Args:
            menu_path: List of menu items (e.g., ['File', 'Export']).

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        if not menu_path:
            return ActionResult.fail(error="Menu path required")

        self._log_action('navigate_menu', {'path': menu_path})

        try:
            # Press Alt to activate menu bar
            self.keyboard.press('alt')
            self._delay(0.2)

            # Navigate through each menu level
            for i, item in enumerate(menu_path):
                # Type first letter or use arrow keys
                self.keyboard.type_text(item[0].lower())
                self._delay(0.2)

                if i < len(menu_path) - 1:
                    # Not last item, wait for submenu
                    self._delay(0.1)

            # Press Enter to select final item
            self.keyboard.press('enter')
            self._delay(0.3)

            return ActionResult.ok(
                message=f"Navigated menu: {' > '.join(menu_path)}",
                data={'path': menu_path},
                duration=time.time() - start_time
            )

        except Exception as e:
            # Press Escape to close any open menus
            self.keyboard.press('escape')
            logger.error(f"Menu navigation failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Menu navigation failed",
                duration=time.time() - start_time
            )


class RefreshDataAction(Action):
    """Refresh market data."""

    def execute(self) -> ActionResult:
        """
        Refresh current data display.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        self._log_action('refresh_data')

        try:
            self.hotkeys.refresh()
            self._delay(0.5)

            return ActionResult.ok(
                message="Data refreshed",
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Refresh failed",
                duration=time.time() - start_time
            )
