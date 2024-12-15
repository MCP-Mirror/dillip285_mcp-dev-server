"""Base manager class with common functionality."""
import uuid
from typing import Dict, Any

class BaseManager:
    """Base class for all managers."""
    
    def _generate_id(self) -> str:
        """Generate a unique identifier.
        
        Returns:
            str: Unique identifier
        """
        return str(uuid.uuid4())
        
    async def cleanup(self):
        """Clean up resources. Override in subclasses."""
        pass