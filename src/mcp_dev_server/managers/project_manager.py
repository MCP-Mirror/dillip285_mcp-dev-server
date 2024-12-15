from ..models import Config

class ProjectManager:
    """Manager class for project-related operations."""
    
    def __init__(self, config: Config):
        """Initialize the project manager.
        
        Args:
            config: Server configuration
        """
        self.config = config