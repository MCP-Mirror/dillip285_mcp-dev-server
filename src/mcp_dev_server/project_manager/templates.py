"""Template system for project creation."""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import jinja2
import yaml

from ..utils.logging import setup_logging
from ..utils.errors import ProjectError

logger = setup_logging(__name__)

class TemplateManager:
    """Manages project templates."""
    
    def __init__(self):
        """Initialize template manager."""
        self.template_dir = self._get_template_dir()
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape()
        )
        
    def _get_template_dir(self) -> Path:
        """Get templates directory path."""
        if os.name == "nt":  # Windows
            template_dir = Path(os.getenv("APPDATA")) / "Claude" / "templates"
        else:  # macOS/Linux
            template_dir = Path.home() / ".config" / "claude" / "templates"
            
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize with basic template if empty
        if not any(template_dir.iterdir()):
            self._initialize_basic_template(template_dir)
            
        return template_dir
        
    def _initialize_basic_template(self, template_dir: Path):
        """Initialize basic project template.
        
        Args:
            template_dir: Templates directory path
        """
        basic_dir = template_dir / "basic"
        basic_dir.mkdir(exist_ok=True)
        
        # Create template configuration
        config = {
            "name": "basic",
            "description": "Basic project template",
            "version": "1.0.0",
            "files": [
                "README.md",
                "requirements.txt",
                ".gitignore",
                "src/__init__.py",
                "tests/__init__.py"
            ],
            "variables": {
                "project_name": "",
                "description": ""
            },
            "features": {
                "git": True,
                "tests": True,
                "docker": False
            }
        }
        
        with open(basic_dir / "template.yaml", "w") as f:
            yaml.dump(config, f)
            
        # Create template files
        readme_content = """# {{ project_name }}

{{ description }}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from {{ project_name.lower() }} import main
```

## Testing

```bash
pytest tests/
```
"""
        
        with open(basic_dir / "README.md", "w") as f:
            f.write(readme_content)
            
        # Create source directory
        src_dir = basic_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        with open(src_dir / "__init__.py", "w") as f:
            f.write('"""{{ project_name }} package."""\n')
            
        # Create tests directory
        tests_dir = basic_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        with open(tests_dir / "__init__.py", "w") as f:
            f.write('"""Tests for {{ project_name }}."""\n')
            
        # Create requirements.txt
        with open(basic_dir / "requirements.txt", "w") as f:
            f.write("pytest>=7.0.0\n")
            
        # Create .gitignore
        gitignore_content = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
"""
        
        with open(basic_dir / ".gitignore", "w") as f:
            f.write(gitignore_content)
            
    async def apply_template(self, template_name: str, project: Any) -> None:
        """Apply template to project.
        
        Args:
            template_name: Name of template to apply
            project: Project instance
        """
        try:
            template_path = self.template_dir / template_name
            if not template_path.exists():
                raise ProjectError(f"Template not found: {template_name}")
                
            # Load template configuration
            with open(template_path / "template.yaml", "r") as f:
                template_config = yaml.safe_load(f)
                
            # Prepare template variables
            variables = {
                "project_name": project.config.name,
                "description": project.config.description
            }
            
            # Process each template file
            for file_path in template_config["files"]:
                template_file = template_path / file_path
                if template_file.exists():
                    # Create target directory if needed
                    target_path = Path(project.path) / file_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Render template content
                    template = self.env.get_template(f"{template_name}/{file_path}")
                    content = template.render(**variables)
                    
                    # Write rendered content
                    with open(target_path, "w") as f:
                        f.write(content)
                        
            logger.info(f"Applied template {template_name} to project {project.config.name}")
            
        except Exception as e:
            logger.error(f"Failed to apply template: {str(e)}")
            raise ProjectError(f"Template application failed: {str(e)}")
            
    async def template_has_git(self, template_name: str) -> bool:
        """Check if template includes Git initialization.
        
        Args:
            template_name: Template name
            
        Returns:
            bool: True if template includes Git
        """
        try:
            template_path = self.template_dir / template_name
            if not template_path.exists():
                return False
                
            # Load template configuration
            with open(template_path / "template.yaml", "r") as f:
                template_config = yaml.safe_load(f)
                
            return template_config.get("features", {}).get("git", False)
            
        except Exception:
            return False
            
    def list_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates.
        
        Returns:
            List[Dict[str, Any]]: Template information
        """
        templates = []
        
        for template_dir in self.template_dir.iterdir():
            if template_dir.is_dir():
                config_path = template_dir / "template.yaml"
                if config_path.exists():
                    with open(config_path, "r") as f:
                        config = yaml.safe_load(f)
                        templates.append(config)
                        
        return templates