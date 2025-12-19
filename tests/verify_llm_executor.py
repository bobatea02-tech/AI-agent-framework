import sys
import os
import logging
import json
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock openai BEFORE import
sys.modules['openai'] = MagicMock()

from src.executors.llm_executor import LLMExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestLLMExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = LLMExecutor(config={"api_key": "dummy_key"})
        # The executor creates self.client. We need to mock the chat.completions.create method on it.
        self.mock_create = self.executor.client.chat.completions.create

    def test_classify_document(self):
        print("\nTesting Classify Document...")
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "document_type": "aadhaar",
            "confidence": 0.95,
            "reasoning": "Contains UIDAI keywords"
        })
        self.mock_create.return_value = mock_response

        inputs = {
            "task_type": "classify",
            "text": "This is a sample Aadhaar Card text."
        }
        
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertEqual(result["document_type"], "aadhaar")
        self.assertEqual(result["confidence"], 0.95)
        
        # Verify call arguments
        call_args = self.mock_create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4o-mini")
        self.assertEqual(call_args["response_format"], {"type": "json_object"})

    def test_extract_aadhaar(self):
        print("\nTesting Extract Aadhaar...")
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "name": "John Doe",
            "aadhaar_number": "1234 5678 9012",
            "dob": "1990-01-01",
            "gender": "Male",
            "address": "123 Street",
            "confidence": 0.98
        })
        self.mock_create.return_value = mock_response

        inputs = {
            "task_type": "extract",
            "document_type": "aadhaar",
            "text": "Aadhaar content..."
        }
        
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["aadhaar_number"], "1234 5678 9012")
        
        # Verify call arguments
        call_args = self.mock_create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4o")
        self.assertEqual(call_args["temperature"], 0)

    def test_extract_pan(self):
        print("\nTesting Extract PAN...")
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "name": "Jane Doe",
            "pan_number": "ABCDE1234F",
            "father_name": "Bob Doe",
            "dob": "1992-02-02",
            "confidence": 0.99
        })
        self.mock_create.return_value = mock_response

        inputs = {
            "task_type": "extract",
            "document_type": "pan",
            "text": "PAN content..."
        }
        
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertEqual(result["pan_number"], "ABCDE1234F")

    def test_invalid_task(self):
        print("\nTesting Invalid Task...")
        with self.assertRaises(ValueError):
            self.executor.execute({"task_type": "unknown"})

if __name__ == "__main__":
    unittest.main()
