"""Project-specific input templates."""
from typing import Dict
from .input_protocol import InputRequest, InputField

# Java Project Templates
JAVA_CONFIG = InputRequest(
    request_id="java_config",
    title="Java Project Configuration",
    description="Configure Java project settings",
    fields=[
        InputField(
            name="java_version",
            type="select",
            description="Java version",
            options=[
                {"value": "21", "label": "Java 21 (LTS)"},
                {"value": "17", "label": "Java 17 (LTS)"},
                {"value": "11", "label": "Java 11 (LTS)"},
                {"value": "8", "label": "Java 8"}
            ]
        ),
        InputField(
            name="project_type",
            type="select",
            description="Project type",
            options=[
                {"value": "spring-boot", "label": "Spring Boot"},
                {"value": "jakarta-ee", "label": "Jakarta EE"},
                {"value": "android", "label": "Android"},
                {"value": "library", "label": "Java Library"}
            ]
        ),
        InputField(
            name="packaging",
            type="select",
            description="Packaging type",
            options=[
                {"value": "jar", "label": "JAR"},
                {"value": "war", "label": "WAR"},
                {"value": "ear", "label": "EAR"}
            ]
        )
    ]
)

# .NET Project Templates
DOTNET_CONFIG = InputRequest(
    request_id="dotnet_config",
    title=".NET Project Configuration",
    description="Configure .NET project settings",
    fields=[
        InputField(
            name="dotnet_version",
            type="select",
            description=".NET version",
            options=[
                {"value": "8.0", "label": ".NET 8.0"},
                {"value": "7.0", "label": ".NET 7.0"},
                {"value": "6.0", "label": ".NET 6.0 (LTS)"}
            ]
        ),
        InputField(
            name="project_type",
            type="select",
            description="Project type",
            options=[
                {"value": "webapi", "label": "ASP.NET Core Web API"},
                {"value": "mvc", "label": "ASP.NET Core MVC"},
                {"value": "blazor", "label": "Blazor"},
                {"value": "maui", "label": ".NET MAUI"},
                {"value": "library", "label": "Class Library"}
            ]
        ),
        InputField(
            name="authentication",
            type="select",
            description="Authentication type",
            options=[
                {"value": "none", "label": "None"},
                {"value": "individual", "label": "Individual Accounts"},
                {"value": "microsoft", "label": "Microsoft Identity Platform"},
                {"value": "windows", "label": "Windows Authentication"}
            ]
        )
    ]
)

# Node.js Project Templates
NODE_CONFIG = InputRequest(
    request_id="node_config",
    title="Node.js Project Configuration",
    description="Configure Node.js project settings",
    fields=[
        InputField(
            name="node_version",
            type="select",
            description="Node.js version",
            options=[
                {"value": "20", "label": "Node.js 20 (LTS)"},
                {"value": "18", "label": "Node.js 18 (LTS)"}
            ]
        ),
        InputField(
            name="project_type",
            type="select",
            description="Project type",
            options=[
                {"value": "express", "label": "Express.js"},
                {"value": "next", "label": "Next.js"},
                {"value": "nest", "label": "NestJS"},
                {"value": "library", "label": "NPM Package"}
            ]
        ),
        InputField(
            name="typescript",
            type="confirm",
            description="Use TypeScript?",
            default=True
        )
    ]
)

# Python Project Templates
PYTHON_CONFIG = InputRequest(
    request_id="python_config",
    title="Python Project Configuration",
    description="Configure Python project settings",
    fields=[
        InputField(
            name="python_version",
            type="select",
            description="Python version",
            options=[
                {"value": "3.12", "label": "Python 3.12"},
                {"value": "3.11", "label": "Python 3.11"},
                {"value": "3.10", "label": "Python 3.10"}
            ]
        ),
        InputField(
            name="project_type",
            type="select",
            description="Project type",
            options=[
                {"value": "fastapi", "label": "FastAPI"},
                {"value": "django", "label": "Django"},
                {"value": "flask", "label": "Flask"},
                {"value": "library", "label": "Python Package"}
            ]
        ),
        InputField(
            name="dependency_management",
            type="select",
            description="Dependency management",
            options=[
                {"value": "poetry", "label": "Poetry"},
                {"value": "pip", "label": "pip + requirements.txt"},
                {"value": "pipenv", "label": "Pipenv"}
            ]
        )
    ]
)

# Golang Project Templates
GOLANG_CONFIG = InputRequest(
    request_id="golang_config",
    title="Go Project Configuration",
    description="Configure Go project settings",
    fields=[
        InputField(
            name="go_version",
            type="select",
            description="Go version",
            options=[
                {"value": "1.22", "label": "Go 1.22"},
                {"value": "1.21", "label": "Go 1.21"},
                {"value": "1.20", "label": "Go 1.20"}
            ]
        ),
        InputField(
            name="project_type",
            type="select",
            description="Project type",
            options=[
                {"value": "gin", "label": "Gin Web Framework"},
                {"value": "echo", "label": "Echo Framework"},
                {"value": "cli", "label": "CLI Application"},
                {"value": "library", "label": "Go Module"}
            ]
        ),
        InputField(
            name="module_path",
            type="text",
            description="Module path (e.g., github.com/user/repo)",
            validation={"pattern": r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+(/[a-zA-Z0-9_.-]+)?$"}
        )
    ]
)

# All project templates
PROJECT_TEMPLATES: Dict[str, InputRequest] = {
    "java_config": JAVA_CONFIG,
    "dotnet_config": DOTNET_CONFIG,
    "node_config": NODE_CONFIG,
    "python_config": PYTHON_CONFIG,
    "golang_config": GOLANG_CONFIG
}