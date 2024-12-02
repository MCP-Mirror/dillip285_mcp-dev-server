"""Project context management for MCP Development Server."""
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel
from ..utils.config import ProjectConfig
from ..utils.logging import setup_logging
from ..utils.errors import ProjectError, FileOperationError

logger = setup_logging(__name__)

class ProjectState(BaseModel):
    """Project state tracking."""
    initialized: bool = False
    last_build_time: Optional[datetime] = None
    last_build_status: Optional[str] = None
    last_test_time: Optional[datetime] = None
    last_test_status: Optional[str] = None
    git_initialized: bool = False

class ProjectContext:
    """Manages the context and state of a development project."""
    
    def __init__(self, config: ProjectConfig):
        self.id = str(uuid.uuid4())
        self.config = config
        self.path = config.path
        self.state = ProjectState()
        self._file_watchers: Dict[str, Any] = {}
        
    async def initialize(self) -> None:
        """Initialize project structure and state."""
        try:
            # Create project directory
            os.makedirs(self.path, exist_ok=True)
            
            # Create project structure
            await self._create_project_structure()
            
            # Initialize state file
            await self._init_state_file()
            
            # Set up file watchers
            await self._setup_file_watchers()
            
            self.state.initialized = True
            logger.info(f"Initialized project {self.config.name} at {self.path}")
            
        except Exception as e:
            raise ProjectError(f"Project initialization failed: {str(e)}")
            
    async def _create_project_structure(self) -> None:
        """Create initial project directory structure."""
        try:
            # Create standard directories
            for dir_name in ['.mcp', 'src', 'tests', 'docs']:
                os.makedirs(os.path.join(self.path, dir_name), exist_ok=True)
                
            # Create basic configuration files
            config_path = os.path.join(self.path, '.mcp', 'project.json')
            with open(config_path, 'w') as f:
                json.dump(self.config.dict(), f, indent=2, default=str)
                
        except Exception as e:
            raise FileOperationError(f"Failed to create project structure: {str(e)}")
            
    async def _init_state_file(self) -> None:
        """Initialize project state file."""
        try:
            state_path = os.path.join(self.path, '.mcp', 'state.json')
            with open(state_path, 'w') as f:
                json.dump(self.state.dict(), f, indent=2, default=str)
                
        except Exception as e:
            raise FileOperationError(f"Failed to initialize state file: {str(e)}")
            
    async def _setup_file_watchers(self) -> None:
        """Set up file system watchers for project directories."""
        # To be implemented with file watching functionality
        pass
        
    def get_structure(self) -> Dict[str, Any]:
        """Get project structure as a dictionary."""
        structure = {"name": self.config.name, "type": "directory", "children": []}
        
        def scan_directory(path: Path, current_dict: Dict[str, Any]) -> None:
            try:
                for item in path.iterdir():
                    # Skip hidden files and .mcp directory
                    if item.name.startswith('.'):
                        continue
                        
                    if item.is_file():
                        current_dict["children"].append({
                            "name": item.name,
                            "type": "file",
                            "size": item.stat().st_size
                        })
                    elif item.is_dir():
                        dir_dict = {
                            "name": item.name,
                            "type": "directory",
                            "children": []
                        }
                        current_dict["children"].append(dir_dict)
                        scan_directory(item, dir_dict)
                        
            except Exception as e:
                logger.error(f"Error scanning directory {path}: {str(e)}")
                
        scan_directory(Path(self.path), structure)
        return structure
        
    def get_file_content(self, relative_path: str) -> str:
        """Get content of a project file."""
        try:
            file_path = os.path.join(self.path, relative_path)
            if not os.path.exists(file_path):
                raise FileOperationError(f"File not found: {relative_path}")
                
            # Basic security check
            if not os.path.normpath(file_path).startswith(str(self.path)):
                raise FileOperationError("Invalid file path")
                
            with open(file_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            raise FileOperationError(f"Failed to read file {relative_path}: {str(e)}")
            
    async def update_file(self, relative_path: str, content: str) -> None:
        """Update content of a project file."""
        try:
            file_path = os.path.join(self.path, relative_path)
            
            # Create directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Security check
            if not os.path.normpath(file_path).startswith(str(self.path)):
                raise FileOperationError("Invalid file path")
                
            with open(file_path, 'w') as f:
                f.write(content)
                
            logger.info(f"Updated file: {relative_path}")
            
        except Exception as e:
            raise FileOperationError(f"Failed to update file {relative_path}: {str(e)}")
            
    async def delete_file(self, relative_path: str) -> None:
        """Delete a project file."""
        try:
            file_path = os.path.join(self.path, relative_path)
            
            # Security check
            if not os.path.normpath(file_path).startswith(str(self.path)):
                raise FileOperationError("Invalid file path")
                
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {relative_path}")
            else:
                logger.warning(f"File not found: {relative_path}")
                
        except Exception as e:
            raise FileOperationError(f"Failed to delete file {relative_path}: {str(e)}")
            
    async def update_state(self, **kwargs) -> None:
        """Update project state."""
        try:
            # Update state object
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
                    
            # Save to state file
            state_path = os.path.join(self.path, '.mcp', 'state.json')
            with open(state_path, 'w') as f:
                json.dump(self.state.dict(), f, indent=2, default=str)
                
            logger.info(f"Updated project state: {kwargs}")
            
        except Exception as e:
            raise ProjectError(f"Failed to update project state: {str(e)}")
            
    async def cleanup(self) -> None:
        """Clean up project resources."""
        try:
            # Stop file watchers
            for watcher in self._file_watchers.values():
                await watcher.stop()
                
            logger.info(f"Cleaned up project resources for {self.config.name}")
            
        except Exception as e:
            logger.error(f"Error during project cleanup: {str(e)}")