"""Core MCP server implementation."""
import asyncio
from typing import Dict, List, Optional, Any

from mcp.server import Server
from mcp.types import (
    Resource, Tool, Prompt, PromptArgument, TextContent,
    PromptMessage, GetPromptResult
)
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

from mcp_dev_server.package.manager import PackageManager

from .project_manager.manager import ProjectManager
from .project_manager.templates import TemplateManager
from .utils.config import Config
from .utils.logging import setup_logging
from .utils.errors import MCPDevServerError

logger = setup_logging(__name__)

class MCPDevServer:
    """MCP Development Server implementation."""
    
    def __init__(self):
        # Initialize server with just the name
        self.server = Server("mcp-dev-server")
        
        # Initialize managers
        self.config = Config()
        self.project_manager = ProjectManager(self.config)
        self.template_manager = TemplateManager()
        
        # Setup request handlers
        self._setup_resource_handlers()
        self._setup_tool_handlers()
        self._setup_prompt_handlers()

    def _setup_resource_handlers(self):
        """Set up resource-related request handlers."""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available project resources."""
            resources = []
            
            if project := self.project_manager.current_project:
                # Project structure
                resources.append(Resource(
                    uri=f"project://{project.id}/structure",
                    name="Project Structure",
                    description="Current project file structure",
                    mimeType="application/json"
                ))
                
                # Git status if enabled
                if project.state.git_initialized:
                    resources.append(Resource(
                        uri=f"project://{project.id}/git/status",
                        name="Git Status",
                        description="Current Git repository status",
                        mimeType="application/json"
                    ))
                
            return resources
            
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource."""
            if not uri.startswith("project://"):
                raise MCPDevServerError(f"Unsupported URI scheme: {uri}")
                
            parts = uri.replace("project://", "").strip("/").split("/")
            if len(parts) < 2:
                raise MCPDevServerError(f"Invalid project URI: {uri}")
                
            project_id, resource_type = parts[0], parts[1]
            
            if project := self.project_manager.get_project(project_id):
                if resource_type == "structure":
                    return project.get_structure()
                elif resource_type == "git/status":
                    # Implement Git status resource
                    pass
                else:
                    raise MCPDevServerError(f"Unknown resource type: {resource_type}")
            else:
                raise MCPDevServerError(f"Project not found: {project_id}")
                
    def _setup_tool_handlers(self):
        """Set up tool-related request handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available development tools."""
            return [
                Tool(
                    name="create-project",
                    description="Create a new development project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "template": {"type": "string"},
                            "path": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="load-project",
                    description="Load an existing project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="git-commit",
                    description="Create a Git commit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "files": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                name="build",
                description="Start a build process",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "environment": {"type": "string"},
                        "command": {"type": "string"},
                        "workdir": {"type": "string"}
                    },
                    "required": ["environment"]
                }
            ),
            Tool(
                name="install-dependencies",
                description="Install project dependencies",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "environment": {"type": "string"},
                        "package_manager": {"type": "string"},
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "dev": {"type": "boolean"}
                    },
                    "required": ["environment", "package_manager", "dependencies"]
                }
            ),
            Tool(
                name="run-tests",
                description="Run test suite",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "environment": {"type": "string"},
                        "command": {"type": "string"},
                        "workdir": {"type": "string"},
                        "format": {"type": "string"}
                    },
                    "required": ["environment"]
                }
            ),
            Tool(
                name="start-workflow",
                description="Start a predefined workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow": {"type": "string"},
                        "config": {"type": "object"}
                    },
                    "required": ["workflow"]
                }
            )
            ]
            
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool execution requests."""
            try:
                if name == "create-project":
                    project = await self.project_manager.create_project(
                        name=arguments["name"],
                        template=arguments.get("template", "basic"),
                        path=arguments.get("path"),
                        description=arguments.get("description", "")
                    )
                    return [TextContent(
                        type="text",
                        text=f"Created project {project.config.name} at {project.path}"
                    )]
                    
                elif name == "load-project":
                    project = await self.project_manager.load_project(
                        arguments["path"]
                    )
                    return [TextContent(
                        type="text",
                        text=f"Loaded project {project.config.name} from {project.path}"
                    )]
                    
                elif name == "git-commit":
                    if project := self.project_manager.current_project:
                        if not project.state.git_initialized:
                            return [TextContent(
                                type="text",
                                text="Git is not initialized for this project",
                                isError=True
                            )]
                            
                        # Implement Git commit
                        pass
                    else:
                        return [TextContent(
                            type="text",
                            text="No active project",
                            isError=True
                        )]
                        
                elif name == "build":
                    build_id = await self.build_manager.start_build(
                    arguments["environment"],
                    arguments
                    )
                    return [TextContent(
                        type="text",
                        text=f"Started build {build_id}"
                    )]
                
                elif name == "install-dependencies":
                    result = await self.dependency_manager.install_dependencies(
                    arguments["environment"],
                    PackageManager(arguments["package_manager"]),
                    arguments["dependencies"],
                    arguments.get("dev", False)
                )
                    return [TextContent(
                        type="text",
                        text="Dependencies installed successfully" if result["success"]
                        else f"Failed to install dependencies: {result['error']}"
                    )]
                
                elif name == "run-tests":
                    test_id = await self.test_manager.run_tests(
                    arguments["environment"],
                    arguments
                )
                    return [TextContent(
                        type="text",
                        text=f"Started test run {test_id}"
                    )]
                
                elif name == "start-workflow":
                    if workflow_template := self.workflow_manager.get_common_workflows().get(arguments["workflow"]):
                        workflow_id = await self.workflow_manager.create_workflow(
                            workflow_template,
                            arguments.get("config")
                        )
                        await self.workflow_manager.start_workflow(workflow_id)
                        return [TextContent(
                            type="text",
                            text=f"Started workflow {workflow_id}"
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"Unknown workflow: {arguments['workflow']}",
                            isError=True
                        )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}",
                        isError=True
                    )]    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}",
                    isError=True
                )]
                
    def _setup_prompt_handlers(self):
        """Set up prompt-related request handlers."""
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts."""
            return [
                Prompt(
                    name="analyze-project",
                    description="Analyze current project structure and state",
                    arguments=[
                        PromptArgument(
                            name="focus",
                            description="Analysis focus (structure/dependencies/git)",
                            required=False
                        )
                    ]
                )
            ]
            
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> GetPromptResult:
            """Generate prompts based on current project state."""
            if name == "analyze-project":
                if project := self.project_manager.current_project:
                    focus = arguments.get("focus", "structure") if arguments else "structure"
                    
                    if focus == "structure":
                        structure = project.get_structure()
                        return GetPromptResult(
                            messages=[
                                PromptMessage(
                                    role="user",
                                    content=TextContent(
                                        type="text",
                                        text=f"Analyze this project structure and suggest improvements:\n\n{structure}"
                                    )
                                )
                            ]
                        )
                else:
                    raise MCPDevServerError("No active project")
            else:
                raise MCPDevServerError(f"Unknown prompt: {name}")
                
    async def run(self):
        """Run the MCP server."""
        try:
            from mcp.server.stdio import stdio_server
            
            async with stdio_server() as (read_stream, write_stream):
                init_options = InitializationOptions(
                    server_name="mcp-dev-server",
                    server_version="0.1.0",
                    capabilities={
                        "resources": {},
                        "tools": {},
                        "prompts": {}
                    }
                )
                
                await self.server.run(
                    read_stream,
                    write_stream,
                    init_options
                )
                
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise
            
    async def cleanup(self):
        """Clean up server resources."""
        try:
            await self.project_manager.cleanup()
            logger.info("Server cleanup completed")
        except Exception as e:
            logger.error(f"Error during server cleanup: {str(e)}")

def main():
    """Entry point for the server."""
    server = MCPDevServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        asyncio.run(server.cleanup())
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

if __name__ == "__main__":
    main()