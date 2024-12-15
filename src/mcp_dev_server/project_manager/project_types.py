"""Project type definitions and configurations."""
from typing import Dict, Any, List
from enum import Enum

class BuildSystem(str, Enum):
    """Build system types."""
    MAVEN = "maven"
    GRADLE = "gradle"
    NPM = "npm"
    YARN = "yarn"
    PIP = "pip"
    POETRY = "poetry"
    DOTNET = "dotnet"
    CARGO = "cargo"
    GO = "go"
    SBT = "sbt"

class ProjectType:
    """Base project type configuration."""
    
    def __init__(
        self,
        name: str,
        description: str,
        file_structure: Dict[str, Any],
        build_systems: List[BuildSystem],
        default_build_system: BuildSystem,
        config_files: List[str],
        environment_variables: Dict[str, str],
        docker_templates: List[str],
        input_templates: List[str]
    ):
        self.name = name
        self.description = description
        self.file_structure = file_structure
        self.build_systems = build_systems
        self.default_build_system = default_build_system
        self.config_files = config_files
        self.environment_variables = environment_variables
        self.docker_templates = docker_templates
        self.input_templates = input_templates

# Define standard project types
JAVA_PROJECT = ProjectType(
    name="java",
    description="Java project",
    file_structure={
        "src/": {
            "main/": {
                "java/": {},
                "resources/": {}
            },
            "test/": {
                "java/": {},
                "resources/": {}
            }
        },
        "target/": {},
    },
    build_systems=[BuildSystem.MAVEN, BuildSystem.GRADLE],
    default_build_system=BuildSystem.MAVEN,
    config_files=["pom.xml", "build.gradle", ".gitignore", "README.md"],
    environment_variables={
        "JAVA_HOME": "",
        "MAVEN_HOME": "",
        "GRADLE_HOME": ""
    },
    docker_templates=["java-maven", "java-gradle"],
    input_templates=["java_config", "maven_config", "gradle_config"]
)

DOTNET_PROJECT = ProjectType(
    name="dotnet",
    description=".NET project",
    file_structure={
        "src/": {},
        "tests/": {},
        "docs/": {}
    },
    build_systems=[BuildSystem.DOTNET],
    default_build_system=BuildSystem.DOTNET,
    config_files=[".csproj", ".sln", "global.json", ".gitignore", "README.md"],
    environment_variables={
        "DOTNET_ROOT": "",
        "ASPNETCORE_ENVIRONMENT": "Development"
    },
    docker_templates=["dotnet-sdk", "dotnet-runtime"],
    input_templates=["dotnet_config", "aspnet_config"]
)

NODE_PROJECT = ProjectType(
    name="node",
    description="Node.js project",
    file_structure={
        "src/": {},
        "tests/": {},
        "dist/": {},
        "public/": {}
    },
    build_systems=[BuildSystem.NPM, BuildSystem.YARN],
    default_build_system=BuildSystem.NPM,
    config_files=["package.json", "tsconfig.json", ".gitignore", "README.md"],
    environment_variables={
        "NODE_ENV": "development",
        "NPM_TOKEN": ""
    },
    docker_templates=["node-dev", "node-prod"],
    input_templates=["node_config", "npm_config", "typescript_config"]
)

PYTHON_PROJECT = ProjectType(
    name="python",
    description="Python project",
    file_structure={
        "src/": {},
        "tests/": {},
        "docs/": {},
        "notebooks/": {}
    },
    build_systems=[BuildSystem.PIP, BuildSystem.POETRY],
    default_build_system=BuildSystem.POETRY,
    config_files=["pyproject.toml", "setup.py", "requirements.txt", ".gitignore", "README.md"],
    environment_variables={
        "PYTHONPATH": "src",
        "PYTHON_ENV": "development"
    },
    docker_templates=["python-dev", "python-prod"],
    input_templates=["python_config", "poetry_config", "pytest_config"]
)

GOLANG_PROJECT = ProjectType(
    name="golang",
    description="Go project",
    file_structure={
        "cmd/": {},
        "internal/": {},
        "pkg/": {},
        "api/": {}
    },
    build_systems=[BuildSystem.GO],
    default_build_system=BuildSystem.GO,
    config_files=["go.mod", "go.sum", ".gitignore", "README.md"],
    environment_variables={
        "GOPATH": "",
        "GO111MODULE": "on"
    },
    docker_templates=["golang-dev", "golang-prod"],
    input_templates=["golang_config", "go_mod_config"]
)

RUST_PROJECT = ProjectType(
    name="rust",
    description="Rust project",
    file_structure={
        "src/": {},
        "tests/": {},
        "benches/": {},
        "examples/": {}
    },
    build_systems=[BuildSystem.CARGO],
    default_build_system=BuildSystem.CARGO,
    config_files=["Cargo.toml", "Cargo.lock", ".gitignore", "README.md"],
    environment_variables={
        "RUST_BACKTRACE": "1",
        "CARGO_HOME": ""
    },
    docker_templates=["rust-dev", "rust-prod"],
    input_templates=["rust_config", "cargo_config"]
)

# Map of all available project types
PROJECT_TYPES: Dict[str, ProjectType] = {
    "java": JAVA_PROJECT,
    "dotnet": DOTNET_PROJECT,
    "node": NODE_PROJECT,
    "python": PYTHON_PROJECT,
    "golang": GOLANG_PROJECT,
    "rust": RUST_PROJECT
}