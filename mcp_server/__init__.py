"""
MCP Server for NTWS Automation.

Provides Model Context Protocol server for Claude integration.
Allows Claude to control NTWS terminal via tools.
"""

from .server import create_server, run_server

__all__ = ["create_server", "run_server"]
