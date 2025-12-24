
import logging
import logging.handlers
import os
import sys
from typing import Any, Dict

import structlog

def setup_logging(
    log_level: str = None,
    log_dir: str = "logs",
    log_filename: str = "app.log"
) -> None:
    """
    Configures structlog and standard logging.
    
    Args:
        log_level: Logging level (e.g., "INFO", "DEBUG"). Defaults to LOG_LEVEL env var or INFO.
        log_dir: Directory to store log files.
        log_filename: Name of the log file.
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    # We use ConsoleRenderer for console to make it readable, or JSONRenderer if you prefer valid JSON always.
    # The prompt asked for "JSON formatting" generally, but often console is preferred readable. 
    # However, "Sets up processors for JSON formatting" implies JSON everywhere usually, or at least for file.
    # Let's use JSON for both to be safe and consistent, or ConsoleRenderer for console + JSON for file.
    # Re-reading: "Uses log level from environment variable... Configures output to both file and console"
    # "Sets up processors for JSON formatting" -> implues structure.
    
    # Let's use JSON for file, and ConsoleRenderer (colored, structured) for console if it's a TTY, 
    # but strictly following "JSON formatting" might mean JSON everywhere. 
    # structlog.processors.JSONRenderer() is what we want for the formatter.
    
    # Formatter for console - let's make it JSON as requested for robust structured logging.
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    console_handler.setFormatter(json_formatter)

    # File handler with rotation
    file_path = os.path.join(log_dir, log_filename)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        file_path, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(json_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates if setup is called multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Intercept standard library logs
    logging.captureWarnings(True)

def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Returns a configured structlog logger.
    
    Args:
        name: Name of the logger. If None, returns the root logger.
    """
    return structlog.get_logger(name)
