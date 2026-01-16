"""
MCP Server implementation for TWS Automation.

Provides an MCP server that exposes TWS automation
capabilities as tools that Claude can invoke.

Usage:
    # Run as module
    python -m tws_automation.mcp_server

    # Or programmatically
    from tws_automation.mcp_server import run_server
    run_server()
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global toolkit instance
_toolkit: Optional['TWSToolkit'] = None


def get_toolkit() -> 'TWSToolkit':
    """Get or create global toolkit instance."""
    global _toolkit

    if _toolkit is None:
        from .. import TWSToolkit
        _toolkit = TWSToolkit()

        # Connect to TWS
        if not _toolkit.connect():
            logger.warning("Could not connect to TWS. Some tools may not work.")

    return _toolkit


def create_server():
    """
    Create MCP server with TWS tools.

    Returns:
        MCP Server instance.
    """
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent

        from .tools import get_tools, handle_tool_call

    except ImportError:
        logger.error(
            "MCP package not installed. Install with: pip install mcp"
        )
        raise

    # Create server
    server = Server("tws-automation")

    @server.list_tools()
    async def list_tools():
        """List available TWS tools."""
        return get_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Handle tool calls."""
        toolkit = get_toolkit()
        result = await handle_tool_call(toolkit, name, arguments)

        return [TextContent(
            type="text",
            text=result
        )]

    return server


async def run_server_async():
    """Run MCP server asynchronously."""
    try:
        from mcp.server.stdio import stdio_server
    except ImportError:
        logger.error("MCP package not installed")
        return

    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run_server():
    """Run MCP server (blocking)."""
    logger.info("Starting TWS MCP Server...")
    asyncio.run(run_server_async())


# Entry point for python -m
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server()
