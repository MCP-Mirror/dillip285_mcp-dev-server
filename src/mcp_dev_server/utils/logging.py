"""Logging configuration for the MCP Development Server."""
import logging
import sys
from typing import Optional

def setup_logging(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the given module.
    
    Args:
        name: Module name for the logger
        level: Optional logging level (defaults to INFO)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    logger.setLevel(level or logging.INFO)
    
    # Create handler if none exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        logger.addHandler(handler)
    
    return logger