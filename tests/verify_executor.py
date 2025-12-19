import sys
import os
import logging
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.executor import BaseExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestExecutor(BaseExecutor):
    def execute(self, inputs: Dict[str, Any]) -> str:
        if inputs.get("fail"):
            raise RuntimeError("Intentional failure")
        return f"Processed {inputs.get('data')}"

def test_executor():
    executor = TestExecutor()
    
    # Test success
    print("Testing Success Case:")
    result = executor.run_with_monitoring({"data": "test_data"})
    print(result)
    assert result["status"] == "success"
    assert result["output"] == "Processed test_data"
    assert "duration" in result
    assert "timestamp" in result
    
    # Test failure
    print("\nTesting Failure Case:")
    result = executor.run_with_monitoring({"fail": True})
    print(result)
    assert result["status"] == "failed"
    assert "Intentional failure" in result["error"]

    # Test input validation
    print("\nTesting Input Validation:")
    result = executor.run_with_monitoring("invalid_input") # type: ignore
    print(result)
    assert result["status"] == "failed"
    assert "Inputs must be a dictionary" in result["error"]
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_executor()
