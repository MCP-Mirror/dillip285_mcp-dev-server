"""Project management for MCP Development Server."""
import os
from typing import Dict, List, Optional
from pathlib import Path

from ..utils.config import ProjectConfig, Config
from ..utils.logging import setup_logging
from ..utils.errors import ProjectError, ProjectNotFoundError
from .context import ProjectContext
from .git import GitManager

logger = setup_logging(__name__)

class ProjectManager:
    """Manages multiple development projects."""
    
    def __init__(self, server_config: Optional[Config] = None):
        self.config = server_config or Config()
        self.projects: Dict[str, ProjectContext] = {}
        self.current_project: Optional[ProjectContext] = None
        self._setup_workspace()
        
    def _setup_workspace(self) -> None:
        """Set up workspace directory."""
        os.makedirs(self.config.server_config.workspace_dir, exist_ok=True)
        
    async def create_project(
        self,
        name: str,
        template: str = "basic",
        path: Optional[str] = None,
        **kwargs
    ) -> ProjectContext:
        """Create a new project."""
        try:
            # Generate project path if not provided
            if not path:
                path = os.path.join(
                    self.config.server_config.workspace_dir,
                    name
                )
            
            # Create project config
            project_config = ProjectConfig(
                name=name,
                path=Path(path),
                template=template,
                **kwargs
            )
            
            # Create project context
            project = ProjectContext(project_config)
            
            # Initialize project
            await project.initialize()
            # Initialize Git if enabled
            if project_config.git_enabled:
                git_manager = GitManager(path)
                await git_manager.initialize()
                await project.update_state(git_initialized=True)
            
            # Store project
            self.projects[project.id] = project
            self.current_project = project
            
            logger.info(f"Created project {name} at {path}")
            return project
            
        except Exception as e:
            raise ProjectError(f"Failed to create project: {str(e)}")
            
    async def load_project(self, path: str) -> ProjectContext:
        """Load an existing project."""
        try:
            # Verify project path exists
            if not os.path.exists(path):
                raise ProjectNotFoundError(f"Project path does not exist: {path}")
                
            # Load project config
            config_path = os.path.join(path, '.mcp', 'project.json')
            if not os.path.exists(config_path):
                raise ProjectNotFoundError(
                    f"Project configuration not found: {config_path}"
                )
                
            # Create project context
            project_config = ProjectConfig.parse_file(config_path)
            project = ProjectContext(project_config)
            
            # Store project
            self.projects[project.id] = project
            self.current_project = project
            
            logger.info(f"Loaded project from {path}")
            return project
            
        except Exception as e:
            raise ProjectError(f"Failed to load project: {str(e)}")
            
    def get_project(self, project_id: str) -> Optional[ProjectContext]:
        """Get project by ID."""
        return self.projects.get(project_id)
        
    def list_projects(self) -> List[dict]:
        """List all projects."""
        return [
            {
                "id": project_id,
                "name": project.config.name,
                "path": str(project.path),
                "template": project.config.template,
                "initialized": project.state.initialized
            }
            for project_id, project in self.projects.items()
        ]
        
    async def set_current_project(self, project_id: str) -> None:
        """Set the current active project."""
        if project := self.get_project(project_id):
            self.current_project = project
            logger.info(f"Set current project to {project.config.name}")
        else:
            raise ProjectNotFoundError(f"Project not found: {project_id}")
            
    async def delete_project(self, project_id: str, delete_files: bool = False) -> None:
        """Delete a project."""
        try:
            if project := self.get_project(project_id):
                # Clean up project resources
                await project.cleanup()
                
                # Remove from projects dict
                del self.projects[project_id]
                
                # Clear current project if it was this one
                if self.current_project and self.current_project.id == project_id:
                    self.current_project = None
                    
                # Optionally delete project files
                if delete_files and os.path.exists(project.path):
                    import shutil
                    shutil.rmtree(project.path)
                    
                logger.info(f"Deleted project {project.config.name}")
            else:
                raise ProjectNotFoundError(f"Project not found: {project_id}")
                
        except Exception as e:
            raise ProjectError(f"Failed to delete project: {str(e)}")
            
    async def cleanup(self) -> None:
        """Clean up all project resources."""
        try:
            for project in self.projects.values():
                await project.cleanup()
                
            self.projects.clear()
            self.current_project = None
            
            logger.info("Cleaned up all projects")
            
        except Exception as e:
            logger.error(f"Error during project cleanup: {str(e)}")