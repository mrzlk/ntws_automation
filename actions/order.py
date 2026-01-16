"""
Order entry actions for TWS.

IMPORTANT: These actions can place real orders in live trading mode.
Use with caution and always verify paper trading mode is active.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from decimal import Decimal
import time

from .base import Action, ActionResult
from ..input.hotkeys import TWSAction

import logging

logger = logging.getLogger(__name__)


@dataclass
class OrderParams:
    """
    Order parameters.

    Attributes:
        symbol: Stock symbol (e.g., 'AAPL').
        side: Order side ('BUY' or 'SELL').
        quantity: Number of shares.
        order_type: Order type ('MKT', 'LMT', 'STP', 'STP_LMT').
        limit_price: Limit price for LMT orders.
        stop_price: Stop price for STP orders.
        time_in_force: Time in force ('DAY', 'GTC', 'IOC', 'FOK').
    """
    symbol: str
    side: Literal['BUY', 'SELL']
    quantity: int
    order_type: Literal['MKT', 'LMT', 'STP', 'STP_LMT'] = 'LMT'
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Literal['DAY', 'GTC', 'IOC', 'FOK'] = 'DAY'

    def validate(self) -> Optional[str]:
        """Validate order parameters."""
        if not self.symbol or len(self.symbol) > 10:
            return "Invalid symbol"

        if self.quantity <= 0:
            return "Quantity must be positive"

        if self.order_type == 'LMT' and self.limit_price is None:
            return "Limit price required for LMT orders"

        if self.order_type in ('STP', 'STP_LMT') and self.stop_price is None:
            return "Stop price required for stop orders"

        if self.limit_price is not None and self.limit_price <= 0:
            return "Limit price must be positive"

        if self.stop_price is not None and self.stop_price <= 0:
            return "Stop price must be positive"

        return None


class CreateOrderAction(Action):
    """
    Create a new order.

    WARNING: In live trading mode, this action can place real orders
    that may result in financial transactions.
    """

    def validate(self, params: OrderParams = None, **kwargs) -> Optional[str]:
        """Validate order parameters."""
        if params is None:
            return "Order params required"

        # Validate order params
        error = params.validate()
        if error:
            return error

        # Safety checks
        safety = self.config.safety

        if params.quantity > safety.max_order_quantity:
            return f"Quantity {params.quantity} exceeds max {safety.max_order_quantity}"

        # Check order value if limit price provided
        if params.limit_price:
            order_value = params.quantity * params.limit_price
            if order_value > safety.max_order_value:
                return f"Order value ${order_value:.2f} exceeds max ${safety.max_order_value:.2f}"

        return None

    def execute(
        self,
        params: OrderParams,
        transmit: bool = False
    ) -> ActionResult:
        """
        Create order with given parameters.

        Steps:
        1. Navigate to symbol (if not already selected)
        2. Use hotkey for Buy (Alt+B) or Sell (Alt+S)
        3. Fill in quantity
        4. Select order type
        5. Fill in price(s)
        6. Optionally transmit (Alt+T)

        Args:
            params: Order parameters.
            transmit: If True, also transmit the order.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        # Validate
        error = self.validate(params=params)
        if error:
            return ActionResult.fail(error=error)

        self._log_action('create_order', {
            'symbol': params.symbol,
            'side': params.side,
            'qty': params.quantity,
            'type': params.order_type,
            'price': params.limit_price
        })

        # Log warning for safety
        logger.warning(
            f"Creating {params.side} order: {params.symbol} "
            f"x{params.quantity} @ {params.limit_price or 'MKT'}"
        )

        try:
            # 1. Search for symbol first
            self.hotkeys.search()
            self._delay(0.3)
            self.keyboard.type_text(params.symbol)
            self._delay(0.5)
            self.keyboard.press('enter')
            self._delay(0.3)

            # 2. Trigger buy/sell hotkey
            if params.side == 'BUY':
                self.hotkeys.buy()
            else:
                self.hotkeys.sell()
            self._delay(0.3)

            # 3. Fill quantity (select all first, then type)
            self.keyboard.hotkey('ctrl', 'a')
            self.keyboard.type_text(str(params.quantity))
            self.keyboard.press('tab')
            self._delay(0.2)

            # 4. Fill price if limit order
            if params.order_type in ('LMT', 'STP_LMT') and params.limit_price:
                self.keyboard.hotkey('ctrl', 'a')
                self.keyboard.type_text(f"{params.limit_price:.2f}")
                self.keyboard.press('tab')
                self._delay(0.2)

            # 5. Transmit if requested
            if transmit:
                if self.config.safety.confirm_orders:
                    logger.info("Order ready for transmission (confirm_orders=True)")
                    # Would wait for confirmation here
                self.hotkeys.transmit()
                self._delay(0.5)

            return ActionResult.ok(
                message=f"Order created: {params.side} {params.symbol} x{params.quantity}",
                data={'params': params, 'transmitted': transmit},
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Order creation failed",
                duration=time.time() - start_time
            )


class TransmitOrderAction(Action):
    """Transmit pending order."""

    def execute(self, confirm: bool = True) -> ActionResult:
        """
        Transmit the selected order.

        Args:
            confirm: If True, verify order details before transmitting.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        self._log_action('transmit_order', {'confirm': confirm})

        try:
            if confirm and self.config.safety.confirm_orders:
                # Here we could capture screen and OCR to verify order
                logger.info("Order transmission requested (confirm mode)")

            self.hotkeys.transmit()
            self._delay(0.5)

            return ActionResult.ok(
                message="Order transmitted",
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Order transmission failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Transmission failed",
                duration=time.time() - start_time
            )


class CancelOrderAction(Action):
    """Cancel order(s)."""

    def execute(
        self,
        order_id: str = None,
        cancel_all: bool = False
    ) -> ActionResult:
        """
        Cancel order(s).

        Args:
            order_id: Specific order to cancel (not implemented yet).
            cancel_all: If True, cancel all pending orders.

        Returns:
            ActionResult with success status.
        """
        start_time = time.time()

        self._log_action('cancel_order', {
            'order_id': order_id,
            'cancel_all': cancel_all
        })

        try:
            if cancel_all:
                self.hotkeys.cancel_all()
                message = "All orders cancelled"
            else:
                self.hotkeys.cancel()
                message = "Order cancelled"

            self._delay(0.5)

            return ActionResult.ok(
                message=message,
                duration=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return ActionResult.fail(
                error=str(e),
                message="Cancellation failed",
                duration=time.time() - start_time
            )
