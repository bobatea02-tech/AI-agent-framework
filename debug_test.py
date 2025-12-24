import sys
import os
from unittest.mock import MagicMock
import json

# Mock dependencies
sys.modules['pdf2image'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['openai'] = MagicMock()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.executors.llm_executor import LLMExecutor

def debug_llm_test():
    try:
        llm_executor = LLMExecutor(config={"api_key": "test_key"})
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "document_type": "aadhaar",
            "confidence": 0.98,
            "reasoning": "Detected Aadhaar"
        })
        
        # Patch the method
        llm_executor.client.chat.completions.create = MagicMock(return_value=mock_response)
        
        result = llm_executor.classify_document("test text")
        print(f"Result: {result}")
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm_test()
