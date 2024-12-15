"""Input request templates for common scenarios."""
from typing import Dict
from .input_protocol import InputRequest, InputField

ENVIRONMENT_SETUP = InputRequest(
    request_id="environment_setup",
    title="Setup Development Environment",
    description="Configure your development environment",
    fields=[
        InputField(
            name="language",
            type="select",
            description="Primary programming language",
            options=[
                {"value": "python", "label": "Python"},
                {"value": "node", "label": "Node.js"},
                {"value": "both", "label": "Python & Node.js"}
            ]
        ),
        InputField(
            name="python_version",
            type="select",
            description="Python version",
            options=[
                {"value": "3.12", "label": "Python 3.12"},
                {"value": "3.11", "label": "Python 3.11"},
                {"value": "3.10", "label": "Python 3.10"}
            ],
            required=False
        ),
        InputField(
            name="node_version",
            type="select",
            description="Node.js version",
            options=[
                {"value": "20", "label": "Node.js 20 LTS"},
                {"value": "18", "label": "Node.js 18 LTS"}
            ],
            required=False
        ),
        InputField(
            name="include_docker",
            type="confirm",
            description="Include Docker support?",
            default=False
        )
    ]
)

TEST_CONFIGURATION = InputRequest(
    request_id="test_configuration",
    title="Configure Test Environment",
    description="Set up testing parameters",
    fields=[
        InputField(
            name="test_framework",
            type="select",
            description="Testing framework",
            options=[
                {"value": "pytest", "label": "pytest"},
                {"value": "unittest", "label": "unittest"},
                {"value": "jest", "label": "Jest"},
                {"value": "mocha", "label": "Mocha"}
            ]
        ),
        InputField(
            name="include_coverage",
            type="confirm",
            description="Include coverage reporting?",
            default=True
        ),
        InputField(
            name="parallel",
            type="confirm",
            description="Run tests in parallel?",
            default=False
        ),
        InputField(
            name="test_path",
            type="text",
            description="Test directory or file pattern",
            default="tests/",
            required=False
        )
    ]
)

DEPLOYMENT_CONFIG = InputRequest(
    request_id="deployment_config",
    title="Configure Deployment",
    description="Set up deployment parameters",
    fields=[
        InputField(
            name="environment",
            type="select",
            description="Deployment environment",
            options=[
                {"value": "development", "label": "Development"},
                {"value": "staging", "label": "Staging"},
                {"value": "production", "label": "Production"}
            ]
        ),
        InputField(
            name="deploy_method",
            type="select",
            description="Deployment method",
            options=[
                {"value": "docker", "label": "Docker Container"},
                {"value": "kubernetes", "label": "Kubernetes"},
                {"value": "serverless", "label": "Serverless"}
            ]
        ),
        InputField(
            name="auto_deploy",
            type="confirm",
            description="Enable automatic deployment?",
            default=False
        ),
        InputField(
            name="rollback_enabled",
            type="confirm",
            description="Enable automatic rollback?",
            default=True
        )
    ]
)

DEBUG_CONFIG = InputRequest(
    request_id="debug_config",
    title="Configure Debugging Session",
    description="Set up debugging parameters",
    fields=[
        InputField(
            name="debug_type",
            type="select",
            description="Type of debugging",
            options=[
                {"value": "python", "label": "Python Debugger"},
                {"value": "node", "label": "Node.js Debugger"},
                {"value": "remote", "label": "Remote Debugging"}
            ]
        ),
        InputField(
            name="port",
            type="number",
            description="Debug port",
            default=9229,
            validation={"min": 1024, "max": 65535}
        ),
        InputField(
            name="break_on_entry",
            type="confirm",
            description="Break on entry point?",
            default=True
        )
    ]
)

TEMPLATE_REQUESTS: Dict[str, InputRequest] = {
    "environment_setup": ENVIRONMENT_SETUP,
    "test_configuration": TEST_CONFIGURATION,
    "deployment_config": DEPLOYMENT_CONFIG,
    "debug_config": DEBUG_CONFIG
}