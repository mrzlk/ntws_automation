"""
Actions module - high-level trading operations.

Provides action classes for:
- Order management (create, transmit, cancel)
- Chart operations
- Portfolio reading
- Navigation
"""

from .base import Action, ActionResult, CompositeAction
from .order import (
    OrderParams,
    CreateOrderAction,
    TransmitOrderAction,
    CancelOrderAction,
)
from .chart import OpenChartAction, ChangeTimeframeAction
from .portfolio import GetPortfolioAction, GetPositionAction, Position
from .navigation import SearchSymbolAction, OpenWindowAction

__all__ = [
    "Action",
    "ActionResult",
    "CompositeAction",
    "OrderParams",
    "CreateOrderAction",
    "TransmitOrderAction",
    "CancelOrderAction",
    "OpenChartAction",
    "ChangeTimeframeAction",
    "GetPortfolioAction",
    "GetPositionAction",
    "Position",
    "SearchSymbolAction",
    "OpenWindowAction",
    "ActionRegistry",
]


class ActionRegistry:
    """
    Registry for available high-level actions.

    Provides convenient access to all actions through
    the TWSToolkit.actions interface.
    """

    def __init__(self, toolkit: 'TWSToolkit'):
        """
        Initialize action registry.

        Args:
            toolkit: Parent TWSToolkit instance.
        """
        self.toolkit = toolkit

        # Initialize actions
        self._search_symbol = SearchSymbolAction(toolkit)
        self._open_window = OpenWindowAction(toolkit)
        self._open_chart = OpenChartAction(toolkit)
        self._change_timeframe = ChangeTimeframeAction(toolkit)
        self._create_order = CreateOrderAction(toolkit)
        self._transmit_order = TransmitOrderAction(toolkit)
        self._cancel_order = CancelOrderAction(toolkit)
        self._get_portfolio = GetPortfolioAction(toolkit)
        self._get_position = GetPositionAction(toolkit)

    # Navigation actions

    def search_symbol(self, symbol: str, select: bool = True) -> ActionResult:
        """
        Search for and select a symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL').
            select: If True, select the first result.

        Returns:
            ActionResult with success status.
        """
        return self._search_symbol.execute(symbol=symbol, select=select)

    def open_window(self, window_name: str) -> ActionResult:
        """
        Open TWS window by name.

        Args:
            window_name: Window name ('portfolio', 'orders', etc.).

        Returns:
            ActionResult with success status.
        """
        return self._open_window.execute(window_name=window_name)

    # Chart actions

    def open_chart(
        self,
        symbol: str,
        timeframe: str = '1D',
        chart_type: str = 'candlestick'
    ) -> ActionResult:
        """
        Open chart for symbol.

        Args:
            symbol: Stock symbol.
            timeframe: Chart timeframe ('1m', '5m', '1H', '1D', etc.).
            chart_type: Chart type ('candlestick', 'line', 'bar').

        Returns:
            ActionResult with success status.
        """
        return self._open_chart.execute(
            symbol=symbol,
            timeframe=timeframe,
            chart_type=chart_type
        )

    def change_timeframe(self, timeframe: str) -> ActionResult:
        """
        Change current chart timeframe.

        Args:
            timeframe: New timeframe.

        Returns:
            ActionResult with success status.
        """
        return self._change_timeframe.execute(timeframe=timeframe)

    # Order actions

    def create_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = 'LMT',
        limit_price: float = None,
        stop_price: float = None,
        time_in_force: str = 'DAY',
        transmit: bool = False
    ) -> ActionResult:
        """
        Create a new order.

        WARNING: In live trading mode, this creates real orders.

        Args:
            symbol: Stock symbol.
            side: 'BUY' or 'SELL'.
            quantity: Number of shares.
            order_type: 'MKT', 'LMT', 'STP', 'STP_LMT'.
            limit_price: Limit price (required for LMT orders).
            stop_price: Stop price (required for STP orders).
            time_in_force: 'DAY', 'GTC', 'IOC', 'FOK'.
            transmit: If True, transmit order immediately.

        Returns:
            ActionResult with success status.
        """
        params = OrderParams(
            symbol=symbol,
            side=side.upper(),
            quantity=quantity,
            order_type=order_type.upper(),
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force.upper()
        )
        return self._create_order.execute(params=params, transmit=transmit)

    def transmit_order(self, confirm: bool = True) -> ActionResult:
        """
        Transmit the selected/current order.

        Args:
            confirm: If True, verify before transmitting.

        Returns:
            ActionResult with success status.
        """
        return self._transmit_order.execute(confirm=confirm)

    def cancel_order(
        self,
        order_id: str = None,
        cancel_all: bool = False
    ) -> ActionResult:
        """
        Cancel order(s).

        Args:
            order_id: Specific order ID to cancel.
            cancel_all: If True, cancel all pending orders.

        Returns:
            ActionResult with success status.
        """
        return self._cancel_order.execute(
            order_id=order_id,
            cancel_all=cancel_all
        )

    # Portfolio actions

    def get_portfolio(self) -> ActionResult:
        """
        Get current portfolio positions.

        Returns:
            ActionResult with list of Position objects in data.
        """
        return self._get_portfolio.execute()

    def get_position(self, symbol: str) -> ActionResult:
        """
        Get position for specific symbol.

        Args:
            symbol: Stock symbol.

        Returns:
            ActionResult with Position object in data.
        """
        return self._get_position.execute(symbol=symbol)
