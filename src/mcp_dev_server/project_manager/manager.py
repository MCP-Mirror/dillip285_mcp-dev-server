"""Project management system for MCP Development Server."""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import git

from .project_types import PROJECT_TYPES, ProjectType, BuildSystem
from .templates import TemplateManager
from ..prompts.project_templates import PROJECT_TEMPLATES
from ..utils.logging import setup_logging
from ..utils.errors import ProjectError
from ..docker.manager import DockerManager

logger = setup_logging(__name__)

class ProjectManager:
    """Manages development projects."""
    
    def __init__(self, config):
        """Initialize project manager.
        
        Args:
            config: Server configuration instance
        """
        self.config = config
        self.template_manager = TemplateManager()
        self.docker_manager = DockerManager()
        self.current_project = None
        self.projects = {}
        
    def get_available_project_types(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available project types.
        
        Returns:
            Dict[str, Dict[str, Any]]: Project type information
        """
        return {
            name: {
                "name": pt.name,
                "description": pt.description,
                "build_systems": [bs.value for bs in pt.build_systems],
                "default_build_system": pt.default_build_system.value
            }
            for name, pt in PROJECT_TYPES.items()
        }
        
    async def create_project(
        self,
        name: str,
        project_type: str,
        project_config: Dict[str, Any],
        path: Optional[str] = None,
        description: str = ""
    ) -> Any:
        """Create a new project.
        
        Args:
            name: Project name
            project_type: Type of project (e.g., java, dotnet, node)
            project_config: Project-specific configuration
            path: Project directory path (optional)
            description: Project description
            
        Returns:
            Project instance
        """
        try:
            if project_type not in PROJECT_TYPES:
                raise ProjectError(f"Unsupported project type: {project_type}")
                
            project_type_info = PROJECT_TYPES[project_type]
            
            # Determine project path
            if not path:
                projects_dir = Path(self.config.get("projectsDir"))
                path = str(projects_dir / name)
                
            project_path = Path(path)
            if project_path.exists():
                raise ProjectError(f"Project path already exists: {path}")
                
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create project configuration
            project_config.update({
                "name": name,
                "type": project_type,
                "description": description,
                "build_system": project_config.get("build_system", 
                    project_type_info.default_build_system.value)
            })
            
            # Save project configuration
            config_path = project_path / "project.json"
            with open(config_path, "w") as f:
                json.dump(project_config, f, indent=2)
                
            # Create project structure
            await self._create_project_structure(project_path, project_type_info)
            
            # Initialize build system
            await self._initialize_build_system(
                project_path, 
                project_type_info, 
                project_config
            )
            
            # Set up Docker environment if requested
            if project_config.get("setup_docker", False):
                await self._setup_docker_environment(
                    project_path,
                    project_type_info,
                    project_config
                )
                
            # Initialize Git repository if requested
            if project_config.get("initialize_git", True):
                repo = git.Repo.init(path)
                repo.index.add("*")
                repo.index.commit("Initial commit")
                
            # Create project instance
            project = await self._create_project_instance(
                path,
                project_config,
                project_type_info
            )
            
            # Store project reference
            self.projects[project.id] = project
            self.current_project = project
            
            logger.info(f"Created {project_type} project: {name} at {path}")
            return project
            
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            raise ProjectError(f"Project creation failed: {str(e)}")
            
    async def _create_project_structure(
        self,
        project_path: Path,
        project_type: ProjectType
    ):
        """Create project directory structure.
        
        Args:
            project_path: Project directory path
            project_type: Project type information
        """
        def create_directory_structure(base_path: Path, structure: Dict[str, Any]):
            for name, content in structure.items():
                path = base_path / name
                if isinstance(content, dict):
                    path.mkdir(exist_ok=True)
                    create_directory_structure(path, content)
                    
        create_directory_structure(project_path, project_type.file_structure)
        
    async def _initialize_build_system(
        self,
        project_path: Path,
        project_type: ProjectType,
        project_config: Dict[str, Any]
    ):
        """Initialize project build system.
        
        Args:
            project_path: Project directory path
            project_type: Project type information
            project_config: Project configuration
        """
        build_system = BuildSystem(project_config["build_system"])
        
        # Generate build system configuration files
        if build_system == BuildSystem.MAVEN:
            await self.template_manager.generate_maven_pom(
                project_path, project_config
            )
        elif build_system == BuildSystem.GRADLE:
            await self.template_manager.generate_gradle_build(
                project_path, project_config
            )
        elif build_system == BuildSystem.DOTNET:
            await self.template_manager.generate_dotnet_project(
                project_path, project_config
            )
        elif build_system in [BuildSystem.NPM, BuildSystem.YARN]:
            await self.template_manager.generate_package_json(
                project_path, project_config
            )
        elif build_system == BuildSystem.POETRY:
            await self.template_manager.generate_pyproject_toml(
                project_path, project_config
            )
            
    async def _setup_docker_environment(
        self,
        project_path: Path,
        project_type: ProjectType,
        project_config: Dict[str, Any]
    ):
        """Set up Docker environment for the project.
        
        Args:
            project_path: Project directory path
            project_type: Project type information
            project_config: Project configuration
        """
        # Generate Dockerfile from template
        dockerfile_template = project_type.docker_templates[0]  # Use first template
        dockerfile_content = await self.docker_manager.generate_dockerfile(
            dockerfile_template,
            project_config
        )
        
        dockerfile_path = project_path / "Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
            
        # Generate docker-compose.yml if needed
        if project_config.get("use_docker_compose", False):
            services = {
                "app": {
                    "build": ".",
                    "volumes": [
                        "./:/workspace"
                    ],
                    "environment": project_type.environment_variables
                }
            }
            
            compose_content = await self.docker_manager.create_compose_config(
                project_config["name"],
                services,
                project_path / "docker-compose.yml"
            )
            
    async def _create_project_instance(
        self,
        path: str,
        config: Dict[str, Any],
        project_type: ProjectType
    ) -> Any:
        """Create project instance based on type.
        
        Args:
            path: Project directory path
            config: Project configuration
            project_type: Project type information
            
        Returns:
            Project instance
        """
        # Import appropriate project class based on type
        if project_type.name == "java":
            from .java_project import JavaProject
            return JavaProject(path, config, project_type)
        elif project_type.name == "dotnet":
            from .dotnet_project import DotNetProject
            return DotNetProject(path, config, project_type)
        elif project_type.name == "node":
            from .node_project import NodeProject
            return NodeProject(path, config, project_type)
        elif project_type.name == "python":
            from .python_project import PythonProject
            return PythonProject(path, config, project_type)
        elif project_type.name == "golang":
            from .golang_project import GolangProject
            return GolangProject(path, config, project_type)
        else:
            from .base_project import Project
            return Project(path, config, project_type)
