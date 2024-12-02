"""Environment management for MCP Development Server."""
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..docker.manager import DockerManager
from ..docker.volumes import VolumeManager
from ..docker.templates import DockerTemplates
from ..utils.logging import setup_logging
from ..utils.errors import EnvironmentError

logger = setup_logging(__name__)

class EnvironmentManager:
    """Manages development environments."""
    
    def __init__(self):
        self.docker_manager = DockerManager()
        self.volume_manager = VolumeManager()
        self.environments: Dict[str, Dict[str, Any]] = {}
        
    async def create_environment(
        self,
        name: str,
        project_path: str,
        env_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new development environment."""
        try:
            config = config or {}
            
            # Create environment directory
            env_path = os.path.join(project_path, '.mcp', 'environments', name)
            os.makedirs(env_path, exist_ok=True)
            
            # Generate Dockerfile
            dockerfile_content = DockerTemplates.get_template(env_type, config)
            dockerfile_path = os.path.join(env_path, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Create volumes for persistence
            volumes = {}
            for volume_name in ['src', 'deps', 'cache']:
                volume = await self.volume_manager.create_volume(
                    f"mcp-{name}-{volume_name}",
                    labels={
                        'mcp.environment': name,
                        'mcp.volume.type': volume_name
                    }
                )
                volumes[volume] = {'bind': f'/app/{volume_name}', 'mode': 'rw'}
            
            # Create container
            container_id = await self.docker_manager.create_container(
                project_path=project_path,
                environment=name,
                dockerfile=dockerfile_path,
                volumes=volumes,
                environment_vars=config.get('env_vars'),
                ports=config.get('ports')
            )
            
            # Store environment configuration
            self.environments[name] = {
                'id': container_id,
                'type': env_type,
                'path': env_path,
                'config': config,
                'volumes': volumes
            }
            
            # Save environment metadata
            self._save_environment_metadata(name)
            
            logger.info(f"Created environment: {name}")
            return container_id
            
        except Exception as e:
            raise EnvironmentError(f"Failed to create environment: {str(e)}")
            
    async def remove_environment(self, name: str) -> None:
        """Remove a development environment."""
        try:
            if env := self.environments.get(name):
                # Stop container
                await self.docker_manager.stop_container(name)
                
                # Remove volumes
                for volume in env['volumes']:
                    await self.volume_manager.remove_volume(volume)
                
                # Remove environment directory
                import shutil
                shutil.rmtree(env['path'])
                
                # Remove from environments dict
                del self.environments[name]
                
                logger.info(f"Removed environment: {name}")
            else:
                raise EnvironmentError(f"Environment not found: {name}")
                
        except Exception as e:
            raise EnvironmentError(f"Failed to remove environment: {str(e)}")
            
    async def execute_in_environment(
        self,
        name: str,
        command: str,
        workdir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command in an environment."""
        try:
            if name not in self.environments:
                raise EnvironmentError(f"Environment not found: {name}")
                
            return await self.docker_manager.execute_command(
                environment=name,
                command=command,
                workdir=workdir
            )
            
        except Exception as e:
            raise EnvironmentError(f"Failed to execute command: {str(e)}")
            
    async def get_environment_status(self, name: str) -> Dict[str, Any]:
        """Get environment status including container and volumes."""
        try:
            if env := self.environments.get(name):
                container_status = await self.docker_manager.get_container_status(name)
                
                volumes_status = {}
                for volume in env['volumes']:
                    volumes_status[volume] = await self.volume_manager.get_volume_info(volume)
                
                return {
                    'container': container_status,
                    'volumes': volumes_status,
                    'type': env['type'],
                    'config': env['config']
                }
            else:
                raise EnvironmentError(f"Environment not found: {name}")
                
        except Exception as e:
            raise EnvironmentError(f"Failed to get environment status: {str(e)}")
            
    def _save_environment_metadata(self, name: str) -> None:
        """Save environment metadata to disk."""
        if env := self.environments.get(name):
            metadata_path = os.path.join(env['path'], 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    'name': name,
                    'type': env['type'],
                    'config': env['config'],
                    'volumes': list(env['volumes'].keys())
                }, f, indent=2)
                
    async def cleanup(self) -> None:
        """Clean up all environments."""
        for name in list(self.environments.keys()):
            try:
                await self.remove_environment(name)
            except Exception as e:
                logger.error(f"Error cleaning up environment {name}: {str(e)}")
