"""Configuration management for MCP Development Server."""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """Configuration manager."""
    
    def __init__(self):
        """Initialize configuration."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = self._load_config()
        
    def _get_config_dir(self) -> Path:
        """Get configuration directory path."""
        if os.name == "nt":  # Windows
            config_dir = Path(os.getenv("APPDATA")) / "Claude"
        else:  # macOS/Linux
            config_dir = Path.home() / ".config" / "claude"
            
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._get_default_config()
        else:
            config = self._get_default_config()
            self._save_config(config)
            return config
            
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "projectsDir": str(Path.home() / "Projects"),
            "templatesDir": str(self.config_dir / "templates"),
            "environments": {
                "default": {
                    "type": "docker",
                    "image": "python:3.12-slim"
                }
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self._save_config(self.config)
        
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        self.config.update(updates)
        self._save_config(self.config)