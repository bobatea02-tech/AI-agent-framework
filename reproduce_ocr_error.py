import sys
import os
from unittest.mock import MagicMock

# Mock dependencies
mock_modules = ['pdf2image', 'pytesseract', 'PIL', 'PIL.Image']
for m in mock_modules:
    sys.modules[m] = MagicMock()

sys.path.insert(0, os.path.abspath('.'))

from src.executors.ocr_executor import OCRExecutor

try:
    print("Attempting to instantiate OCRExecutor with config...")
    executor = OCRExecutor(config={"test": "config"})
    print("Success!")
except TypeError as e:
    print(f"Caught expected TypeError: {e}")
except Exception as e:
    print(f"Caught unexpected error: {e}")
