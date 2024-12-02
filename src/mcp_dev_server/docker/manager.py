import asyncio
import docker
from docker.errors import DockerException
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..utils.logging import setup_logging
from ..utils.errors import DockerError
from .streams import EnhancedOutputStreamManager
from .streams import BiDirectionalSync

logger = setup_logging(__name__)

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}
        # Update to use enhanced versions
        self.output_manager = EnhancedOutputStreamManager(self)
        self.file_sync = BiDirectionalSync(self)
        
    async def create_container(
        self,
        project_path: str,
        environment: str,
        dockerfile: Optional[str] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """Create and start a Docker container."""
        try:
            # Build image if Dockerfile provided
            if dockerfile:
                image, _ = self.client.images.build(
                    path=project_path,
                    dockerfile=dockerfile,
                    tag=f"mcp-dev-{environment}"
                )
            else:
                image = f"mcp-dev-{environment}"
            
            # Create container
            container = self.client.containers.run(
                image,
                name=f"mcp-dev-{environment}",
                detach=True,
                ports=ports or {},
                volumes=volumes or {},
                environment=environment_vars or {},
                remove=True  # Auto-remove when stopped
            )
            
            # Store container reference
            self.containers[environment] = container
            
            logger.info(f"Created container for environment: {environment}")
            return container.id
            
        except DockerException as e:
            raise DockerError(f"Failed to create container: {str(e)}")
            
    async def stop_container(self, environment: str) -> None:
        """Stop a running container."""
        try:
            if container := self.containers.get(environment):
                container.stop()
                del self.containers[environment]
                logger.info(f"Stopped container for environment: {environment}")
            
        except DockerException as e:
            raise DockerError(f"Failed to stop container: {str(e)}")
            
    async def execute_command(
        self,
        environment: str,
        command: str,
        workdir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command in a container."""
        try:
            if container := self.containers.get(environment):
                exec_result = container.exec_run(
                    command,
                    workdir=workdir,
                    demux=True
                )
                
                return {
                    "exit_code": exec_result.exit_code,
                    "output": exec_result.output[0].decode() if exec_result.output[0] else "",
                    "error": exec_result.output[1].decode() if exec_result.output[1] else ""
                }
            else:
                raise DockerError(f"Container not found: {environment}")
                
        except DockerException as e:
            raise DockerError(f"Failed to execute command: {str(e)}")
            
    async def get_container_status(self, environment: str) -> Dict[str, Any]:
        """Get container status and stats."""
        try:
            if container := self.containers.get(environment):
                stats = container.stats(stream=False)
                return {
                    "id": container.id,
                    "status": container.status,
                    "state": container.attrs['State'],
                    "stats": {
                        "cpu_usage": stats['cpu_stats']['cpu_usage']['total_usage'],
                        "memory_usage": stats['memory_stats']['usage'],
                        "network_rx": stats['networks']['eth0']['rx_bytes'],
                        "network_tx": stats['networks']['eth0']['tx_bytes']
                    }
                }
            else:
                raise DockerError(f"Container not found: {environment}")
                
        except DockerException as e:
            raise DockerError(f"Failed to get container status: {str(e)}")
            
    async def cleanup(self) -> None:
        """Stop all containers and cleanup resources."""
        try:
            for environment, container in self.containers.items():
                try:
                    container.stop()
                    logger.info(f"Stopped container: {environment}")
                except Exception as e:
                    logger.error(f"Error stopping container {environment}: {str(e)}")
                    
            self.containers.clear()
            
        except Exception as e:
            logger.error(f"Error during Docker cleanup: {str(e)}")