# src/observability/logger.py
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            # Use explicit UTC timestamp (append Z) so downstream systems know it's UTC
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        wf = getattr(record, "workflow_id", None)
        if wf is not None:
            log_obj["workflow_id"] = wf

        tid = getattr(record, "task_id", None)
        if tid is not None:
            log_obj["task_id"] = tid

        dur = getattr(record, "duration_ms", None)
        if dur is not None:
            log_obj["duration_ms"] = dur
        # Include exception/stack information if present
        if record.exc_info:
            try:
                log_obj["exc_info"] = self.formatException(record.exc_info)
            except Exception:
                # Fallback: include textual representation
                log_obj["exc_info"] = str(record.exc_info)

        stack = getattr(record, "stack_info", None)
        # formatStack expects a str; only call it when stack is truthy
        if stack:
            try:
                log_obj["stack_info"] = self.formatStack(stack)
            except Exception:
                log_obj["stack_info"] = str(stack)

        return json.dumps(log_obj)

def setup_logging():
    """Configure structured JSON logging"""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    
    root_logger = logging.getLogger()
    # Avoid adding duplicate handlers when this module is imported multiple times
    found = False
    for h in root_logger.handlers:
        if isinstance(h, logging.StreamHandler) and isinstance(getattr(h, "formatter", None), JsonFormatter):
            found = True
            break
    if not found:
        root_logger.addHandler(handler)

    # Only set the level if it's not already more/less restrictive
    if root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.INFO)
    
    return root_logger

# Provide a module-level logger object for convenience, but avoid emitting
# example logs at import time. Consumers can call `setup_logging()` explicitly
# or import `logger` and use it.
logger = setup_logging()


if __name__ == "__main__":
    # Demonstration when running this file directly
    demo = setup_logging()
    demo.info(
        "task_completed",
        extra={
            "workflow_id": "wf_demo",
            "task_id": "demo_task",
            "duration_ms": 234
        }
    )
