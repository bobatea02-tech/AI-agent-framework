
import pytest
from unittest.mock import MagicMock
from src.executors.ocr_executor import OcrExecutor
from src.executors.base import BaseExecutor

def test_ocr_executor_inheritance():
    assert issubclass(OcrExecutor, BaseExecutor)

def test_ocr_executor_execute_success():
    executor = OcrExecutor()
    # Mock extract to avoid actual processing
    executor.extract = MagicMock(return_value={"text": "mocked text"})
    
    inputs = {"document": "path/to/image.png"}
    result = executor.execute(config={}, inputs=inputs)
    
    executor.extract.assert_called_once_with("path/to/image.png")
    assert result == {"text": "mocked text"}

def test_ocr_executor_execute_missing_input():
    executor = OcrExecutor()
    inputs = {}
    
    with pytest.raises(ValueError, match="Input 'document' is required"):
        executor.execute(config={}, inputs=inputs)
