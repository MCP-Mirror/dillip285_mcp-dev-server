"""Package management integration for MCP Development Server."""

from typing import Dict, List, Optional, Any
from enum import Enum
from ..utils.errors import PackageError
from ..utils.logging import setup_logging

logger = setup_logging(__name__)

class PackageManager(str, Enum):
    """Supported package managers."""
    NPM = "npm"
    PIP = "pip"
    CARGO = "cargo"

class DependencyManager:
    """Manages project dependencies."""
    
    def __init__(self, env_manager):
        self.env_manager = env_manager
        
    async def install_dependencies(
        self,
        environment: str,
        package_manager: PackageManager,
        dependencies: List[str],
        dev: bool = False
    ) -> Dict[str, Any]:
        """Install project dependencies."""
        try:
            command = self._build_install_command(
                package_manager,
                dependencies,
                dev
            )
            
            result = await self.env_manager.execute_in_environment(
                environment,
                command
            )
            
            return {
                "success": result["exit_code"] == 0,
                "output": result["output"],
                "error": result.get("error")
            }
            
        except Exception as e:
            raise PackageError(f"Failed to install dependencies: {str(e)}")
            
    async def update_dependencies(
        self,
        environment: str,
        package_manager: PackageManager,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update project dependencies."""
        try:
            command = self._build_update_command(package_manager, dependencies)
            
            result = await self.env_manager.execute_in_environment(
                environment,
                command
            )
            
            return {
                "success": result["exit_code"] == 0,
                "output": result["output"],
                "error": result.get("error")
            }
            
        except Exception as e:
            raise PackageError(f"Failed to update dependencies: {str(e)}")
            
    def _build_install_command(
        self,
        package_manager: PackageManager,
        dependencies: List[str],
        dev: bool
    ) -> str:
        """Build dependency installation command."""
        if package_manager == PackageManager.NPM:
            dev_flag = "--save-dev" if dev else ""
            deps = " ".join(dependencies)
            return f"npm install {dev_flag} {deps}"
            
        elif package_manager == PackageManager.PIP:
            dev_flag = "-D" if dev else ""
            deps = " ".join(dependencies)
            return f"pip install {dev_flag} {deps}"
            
        elif package_manager == PackageManager.CARGO:
            dev_flag = "--dev" if dev else ""
            deps = " ".join(dependencies)
            return f"cargo add {dev_flag} {deps}"
            
        else:
            raise PackageError(f"Unsupported package manager: {package_manager}")
            
    def _build_update_command(
        self,
        package_manager: PackageManager,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Build dependency update command."""
        if package_manager == PackageManager.NPM:
            return "npm update" if not dependencies else f"npm update {' '.join(dependencies)}"
            
        elif package_manager == PackageManager.PIP:
            return "pip install -U -r requirements.txt" if not dependencies else f"pip install -U {' '.join(dependencies)}"
            
        elif package_manager == PackageManager.CARGO:
            return "cargo update" if not dependencies else f"cargo update {' '.join(dependencies)}"
            
        else:
            raise PackageError(f"Unsupported package manager: {package_manager}")
