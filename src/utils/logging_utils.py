"""
Logging utilities module
-----------------------
Provides centralized logging configuration for the SDK.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = "harvesters_sdk.log",
    log_format: str = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S"
) -> None:
    """
    Configure global logging for the SDK.

    Args:
        level: Logging level (default: logging.INFO)
        log_file: Optional path to log file
        log_format: Format string for log messages
        date_format: Format string for timestamps
    """
    # Create handlers list
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    # Configure logging
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )

    # Create main logger
    logger = logging.getLogger("harvestersSDK")
    logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name, prefixed with 'harvestersSDK'.

    Args:
        name: Logger name (will be prefixed with 'harvestersSDK.')

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"harvestersSDK.{name}")