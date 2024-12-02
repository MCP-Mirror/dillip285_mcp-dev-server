"""Custom error types for the MCP Development Server."""

class MCPDevServerError(Exception):
    """Base exception class for MCP Development Server errors."""
    pass

class ProjectError(MCPDevServerError):
    """Project-related errors."""
    pass

class ProjectNotFoundError(ProjectError):
    """Raised when a project cannot be found."""
    pass

class ProjectInitializationError(ProjectError):
    """Raised when project initialization fails."""
    pass

class FileOperationError(MCPDevServerError):
    """File system operation errors."""
    pass

class GitError(MCPDevServerError):
    """Git operation errors."""
    pass

class ConfigurationError(MCPDevServerError):
    """Configuration-related errors."""
    pass

class TemplateError(MCPDevServerError):
    """Project template errors."""
    pass
"""Add Docker-related error types."""

class DockerError(Exception):
    """Base exception for Docker-related errors."""
    pass

class ContainerError(DockerError):
    """Container operation errors."""
    pass

class VolumeError(DockerError):
    """Volume operation errors."""
    pass

class NetworkError(DockerError):
    """Network operation errors."""
    pass

class StreamError(Exception):
    """Enhanced stream-related errors."""
    pass

class SyncError(Exception):
    """Enhanced sync-related errors."""
    pass