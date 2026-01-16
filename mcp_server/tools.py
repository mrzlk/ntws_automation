"""
MCP Tools definitions for TWS Automation.

Defines the tools that Claude can use to control TWS.
"""

import json
import logging
import base64
from typing import List, Dict, Any, TYPE_CHECKING
from io import BytesIO

if TYPE_CHECKING:
    from .. import TWSToolkit

logger = logging.getLogger(__name__)


def get_tools() -> List[Dict[str, Any]]:
    """
    Get list of available MCP tools.

    Returns:
        List of tool definitions in MCP format.
    """
    try:
        from mcp.types import Tool
    except ImportError:
        # Return raw dicts if mcp not installed
        Tool = dict

    tools = [
        # Order tools (priority)
        Tool(
            name="create_order",
            description="Create a new order in TWS. WARNING: In live mode this places real orders.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., 'AAPL')"
                    },
                    "side": {
                        "type": "string",
                        "enum": ["BUY", "SELL"],
                        "description": "Order side"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of shares"
                    },
                    "order_type": {
                        "type": "string",
                        "enum": ["MKT", "LMT", "STP", "STP_LMT"],
                        "default": "LMT",
                        "description": "Order type"
                    },
                    "limit_price": {
                        "type": "number",
                        "description": "Limit price (required for LMT orders)"
                    },
                    "transmit": {
                        "type": "boolean",
                        "default": False,
                        "description": "Transmit order immediately"
                    }
                },
                "required": ["symbol", "side", "quantity"]
            }
        ),

        Tool(
            name="transmit_order",
            description="Transmit the current/selected order",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "default": True,
                        "description": "Verify before transmitting"
                    }
                }
            }
        ),

        Tool(
            name="cancel_order",
            description="Cancel order(s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Specific order ID to cancel"
                    },
                    "cancel_all": {
                        "type": "boolean",
                        "default": False,
                        "description": "Cancel all pending orders"
                    }
                }
            }
        ),

        # Navigation tools
        Tool(
            name="search_symbol",
            description="Search for and select a stock symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol to search"
                    },
                    "select": {
                        "type": "boolean",
                        "default": True,
                        "description": "Select first result"
                    }
                },
                "required": ["symbol"]
            }
        ),

        Tool(
            name="open_chart",
            description="Open a chart for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "timeframe": {
                        "type": "string",
                        "default": "1D",
                        "description": "Chart timeframe (1m, 5m, 1H, 1D, etc.)"
                    }
                },
                "required": ["symbol"]
            }
        ),

        # Portfolio tools
        Tool(
            name="get_portfolio",
            description="Get current portfolio positions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        Tool(
            name="get_position",
            description="Get position for specific symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    }
                },
                "required": ["symbol"]
            }
        ),

        # Screen tools
        Tool(
            name="screenshot",
            description="Take a screenshot of TWS terminal",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Named region to capture (optional)"
                    }
                }
            }
        ),

        Tool(
            name="read_screen",
            description="Read text from screen using OCR",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Named region to read"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern to find"
                    }
                }
            }
        ),

        # Status tools
        Tool(
            name="get_status",
            description="Get TWS connection status and trading mode",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]

    return tools


async def handle_tool_call(
    toolkit: 'TWSToolkit',
    name: str,
    arguments: dict
) -> str:
    """
    Handle MCP tool call.

    Args:
        toolkit: TWSToolkit instance.
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        JSON string with result.
    """
    logger.info(f"Tool call: {name} with args: {arguments}")

    try:
        result = _execute_tool(toolkit, name, arguments)
        return json.dumps(result, default=str)

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def _execute_tool(
    toolkit: 'TWSToolkit',
    name: str,
    args: dict
) -> dict:
    """Execute tool and return result dict."""

    # Order tools
    if name == "create_order":
        result = toolkit.actions.create_order(
            symbol=args["symbol"],
            side=args["side"],
            quantity=args["quantity"],
            order_type=args.get("order_type", "LMT"),
            limit_price=args.get("limit_price"),
            transmit=args.get("transmit", False)
        )
        return _action_result_to_dict(result)

    elif name == "transmit_order":
        result = toolkit.actions.transmit_order(
            confirm=args.get("confirm", True)
        )
        return _action_result_to_dict(result)

    elif name == "cancel_order":
        result = toolkit.actions.cancel_order(
            order_id=args.get("order_id"),
            cancel_all=args.get("cancel_all", False)
        )
        return _action_result_to_dict(result)

    # Navigation tools
    elif name == "search_symbol":
        result = toolkit.actions.search_symbol(
            symbol=args["symbol"],
            select=args.get("select", True)
        )
        return _action_result_to_dict(result)

    elif name == "open_chart":
        result = toolkit.actions.open_chart(
            symbol=args["symbol"],
            timeframe=args.get("timeframe", "1D")
        )
        return _action_result_to_dict(result)

    # Portfolio tools
    elif name == "get_portfolio":
        result = toolkit.actions.get_portfolio()
        response = _action_result_to_dict(result)
        if result.data:
            response["positions"] = [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_price": p.avg_price,
                    "current_price": p.current_price,
                    "pnl": p.pnl
                }
                for p in result.data
            ]
        return response

    elif name == "get_position":
        result = toolkit.actions.get_position(symbol=args["symbol"])
        response = _action_result_to_dict(result)
        if result.data:
            p = result.data
            response["position"] = {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "avg_price": p.avg_price,
                "pnl": p.pnl
            }
        return response

    # Screen tools
    elif name == "screenshot":
        image = toolkit.capture.capture_tws()
        if image:
            # Convert to base64
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            b64 = base64.b64encode(buffer.getvalue()).decode()
            return {
                "success": True,
                "image_base64": b64,
                "width": image.width,
                "height": image.height
            }
        return {"success": False, "error": "Could not capture screenshot"}

    elif name == "read_screen":
        image = toolkit.capture.capture_tws()
        if image:
            if args.get("pattern"):
                result = toolkit.ocr.find_text(image, args["pattern"])
                if result:
                    return {
                        "success": True,
                        "text": result.text,
                        "confidence": result.confidence,
                        "position": result.bbox
                    }
                return {"success": False, "error": "Text not found"}
            else:
                results = toolkit.ocr.read_text(image)
                return {
                    "success": True,
                    "texts": [
                        {"text": r.text, "confidence": r.confidence}
                        for r in results
                    ]
                }
        return {"success": False, "error": "Could not capture screen"}

    # Status tools
    elif name == "get_status":
        is_connected = toolkit.is_connected()
        is_paper = toolkit._verify_paper_trading() if is_connected else None

        return {
            "success": True,
            "connected": is_connected,
            "paper_trading": is_paper,
            "tws_path": toolkit.config.tws_path
        }

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {name}"
        }


def _action_result_to_dict(result) -> dict:
    """Convert ActionResult to dict."""
    return {
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "duration": result.duration
    }
