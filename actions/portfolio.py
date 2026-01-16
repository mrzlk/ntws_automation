"""
Portfolio and position management actions.
"""

from dataclasses import dataclass
from typing import List, Optional
import time

from .base import Action, ActionResult

import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """
    Portfolio position.

    Attributes:
        symbol: Stock symbol.
        quantity: Number of shares (negative for short).
        avg_price: Average entry price.
        current_price: Current market price.
        market_value: Current market value.
        pnl: Unrealized P&L in dollars.
        pnl_percent: Unrealized P&L percentage.
    """
    symbol: str
    quantity: int
    avg_price: float
    current_price: float = 0.0
    market_value: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0


class GetPortfolioAction(Action):
    """Get current portfolio positions."""

    def execute(self) -> ActionResult:
        """
        Read portfolio positions from TWS.

        Uses combination of:
        1. Navigate to portfolio window
        2. OCR to read position data

        Returns:
            ActionResult with list of Position objects in data.
        """
        start_time = time.time()

        self._log_action('get_portfolio')

        try:
            # 1. Open portfolio window
            self.hotkeys.execute(TWSAction.PORTFOLIO) if hasattr(self.hotkeys, 'execute') else None
            self._delay(0.5)

            # 2. Capture portfolio area
            screenshot = self.capture.capture_tws()
            if not screenshot:
                return ActionResult.fail(
                    error="Could not capture screen",
                    message="Portfolio read failed"
                )

            # 3. Use OCR to read positions
            # This is a simplified version - real implementation
            # would need to parse the portfolio table structure

            positions = []

            # Try to read using OCR
            region = self.toolkit.regions.get('portfolio_table', absolute=True)
            if region:
                table_data = self.ocr.read_table(
                    screenshot.crop(region.bounds)
                )

                for row in table_data:
                    try:
                        # Parse row data (format depends on TWS layout)
                        if 'symbol' in row or 'Symbol' in row:
                            symbol = row.get('symbol') or row.get('Symbol', '')
                            if symbol:
                                positions.append(Position(
                                    symbol=symbol,
                                    quantity=int(row.get('quantity', 0)),
                                    avg_price=float(row.get('avg_price', 0)),
                                    current_price=float(row.get('price', 0)),
                                    pnl=float(row.get('pnl', 0))
                                ))
                    except (ValueError, KeyError):
                        continue

            return ActionResult.ok(
                message=f"Found {len(positions)} positions",
                data=positions,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Portfolio read failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Portfolio read failed",
                duration=time.time() - start_time
            )


class GetPositionAction(Action):
    """Get specific position details."""

    def validate(self, symbol: str = None, **kwargs) -> Optional[str]:
        """Validate symbol."""
        if not symbol:
            return "Symbol required"
        return None

    def execute(self, symbol: str) -> ActionResult:
        """
        Get position for specific symbol.

        Args:
            symbol: Stock symbol.

        Returns:
            ActionResult with Position object in data.
        """
        start_time = time.time()

        error = self.validate(symbol=symbol)
        if error:
            return ActionResult.fail(error=error)

        self._log_action('get_position', {'symbol': symbol})

        try:
            # Get all positions and filter
            portfolio_result = GetPortfolioAction(self.toolkit).execute()

            if not portfolio_result.success:
                return portfolio_result

            positions = portfolio_result.data or []
            symbol_upper = symbol.upper()

            for position in positions:
                if position.symbol.upper() == symbol_upper:
                    return ActionResult.ok(
                        message=f"Found position: {symbol}",
                        data=position,
                        duration=time.time() - start_time
                    )

            return ActionResult.ok(
                message=f"No position found for {symbol}",
                data=None,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Position read failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Position read failed",
                duration=time.time() - start_time
            )


class ClosePositionAction(Action):
    """Close a position."""

    def execute(
        self,
        symbol: str,
        quantity: int = None,
        order_type: str = 'MKT'
    ) -> ActionResult:
        """
        Close position for symbol.

        Args:
            symbol: Symbol to close.
            quantity: Shares to close (None = all).
            order_type: Order type for closing.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        self._log_action('close_position', {
            'symbol': symbol,
            'quantity': quantity,
            'order_type': order_type
        })

        try:
            # 1. Get current position
            position_result = GetPositionAction(self.toolkit).execute(symbol)

            if not position_result.success:
                return position_result

            position = position_result.data
            if not position:
                return ActionResult.fail(
                    error=f"No position found for {symbol}",
                    message="Close failed"
                )

            # 2. Determine closing quantity
            close_qty = quantity or abs(position.quantity)
            close_side = 'SELL' if position.is_long else 'BUY'

            # 3. Create closing order
            from .order import CreateOrderAction, OrderParams

            params = OrderParams(
                symbol=symbol,
                side=close_side,
                quantity=close_qty,
                order_type=order_type
            )

            order_action = CreateOrderAction(self.toolkit)
            return order_action.execute(params=params, transmit=False)

        except Exception as e:
            logger.error(f"Close position failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Close position failed",
                duration=time.time() - start_time
            )


# Import TWSAction for hotkey access
from ..input.hotkeys import TWSAction
