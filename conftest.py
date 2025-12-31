
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
    'pdf2image',
    'pytesseract',
    'PIL',
    'PIL.Image',
    'openai'
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()

# Ensure sys.path is correct for imports (now in root)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
