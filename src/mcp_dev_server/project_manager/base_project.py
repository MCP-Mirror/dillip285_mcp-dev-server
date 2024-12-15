"""Base project class definition."""
import os
import uuid
import xml.etree.ElementTree as ET
import json
import tomli
from pathlib import Path
from typing import Dict, Any, Optional, List
import git

from .project_types import ProjectType, BuildSystem
from ..utils.errors import ProjectError
from ..utils.logging import setup_logging

logger = setup_logging(__name__)

class Project:
    """Base project class."""
    
    def __init__(self, path: str, config: Dict[str, Any], project_type: ProjectType):
        """Initialize project instance."""
        self.id = str(uuid.uuid4())
        self.path = path
        self.config = config
        self.project_type = project_type
        self.build_system = BuildSystem(config["build_system"])
        
    def get_dependencies(self) -> Dict[str, Any]:
        """Get project dependencies."""
        if self.build_system == BuildSystem.MAVEN:
            return self._get_maven_dependencies()
        elif self.build_system == BuildSystem.GRADLE:
            return self._get_gradle_dependencies()
        elif self.build_system in [BuildSystem.NPM, BuildSystem.YARN]:
            return self._get_node_dependencies()
        elif self.build_system == BuildSystem.POETRY:
            return self._get_poetry_dependencies()
        elif self.build_system == BuildSystem.DOTNET:
            return self._get_dotnet_dependencies()
        elif self.build_system == BuildSystem.GO:
            return self._get_go_dependencies()
        else:
            return {}

    def _get_maven_dependencies(self) -> Dict[str, Any]:
        """Get Maven project dependencies."""
        pom_path = Path(self.path) / "pom.xml"
        if not pom_path.exists():
            return {}

        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            dependencies = []
            for dep in root.findall('.//maven:dependency', ns):
                dependencies.append({
                    'groupId': dep.find('maven:groupId', ns).text,
                    'artifactId': dep.find('maven:artifactId', ns).text,
                    'version': dep.find('maven:version', ns).text if dep.find('maven:version', ns) is not None else None,
                    'scope': dep.find('maven:scope', ns).text if dep.find('maven:scope', ns) is not None else 'compile'
                })
                
            return {'maven': dependencies}
        except Exception as e:
            logger.error(f"Error parsing Maven dependencies: {e}")
            return {}

    def _get_node_dependencies(self) -> Dict[str, Any]:
        """Get Node.js project dependencies."""
        package_path = Path(self.path) / "package.json"
        if not package_path.exists():
            return {}

        try:
            with open(package_path) as f:
                package_data = json.load(f)
                return {
                    'dependencies': package_data.get('dependencies', {}),
                    'devDependencies': package_data.get('devDependencies', {})
                }
        except Exception as e:
            logger.error(f"Error parsing Node.js dependencies: {e}")
            return {}

    def _get_poetry_dependencies(self) -> Dict[str, Any]:
        """Get Poetry project dependencies."""
        pyproject_path = Path(self.path) / "pyproject.toml"
        if not pyproject_path.exists():
            return {}

        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomli.load(f)
                tool_poetry = pyproject_data.get('tool', {}).get('poetry', {})
                return {
                    'dependencies': tool_poetry.get('dependencies', {}),
                    'dev-dependencies': tool_poetry.get('dev-dependencies', {})
                }
        except Exception as e:
            logger.error(f"Error parsing Poetry dependencies: {e}")
            return {}

    def _get_dotnet_dependencies(self) -> Dict[str, Any]:
        """Get .NET project dependencies."""
        try:
            # Find all .csproj files
            csproj_files = list(Path(self.path).glob("**/*.csproj"))
            dependencies = {}
            
            for csproj in csproj_files:
                tree = ET.parse(csproj)
                root = tree.getroot()
                project_deps = []
                
                for item_group in root.findall('.//PackageReference'):
                    project_deps.append({
                        'Include': item_group.get('Include'),
                        'Version': item_group.get('Version')
                    })
                    
                dependencies[csproj.stem] = project_deps
                
            return dependencies
        except Exception as e:
            logger.error(f"Error parsing .NET dependencies: {e}")
            return {}

    def _get_go_dependencies(self) -> Dict[str, Any]:
        """Get Go project dependencies."""
        go_mod_path = Path(self.path) / "go.mod"
        if not go_mod_path.exists():
            return {}

        try:
            result = subprocess.run(
                ['go', 'list', '-m', 'all'],
                capture_output=True,
                text=True,
                cwd=self.path
            )
            if result.returncode == 0:
                dependencies = []
                for line in result.stdout.splitlines()[1:]:  # Skip first line (module name)
                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies.append({
                            'module': parts[0],
                            'version': parts[1]
                        })
                return {'modules': dependencies}
        except Exception as e:
            logger.error(f"Error parsing Go dependencies: {e}")
            return {}

    async def update_dependencies(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update project dependencies."""
        if self.build_system == BuildSystem.MAVEN:
            cmd = "mvn versions:use-latest-versions"
        elif self.build_system == BuildSystem.GRADLE:
            cmd = "./gradlew dependencyUpdates"
        elif self.build_system == BuildSystem.NPM:
            cmd = "npm update"
        elif self.build_system == BuildSystem.YARN:
            cmd = "yarn upgrade"
        elif self.build_system == BuildSystem.POETRY:
            cmd = "poetry update"
        elif self.build_system == BuildSystem.DOTNET:
            cmd = "dotnet restore"
        else:
            raise ProjectError(f"Dependency updates not supported for {self.build_system}")
            
        return await self.execute_command(cmd)

    async def get_project_analysis(self) -> Dict[str, Any]:
        """Get project analysis results."""
        analysis = {
            "structure": self.get_structure(),
            "dependencies": self.get_dependencies(),
            "metadata": {
                "name": self.config["name"],
                "type": self.project_type.name,
                "build_system": self.build_system.value,
                "config": self.config
            }
        }

        # Add Git information if available
        git_info = self.get_git_status()
        if git_info.get("initialized", False):
            analysis["git"] = git_info

        # Add build/test status if available
        if hasattr(self, 'last_build'):
            analysis["last_build"] = self.last_build
        if hasattr(self, 'last_test_run'):
            analysis["last_test_run"] = self.last_test_run

        return analysis

    def get_structure(self) -> Dict[str, Any]:
        """Get project structure."""
        def scan_dir(path: Path) -> Dict[str, Any]:
            structure = {}
            ignore_patterns = ['.git', '__pycache__', 'node_modules', 'target', 'build']
            
            for item in path.iterdir():
                if item.name in ignore_patterns:
                    continue
                    
                if item.is_file():
                    structure[item.name] = {
                        "type": "file",
                        "size": item.stat().st_size
                    }
                elif item.is_dir():
                    structure[item.name] = {
                        "type": "directory",
                        "contents": scan_dir(item)
                    }
                    
            return structure
            
        return scan_dir(Path(self.path))

    async def cleanup(self):
        """Clean up project resources."""
        try:
            # Clean build artifacts
            if self.build_system == BuildSystem.MAVEN:
                await self.execute_command("mvn clean")
            elif self.build_system == BuildSystem.GRADLE:
                await self.execute_command("./gradlew clean")
            elif self.build_system == BuildSystem.NPM:
                await self.execute_command("npm run clean")

            logger.info(f"Cleaned up project: {self.config['name']}")
        except Exception as e:
            logger.error(f"Project cleanup failed: {e}")
            raise ProjectError(f"Cleanup failed: {str(e)}")
