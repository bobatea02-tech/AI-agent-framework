import sys
import os
from unittest.mock import MagicMock, patch

print("DEBUG: Loading conftest.py...")
# Mock all external dependencies globally for all tests

mock_modules = [
    'kafka',
    'kafka.producer',
    'kafka.admin',
    'redis',
    'structlog',
    'structlog.contextvars',
    'structlog.processors',
    'structlog.dev',
    'pdf2image',
    'pytesseract',
    'PIL',
    'PIL.Image',
    'openai'
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()

# Setup functional mock for structlog
mock_structlog = sys.modules['structlog']
mock_logger = MagicMock()
mock_structlog.get_logger.return_value = mock_logger
mock_structlog.make_filtering_bound_logger.return_value = mock_logger

# Mock processors as needed
mock_structlog.processors.JSONRenderer = MagicMock()
mock_structlog.processors.TimeStamper = MagicMock()
mock_structlog.dev.ConsoleRenderer = MagicMock()
mock_structlog.processors.StackInfoRenderer = MagicMock()
mock_structlog.processors.add_log_level = MagicMock()

# Mock StateManager
# We need to mock the actual class in its module if possible, 
# but for now, we'll patch it where it's used if needed.
# However, a global patch for redis is often enough if StateManager is imported.

# Ensure sys.path is correct for imports (now in root)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

