"""
MCP Server for TWS Automation.

Provides Model Context Protocol server for Claude integration.
Allows Claude to control TWS terminal via tools.
"""

from .server import create_server, run_server

__all__ = ["create_server", "run_server"]
