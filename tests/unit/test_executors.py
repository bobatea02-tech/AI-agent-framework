import sys
import os
from unittest.mock import MagicMock, patch

# Mock project-external dependencies BEFORE importing executors to avoid ImportErrors
sys.modules['pdf2image'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['openai'] = MagicMock()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import json
from src.executors.ocr_executor import OCRExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.validation_executor import ValidationExecutor

@pytest.fixture
def ocr_executor():
    return OCRExecutor()

@pytest.fixture
def llm_executor():
    # Pass a dummy key to avoid validation errors during init if any
    return LLMExecutor(config={"api_key": "test_key"})

@pytest.fixture
def validation_executor():
    return ValidationExecutor()

def test_ocr_executor_initialization(ocr_executor):
    """Test OCRExecutor can be instantiated"""
    assert isinstance(ocr_executor, OCRExecutor)
    assert ocr_executor.config == {}

def test_llm_executor_classification(llm_executor):
    """Test classify_document with mocked OpenAI response"""
    # Mock the OpenAI client's chat completion call
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({
        "document_type": "aadhaar",
        "confidence": 0.98,
        "reasoning": "Detected Aadhaar number pattern and UIDAI keywords."
    })
    
    # Use patch.object to patch the chat completions create method
    with patch.object(llm_executor.client.chat.completions, 'create', return_value=mock_response) as mock_create:
        result = llm_executor.classify_document("This is a sample document with Aadhaar number 1234 5678 1234")
        
        assert result["document_type"] == "aadhaar"
        assert "confidence" in result
        assert result["confidence"] == 0.98
        
        # Verify the mock was called with correct parameters (subset)
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["response_format"] == {"type": "json_object"}

def test_validation_executor_valid_data(validation_executor):
    """Test with valid Aadhaar and PAN data"""
    data = {
        "aadhaar_number": "123456789012",
        "pan_number": "ABCDE1234F"
    }
    result = validation_executor.execute({}, {"data": data})
    
    assert result["is_valid"] is True
    assert result["status"] == "success"
    assert len(result["errors"]) == 0
    assert result["fields_validated"] == 2

def test_validation_executor_invalid_data(validation_executor):
    """Test with invalid Aadhaar number"""
    data = {
        "aadhaar_number": "123", # Invalid: too short
        "pan_number": "ABCDE1234F" # Valid
    }
    result = validation_executor.execute({}, {"data": data})
    
    assert result["is_valid"] is False
    assert result["status"] == "failure"
    assert len(result["errors"]) == 1
    assert "aadhaar_number" in result["errors"][0]
    assert result["fields_validated"] == 2
