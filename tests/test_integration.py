"""Test MCP server integration with Claude."""
import asyncio
import pytest
from mcp_dev_server.server import MCPDevServer
from mcp_dev_server.utils.config import Config

@pytest.mark.asyncio
async def test_server_initialization():
    """Test server initialization."""
    config = Config()
    server = MCPDevServer()
    
    # Test project creation
    project = await server.project_manager.create_project(
        name="test-project",
        project_type="python",
        project_config={
            "python_version": "3.12",
            "project_type": "fastapi",
            "dependency_management": "poetry"
        }
    )
    
    assert project is not None
    assert project.config["name"] == "test-project"
    
    # Test tool execution
    result = await server.handle_call_tool("build", {
        "environment": "default",
        "command": "build"
    })
    
    assert result[0].type == "text"
    
    # Cleanup
    await server.cleanup()