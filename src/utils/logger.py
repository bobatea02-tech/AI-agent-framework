import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory
from structlog.types import Processor

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.json")


def setup_logging() -> None:
    """
    Configure structlog and standard logging.
    Sets up JSON formatting, timestamping, and output to both console and rotating file.
    """
    # Get log level from environment or default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Standard logging configuration
    # We need to configure the root logger to capture all logs (including libraries)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates during reloads
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 1. Stream Handler (Console) - Human readable or JSON based on env?
    # Requirement says "Configure output to both file and console"
    # Usually console is human readable in dev, JSON in prod.
    # Let's use a standard formatter for console for readability unless LOG_FORMAT=json
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 2. File Handler (JSON) - Rotating
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)

    # structlog Processor Configuration
    # These processors run effectively "before" the formatter
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Add request_id validation/extraction if passed in context, handled by merge_contextvars
    ]

    # Structlog configuration
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Formatter for JSON file output
    # This renders the final dict to a JSON string
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    file_handler.setFormatter(json_formatter)

    # Formatter for Console
    # Use ConsoleRenderer for colors/readability or JSON
    if os.getenv("LOG_FORMAT", "concise").lower() == "json":
        console_formatter = json_formatter
    else:
        console_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
    console_handler.setFormatter(console_formatter)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress overly verbose libraries if needed (optional optimization)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str = "ai_agent") -> structlog.stdlib.BoundLogger:
    """
    Return a configured structlog logger.
    
    Args:
        name: Logger name.
        
    Returns:
        BoundLogger: Configured logger instance.
    """
    return structlog.get_logger(name)
