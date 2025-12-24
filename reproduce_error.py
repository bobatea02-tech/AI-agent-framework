import sys
import os
from unittest.mock import MagicMock

# Attempt to duplicate conftest.py logic
mock_modules = ['kafka', 'redis', 'structlog', 'pdf2image', 'pytesseract', 'PIL', 'PIL.Image', 'openai']
for m in mock_modules:
    sys.modules[m] = MagicMock()

sys.path.insert(0, os.path.abspath('.'))

try:
    print("Attempting to import src.api.main...")
    from src.api.main import app
    print("Import successful!")
    
    from src.api.routes import orchestrator_instance
    print("Orchestrator instance created!")
    
    from src.executors.ocr_executor import OCRExecutor
    print("OCRExecutor imported!")
    
except Exception as e:
    import traceback
    traceback.print_exc()
