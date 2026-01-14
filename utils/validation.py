"""
Input validation utilities.
"""

import re
from typing import Optional, Union
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """
    Validation error.

    Raised when input validation fails.
    """

    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.message = message
        self.field = field


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize stock symbol.

    Args:
        symbol: Stock symbol to validate.

    Returns:
        Normalized uppercase symbol.

    Raises:
        ValidationError: If symbol is invalid.

    Example:
        >>> validate_symbol('aapl')
        'AAPL'
        >>> validate_symbol('BRK.B')
        'BRK.B'
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string", "symbol")

    symbol = symbol.strip().upper()

    # Allow letters, dots (for class shares), and hyphens
    if not re.match(r'^[A-Z]{1,5}(\.[A-Z])?(-[A-Z])?$', symbol):
        raise ValidationError(
            f"Invalid symbol format: {symbol}. "
            "Must be 1-5 uppercase letters, optionally with .X or -X suffix.",
            "symbol"
        )

    return symbol


def validate_quantity(
    quantity: Union[int, str],
    max_qty: int = None,
    min_qty: int = 1
) -> int:
    """
    Validate order quantity.

    Args:
        quantity: Quantity to validate.
        max_qty: Maximum allowed quantity.
        min_qty: Minimum allowed quantity.

    Returns:
        Validated quantity as integer.

    Raises:
        ValidationError: If quantity is invalid.
    """
    try:
        qty = int(quantity)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Quantity must be an integer, got: {quantity}",
            "quantity"
        )

    if qty < min_qty:
        raise ValidationError(
            f"Quantity must be at least {min_qty}, got: {qty}",
            "quantity"
        )

    if max_qty is not None and qty > max_qty:
        raise ValidationError(
            f"Quantity {qty} exceeds maximum {max_qty}",
            "quantity"
        )

    return qty


def validate_price(
    price: Union[float, str, Decimal],
    min_price: float = 0.01,
    max_price: float = None
) -> Decimal:
    """
    Validate and convert price.

    Args:
        price: Price to validate.
        min_price: Minimum allowed price.
        max_price: Maximum allowed price.

    Returns:
        Validated price as Decimal.

    Raises:
        ValidationError: If price is invalid.
    """
    try:
        if isinstance(price, Decimal):
            price_decimal = price
        else:
            price_decimal = Decimal(str(price))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(
            f"Price must be a valid number, got: {price}",
            "price"
        )

    if price_decimal < Decimal(str(min_price)):
        raise ValidationError(
            f"Price must be at least {min_price}, got: {price_decimal}",
            "price"
        )

    if max_price is not None and price_decimal > Decimal(str(max_price)):
        raise ValidationError(
            f"Price {price_decimal} exceeds maximum {max_price}",
            "price"
        )

    return price_decimal


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: Order side ('BUY' or 'SELL').

    Returns:
        Normalized uppercase side.

    Raises:
        ValidationError: If side is invalid.
    """
    if not side:
        raise ValidationError("Side is required", "side")

    side = side.strip().upper()

    if side not in ('BUY', 'SELL'):
        raise ValidationError(
            f"Side must be 'BUY' or 'SELL', got: {side}",
            "side"
        )

    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: Order type.

    Returns:
        Normalized uppercase order type.

    Raises:
        ValidationError: If order type is invalid.
    """
    valid_types = ('MKT', 'LMT', 'STP', 'STP_LMT', 'MIT', 'LIT')

    if not order_type:
        raise ValidationError("Order type is required", "order_type")

    order_type = order_type.strip().upper()

    if order_type not in valid_types:
        raise ValidationError(
            f"Invalid order type: {order_type}. Valid types: {', '.join(valid_types)}",
            "order_type"
        )

    return order_type


def validate_timeframe(timeframe: str) -> str:
    """
    Validate chart timeframe.

    Args:
        timeframe: Timeframe string.

    Returns:
        Normalized timeframe.

    Raises:
        ValidationError: If timeframe is invalid.
    """
    valid_timeframes = (
        '1m', '5m', '15m', '30m',
        '1h', '1H', '4h', '4H',
        '1d', '1D', '1w', '1W', '1M'
    )

    if not timeframe:
        raise ValidationError("Timeframe is required", "timeframe")

    if timeframe not in valid_timeframes:
        raise ValidationError(
            f"Invalid timeframe: {timeframe}. Valid: {', '.join(valid_timeframes)}",
            "timeframe"
        )

    return timeframe
