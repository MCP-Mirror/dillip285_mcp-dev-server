"""Docker volume management for MCP Development Server."""
from typing import Dict, List, Optional
import docker
from docker.errors import DockerException

from ..utils.logging import setup_logging
from ..utils.errors import DockerError

logger = setup_logging(__name__)

class VolumeManager:
    """Manages Docker volumes for development environments."""
    
    def __init__(self):
        self.client = docker.from_env()
        
    async def create_volume(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a Docker volume."""
        try:
            volume = self.client.volumes.create(
                name=name,
                driver='local',
                labels=labels or {}
            )
            logger.info(f"Created volume: {name}")
            return volume.name
            
        except DockerException as e:
            raise DockerError(f"Failed to create volume: {str(e)}")
            
    async def remove_volume(self, name: str) -> None:
        """Remove a Docker volume."""
        try:
            volume = self.client.volumes.get(name)
            volume.remove()
            logger.info(f"Removed volume: {name}")
            
        except DockerException as e:
            raise DockerError(f"Failed to remove volume: {str(e)}")
            
    async def list_volumes(
        self,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """List Docker volumes."""
        try:
            volumes = self.client.volumes.list(filters=filters or {})
            return [
                {
                    "name": v.name,
                    "driver": v.attrs['Driver'],
                    "mountpoint": v.attrs['Mountpoint'],
                    "labels": v.attrs['Labels'] or {}
                }
                for v in volumes
            ]
            
        except DockerException as e:
            raise DockerError(f"Failed to list volumes: {str(e)}")
            
    async def get_volume_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a volume."""
        try:
            volume = self.client.volumes.get(name)
            return {
                "name": volume.name,
                "driver": volume.attrs['Driver'],
                "mountpoint": volume.attrs['Mountpoint'],
                "labels": volume.attrs['Labels'] or {},
                "scope": volume.attrs['Scope'],
                "status": volume.attrs.get('Status', {})
            }
            
        except DockerException as e:
            raise DockerError(f"Failed to get volume info: {str(e)}")
