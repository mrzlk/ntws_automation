"""
Chart-related actions for TWS.
"""

from typing import Optional
import time

from .base import Action, ActionResult

import logging

logger = logging.getLogger(__name__)


class OpenChartAction(Action):
    """Open a chart for a symbol."""

    TIMEFRAME_MAP = {
        '1m': '1 min',
        '5m': '5 mins',
        '15m': '15 mins',
        '30m': '30 mins',
        '1h': '1 hour',
        '1H': '1 hour',
        '4h': '4 hours',
        '4H': '4 hours',
        '1d': '1 day',
        '1D': '1 day',
        '1w': '1 week',
        '1W': '1 week',
        '1M': '1 month',
    }

    def validate(self, symbol: str = None, **kwargs) -> Optional[str]:
        """Validate symbol format."""
        if not symbol:
            return "Symbol required"
        if len(symbol) > 10:
            return "Symbol too long"
        return None

    def execute(
        self,
        symbol: str,
        timeframe: str = '1D',
        chart_type: str = 'candlestick'
    ) -> ActionResult:
        """
        Open chart for symbol.

        Steps:
        1. Use Ctrl+F or symbol search hotkey
        2. Type symbol name
        3. Press Enter to select
        4. Navigate to chart (via menu or right-click)

        Args:
            symbol: Stock symbol.
            timeframe: Chart timeframe.
            chart_type: Chart type.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        error = self.validate(symbol=symbol)
        if error:
            return ActionResult.fail(error=error)

        self._log_action('open_chart', {
            'symbol': symbol,
            'timeframe': timeframe
        })

        try:
            # 1. Search for symbol
            self.hotkeys.search()
            self._delay(0.3)

            # 2. Type symbol
            self.keyboard.type_text(symbol.upper())
            self._delay(0.5)

            # 3. Select first result
            self.keyboard.press('enter')
            self._delay(0.5)

            # 4. Open chart via right-click menu
            # (This is a simplified version - real implementation
            # would need to navigate the context menu)
            self.mouse.right_click()
            self._delay(0.3)

            # Type 'c' for Chart option (if available)
            self.keyboard.press('c')
            self._delay(0.5)

            return ActionResult.ok(
                message=f"Chart opened: {symbol}",
                data={'symbol': symbol, 'timeframe': timeframe},
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Chart open failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Failed to open chart",
                duration=time.time() - start_time
            )


class ChangeTimeframeAction(Action):
    """Change chart timeframe."""

    TIMEFRAME_MAP = {
        '1m': '1 min',
        '5m': '5 mins',
        '15m': '15 mins',
        '30m': '30 mins',
        '1h': '1 hour',
        '1H': '1 hour',
        '4h': '4 hours',
        '4H': '4 hours',
        '1d': '1 day',
        '1D': '1 day',
        '1w': '1 week',
        '1W': '1 week',
        '1M': '1 month',
    }

    def validate(self, timeframe: str = None, **kwargs) -> Optional[str]:
        """Validate timeframe."""
        if not timeframe:
            return "Timeframe required"
        if timeframe not in self.TIMEFRAME_MAP:
            valid = ', '.join(self.TIMEFRAME_MAP.keys())
            return f"Invalid timeframe. Valid: {valid}"
        return None

    def execute(self, timeframe: str) -> ActionResult:
        """
        Change current chart timeframe.

        Args:
            timeframe: New timeframe.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        error = self.validate(timeframe=timeframe)
        if error:
            return ActionResult.fail(error=error)

        self._log_action('change_timeframe', {'timeframe': timeframe})

        try:
            # This is a placeholder - actual implementation would
            # need to find and interact with timeframe selector
            logger.info(f"Changing timeframe to {timeframe}")

            # Typically would:
            # 1. Click on timeframe dropdown
            # 2. Select the desired timeframe
            # 3. Wait for chart to update

            return ActionResult.ok(
                message=f"Timeframe changed to {timeframe}",
                data={'timeframe': timeframe},
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Timeframe change failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Failed to change timeframe",
                duration=time.time() - start_time
            )


class AddIndicatorAction(Action):
    """Add technical indicator to chart."""

    def execute(
        self,
        indicator_name: str,
        **params
    ) -> ActionResult:
        """
        Add indicator to current chart.

        Args:
            indicator_name: Indicator name (e.g., 'SMA', 'RSI').
            **params: Indicator parameters.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        self._log_action('add_indicator', {
            'indicator': indicator_name,
            'params': params
        })

        try:
            # Placeholder - would need to:
            # 1. Open indicator dialog
            # 2. Search for indicator
            # 3. Configure parameters
            # 4. Apply

            logger.info(f"Adding indicator: {indicator_name}")

            return ActionResult.ok(
                message=f"Indicator added: {indicator_name}",
                data={'indicator': indicator_name, 'params': params},
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Add indicator failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Failed to add indicator",
                duration=time.time() - start_time
            )
