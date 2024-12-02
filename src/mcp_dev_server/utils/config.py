"""Configuration management for the MCP Development Server."""
import os
import json
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from .logging import setup_logging
from .errors import ConfigurationError

logger = setup_logging(__name__)

class ProjectConfig(BaseModel):
    """Project configuration model."""
    name: str
    path: Path
    template: str = Field(default="basic")
    git_enabled: bool = Field(default=True)
    docker_config: Dict[str, Any] = Field(default_factory=dict)
    build_config: Dict[str, Any] = Field(default_factory=dict)
    test_config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {
        "production": {},
        "development": {}
    })

    class Config:
        arbitrary_types_allowed = True

class ServerConfig(BaseModel):
    """Server configuration model."""
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    workspace_dir: Path = Field(default=Path.home() / ".mcp-dev-server")
    max_projects: int = Field(default=10)

class Config:
    """Configuration manager."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._default_config_path()
        self.server_config = ServerConfig()
        self._load_config()
        
    @staticmethod
    def _default_config_path() -> str:
        """Get default configuration path."""
        config_dir = os.path.expanduser("~/.config/mcp-dev-server")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")
        
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path) as f:
                    config_data = json.load(f)
                self.server_config = ServerConfig(**config_data)
                logger.info("Loaded configuration from %s", self.config_path)
            else:
                self._save_config()
                logger.info("Created default configuration at %s", self.config_path)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
            
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(
                    self.server_config.dict(),
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
            
    def update_server_config(self, **kwargs) -> None:
        """Update server configuration."""
        try:
            # Update only provided fields
            for key, value in kwargs.items():
                if hasattr(self.server_config, key):
                    setattr(self.server_config, key, value)
            self._save_config()
        except Exception as e:
            raise ConfigurationError(f"Failed to update configuration: {str(e)}")

    @staticmethod
    def create_project_config(**kwargs) -> ProjectConfig:
        """Create a new project configuration."""
        try:
            return ProjectConfig(**kwargs)
        except Exception as e:
            raise ConfigurationError(f"Failed to create project configuration: {str(e)}")