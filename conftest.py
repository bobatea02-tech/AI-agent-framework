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
    # 'structlog',  <-- Removed
    # 'structlog.contextvars', <-- Removed
    # 'structlog.processors', <-- Removed
    # 'structlog.dev', <-- Removed
    'pdf2image',
    'pytesseract',
    'PIL',
    'PIL.Image',
    'openai'
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()

# structlog configuration removal
# We use the real structlog library now.

# Mock StateManager
# We need to mock the actual class in its module if possible, 
# but for now, we'll patch it where it's used if needed.
# However, a global patch for redis is often enough if StateManager is imported.

# Ensure sys.path is correct for imports (now in root)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

