"""
Entry point for running MCP server as module.

Usage:
    python -m ntws_automation.mcp_server
"""

import logging
from .server import run_server

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_server()
