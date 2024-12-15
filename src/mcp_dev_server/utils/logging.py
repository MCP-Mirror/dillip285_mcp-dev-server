"""Logging configuration for MCP Development Server."""
import logging
import sys
from typing import Optional

def setup_logging(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name or __name__)
    logger.setLevel(level)
    
    # Create stderr handler (MCP protocol requires clean stdout)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger