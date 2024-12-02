"""MCP Development Server Package."""
from . import server
import asyncio
from typing import Optional
from .utils.logging import setup_logging

logger = setup_logging(__name__)

def main():
    """Main entry point for the package."""
    try:
        server_instance = server.MCPDevServer()
        asyncio.run(server_instance.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

# Expose key components at package level
__all__ = ['main', 'server']