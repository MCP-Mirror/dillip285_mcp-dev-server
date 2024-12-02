"""Project template system for MCP Development Server."""
import os
import json
import shutil
from typing import Dict, List, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from ..utils.logging import setup_logging
from ..utils.errors import TemplateError

logger = setup_logging(__name__)

class TemplateManager:
    """Manages project templates."""
    
    def __init__(self):
        self.template_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'resources',
            'templates'
        )
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def list_templates(self) -> List[dict]:
        """List available templates."""
        templates = []
        for template_name in os.listdir(self.template_dir):
            template_path = os.path.join(self.template_dir, template_name)
            if os.path.isdir(template_path):
                # Load template metadata
                meta_path = os.path.join(template_path, 'template.json')
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        metadata = json.load(f)
                        templates.append({
                            "name": template_name,
                            **metadata
                        })
                        
        return templates
        
    async def apply_template(
        self,
        template_name: str,
        target_path: str,
        variables: Optional[Dict] = None
    ) -> None:
        """Apply a template to a target directory."""
        try:
            template_path = os.path.join(self.template_dir, template_name)
            if not os.path.exists(template_path):
                raise TemplateError(f"Template not found: {template_name}")
                
            # Load template configuration
            config_path = os.path.join(template_path, 'template.json')
            if os.path.exists(config_path):
                with open(config_path) as f:
                    template_config = json.load(f)
            else:
                template_config = {}
                
            # Create target directory
            os.makedirs(target_path, exist_ok=True)
            
            # Copy template files
            for root, _, files in os.walk(os.path.join(template_path, 'files')):
                rel_path = os.path.relpath(root, os.path.join(template_path, 'files'))
                target_dir = os.path.join(target_path, rel_path)
                os.makedirs(target_dir, exist_ok=True)
                
                for file in files:
                    if file.endswith('.j2'):  # Jinja2 template
                        template = self.env.get_template(
                            os.path.join(template_name, 'files', rel_path, file)
                        )
                        output = template.render(**(variables or {}))
                        
                        # Write rendered template
                        output_file = os.path.join(
                            target_dir,
                            file[:-3]  # Remove .j2 extension
                        )
                        with open(output_file, 'w') as f:
                            f.write(output)
                    else:
                        # Copy regular file
                        src = os.path.join(root, file)
                        dst = os.path.join(target_dir, file)
                        shutil.copy2(src, dst)
                        
            # Run post-template hooks if defined
            await self._run_hooks(
                template_config.get('hooks', {}),
                target_path,
                variables or {}
            )
            
            logger.info(f"Applied template {template_name} to {target_path}")
            
        except Exception as e:
            raise TemplateError(f"Failed to apply template: {str(e)}")
            
    async def _run_hooks(
        self,
        hooks: Dict,
        target_path: str,
        variables: Dict
    ) -> None:
        """Run template hooks."""
        try:
            if post_create := hooks.get('post-create'):
                if isinstance(post_create, list):
                    for cmd in post_create:
                        # Template the command
                        cmd_template = self.env.from_string(cmd)
                        command = cmd_template.render(**variables)
                        
                        # Execute command
                        import subprocess
                        subprocess.run(
                            command,
                            shell=True,
                            check=True,
                            cwd=target_path
                        )
                        
        except Exception as e:
            raise TemplateError(f"Failed to run template hooks: {str(e)}")
            
    def get_template_variables(self, template_name: str) -> Dict:
        """Get required variables for a template."""
        template_path = os.path.join(self.template_dir, template_name)
        if not os.path.exists(template_path):
            raise TemplateError(f"Template not found: {template_name}")
            
        config_path = os.path.join(template_path, 'template.json')
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
                return config.get('variables', {})
                
        return {}