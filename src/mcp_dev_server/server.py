"""MCP Development Server implementation."""
from typing import Dict, Any, Optional, Sequence
import logging
import sys
import json

# Import MCP components
from mcp.server import Server as MCPServer
from mcp.server.stdio import stdio_server
import mcp.types as types

from .models import Config, InputResponse, MCPDevServerError
from .managers import (
    ProjectManager, 
    TemplateManager,
    BuildManager,
    DependencyManager,
    TestManager,
    WorkflowManager
)
from .handlers import InputRequestHandler

# Configure logging to stderr to keep stdout clean
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for development

class MCPDevServer:
    """MCP Development Server implementation."""
    
    def __init__(self):
        """Initialize the MCP Development Server."""
        logger.info("Initializing MCP Development Server")
        
        try:
            # Initialize server
            self.server = MCPServer("mcp-dev-server")
            
            # Initialize configuration
            self.config = Config()
            
            # Initialize all managers
            self.project_manager = ProjectManager(self.config)
            self.template_manager = TemplateManager()
            self.build_manager = BuildManager()
            self.dependency_manager = DependencyManager()
            self.test_manager = TestManager()
            self.workflow_manager = WorkflowManager()
            self.input_handler = InputRequestHandler()
            
            # Setup request handlers
            self._setup_resource_handlers()
            self._setup_tool_handlers()
            self._setup_prompt_handlers()
            
            logger.info("Server initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise

    def _setup_resource_handlers(self):
        """Set up resource request handlers."""
        @self.server.list_resources()
        async def list_resources() -> list[types.Resource]:
            """List available resources."""
            logger.debug("Listing resources")
            return []

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content."""
            logger.debug(f"Reading resource: {uri}")
            return ""

    def _setup_tool_handlers(self):
        """Set up tool request handlers."""
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools."""
            logger.debug("Listing tools")
            return []

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
            """Execute a tool."""
            logger.debug(f"Calling tool {name} with arguments {arguments}")
            return [types.TextContent(type="text", text="Tool execution result")]

    def _setup_prompt_handlers(self):
        """Set up prompt request handlers."""
        @self.server.list_prompts()
        async def list_prompts() -> list[types.Prompt]:
            """List available prompts."""
            logger.debug("Listing prompts")
            return []

    async def run(self):
        """Run the MCP Development Server."""
        try:
            logger.info(f"Starting {self.server.name}...")
            
            # Use stdio transport
            async with stdio_server() as streams:
                logger.info("Using stdio transport")
                await self.server.run(
                    streams[0],  # read stream
                    streams[1],  # write stream
                    self.server.create_initialization_options(),
                    raise_exceptions=True  # Enable for debugging
                )
                
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise MCPDevServerError(f"Server error: {str(e)}")

        finally:
            logger.info("Server shutdown")
