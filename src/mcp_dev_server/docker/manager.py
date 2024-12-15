"""Docker integration for MCP Development Server."""
import asyncio
import docker
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import yaml
import jinja2

from ..utils.logging import setup_logging
from ..utils.errors import MCPDevServerError

logger = setup_logging(__name__)

class DockerManager:
    """Manages Docker containers and environments."""
    
    def __init__(self):
        """Initialize Docker manager."""
        self.client = docker.from_env()
        self.active_containers: Dict[str, Any] = {}
        self._setup_template_environment()
        
    def _setup_template_environment(self):
        """Set up Jinja2 template environment."""
        template_dir = Path(__file__).parent / "templates"
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=jinja2.select_autoescape()
        )
        
    async def create_environment(
        self,
        name: str,
        image: str,
        project_path: str,
        env_vars: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """Create a new Docker environment.
        
        Args:
            name: Environment name
            image: Docker image name
            project_path: Project directory path
            env_vars: Environment variables
            ports: Port mappings
            volumes: Additional volume mappings
            
        Returns:
            str: Environment ID
        """
        try:
            # Ensure image is available
            try:
                self.client.images.get(image)
            except docker.errors.ImageNotFound:
                logger.info(f"Pulling image: {image}")
                self.client.images.pull(image)
                
            # Setup default volumes
            container_volumes = {
                project_path: {
                    "bind": "/workspace",
                    "mode": "rw"
                }
            }
            if volumes:
                container_volumes.update(volumes)
                
            # Create container
            container = self.client.containers.run(
                image=image,
                name=f"mcp-env-{name}",
                detach=True,
                volumes=container_volumes,
                environment=env_vars or {},
                ports=ports or {},
                working_dir="/workspace",
                remove=True
            )
            
            env_id = container.id
            self.active_containers[env_id] = {
                "name": name,
                "container": container,
                "status": "running"
            }
            
            logger.info(f"Created environment: {name} ({env_id})")
            return env_id
            
        except Exception as e:
            logger.error(f"Failed to create environment: {str(e)}")
            raise MCPDevServerError(f"Environment creation failed: {str(e)}")
            
    async def generate_dockerfile(
        self,
        template: str,
        variables: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Generate Dockerfile from template.
        
        Args:
            template: Template name
            variables: Template variables
            output_path: Optional path to save Dockerfile
            
        Returns:
            str: Generated Dockerfile content
        """
        try:
            template = self.template_env.get_template(f"{template}.dockerfile")
            content = template.render(**variables)
            
            if output_path:
                with open(output_path, "w") as f:
                    f.write(content)
                    
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate Dockerfile: {str(e)}")
            raise MCPDevServerError(f"Dockerfile generation failed: {str(e)}")
            
    async def create_compose_config(
        self,
        name: str,
        services: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Create Docker Compose configuration.
        
        Args:
            name: Project name
            services: Service configurations
            output_path: Optional path to save docker-compose.yml
            
        Returns:
            str: Generated docker-compose.yml content
        """
        try:
            compose_config = {
                "version": "3.8",
                "services": services,
                "networks": {
                    "mcp-network": {
                        "driver": "bridge"
                    }
                }
            }
            
            content = yaml.dump(compose_config, default_flow_style=False)
            
            if output_path:
                with open(output_path, "w") as f:
                    f.write(content)
                    
            return content
            
        except Exception as e:
            logger.error(f"Failed to create Docker Compose config: {str(e)}")
            raise MCPDevServerError(f"Compose config creation failed: {str(e)}")
            
    async def execute_command(
        self,
        env_id: str,
        command: str,
        workdir: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Execute command in Docker environment.
        
        Args:
            env_id: Environment ID
            command: Command to execute
            workdir: Working directory
            stream: Stream output in real-time
            
        Returns:
            Dict[str, Any]: Command execution results
        """
        try:
            if env_id not in self.active_containers:
                raise MCPDevServerError(f"Environment not found: {env_id}")
                
            container = self.active_containers[env_id]["container"]
            exec_result = container.exec_run(
                command,
                workdir=workdir or "/workspace",
                stream=True
            )
            
            if stream:
                output = []
                for line in exec_result.output:
                    decoded_line = line.decode().strip()
                    output.append(decoded_line)
                    yield decoded_line
                    
                return {
                    "exit_code": exec_result.exit_code,
                    "output": output
                }
            else:
                output = []
                for line in exec_result.output:
                    output.append(line.decode().strip())
                    
                return {
                    "exit_code": exec_result.exit_code,
                    "output": output
                }
                
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise MCPDevServerError(f"Command execution failed: {str(e)}")
            
    async def cleanup(self):
        """Clean up Docker resources."""
        try:
            for env_id in list(self.active_containers.keys()):
                await self.destroy_environment(env_id)
                
        except Exception as e:
            logger.error(f"Docker cleanup failed: {str(e)}")
            raise MCPDevServerError(f"Docker cleanup failed: {str(e)}")
            
    def get_logs(self, env_id: str, tail: Optional[int] = None) -> str:
        """Get container logs.
        
        Args:
            env_id: Environment ID
            tail: Number of lines to return from the end
            
        Returns:
            str: Container logs
        """
        try:
            if env_id not in self.active_containers:
                raise MCPDevServerError(f"Environment not found: {env_id}")
                
            container = self.active_containers[env_id]["container"]
            return container.logs(tail=tail).decode()
            
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}")
            raise MCPDevServerError(f"Log retrieval failed: {str(e)}")
