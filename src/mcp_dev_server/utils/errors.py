"""Error definitions for MCP Development Server."""

class MCPDevServerError(Exception):
    """Base error class for MCP Development Server."""
    pass

class ProjectError(MCPDevServerError):
    """Project-related errors."""
    pass

class BuildError(MCPDevServerError):
    """Build-related errors."""
    pass

class TestError(MCPDevServerError):
    """Test-related errors."""
    pass

class EnvironmentError(MCPDevServerError):
    """Environment-related errors."""
    pass

class ConfigurationError(MCPDevServerError):
    """Configuration-related errors."""
    pass

class WorkflowError(MCPDevServerError):
    """Workflow-related errors."""
    pass