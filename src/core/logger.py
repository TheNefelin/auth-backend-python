"""Logger module for the Auth Unificado backend.

Provides structured logging configuration.
"""

import logging
import sys
from typing import Any

from .config import settings


def setup_logging() -> logging.Logger:
    """Set up application logging configuration."""
    logger = logging.getLogger("auth-unificado")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Avoid adding handler multiple times
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger


# Create default logger instance
logger = setup_logging()