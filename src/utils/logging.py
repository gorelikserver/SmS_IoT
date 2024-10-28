import logging
import logging.handlers
import os
from typing import Optional
from .config import load_config


def setup_logging(config: Optional[dict] = None) -> None:
    """
    Setup logging configuration.
    If no config is provided, loads it using load_config()
    """
    if config is None:
        config = load_config()

    log_config = config['logging']

    # Create logs directory if it doesn't exist
    log_file = log_config['file']
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(log_config['format'])

    # Setup file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=log_config['max_size'],
        backupCount=log_config['backup_count']
    )
    file_handler.setFormatter(formatter)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config['level'])

    # Remove any existing handlers and add our handlers
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log startup message
    root_logger.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)

