import pytest
import os
import json
import logging
import sys
from unittest.mock import MagicMock

# Ensure project root is in sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.orchestrator import Orchestrator
from src.core.task_flow import load_task_flow
from src.executors.base import BaseExecutor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Model for DatabaseExecutor (simulating what SQLAlchemy would do)
class MockModel:
    __table__ = MagicMock()
    __table__.name = "mock_table"
    def __init__(self, **kwargs):
        self.data = kwargs

@pytest.fixture
def mock_executors():
    """Mock standard executors to control behavior in tests."""
    
    # Mock OCR Executor
    ocr_mock = MagicMock(spec=BaseExecutor)
    ocr_mock.execute.return_value = {
        "text": "Name: John Doe\nPAN: ABCDE1234F",
        "method": "mock_ocr"
    }
    
    # Mock LLM Executor
    llm_mock = MagicMock(spec=BaseExecutor)
    def llm_side_effect(config, inputs):
        task_type = inputs.get("task_type")
        if task_type == "classify":
            # Simulate classification
            return {
                "document_type": "pan",
                "confidence": 0.99
            }
        elif task_type == "extract":
            # Simulate extraction
            return {
                "name": "John Doe",
                "pan_number": "ABCDE1234F"
            }
        return {}
    llm_mock.execute.side_effect = llm_side_effect
    
    # Mock Validation Executor
    val_mock = MagicMock(spec=BaseExecutor)
    val_mock.execute.return_value = {
        "is_valid": True,
        "errors": [],
        "status": "success",
        "fields_validated": 2
    }

    # Mock Database Executor
    db_mock = MagicMock(spec=BaseExecutor)
    db_mock.execute.return_value = {"status": "stored", "table": "mock_table"}

    return {
        "OcrExecutor": ocr_mock,
        "LLMExecutor": llm_mock,
        "ValidationExecutor": val_mock,
        "DatabaseExecutor": db_mock
    }

def test_complex_agent_flow(mock_executors):
    """
    Test the complex_agent_flow.json workflow end-to-end using mocked executors.
    This validates the graph structure and data flow logic.
    """
    
    # 1. Load workflow definition
    workflow_path = os.path.join(
        os.path.dirname(__file__), 
        "../../workflows/examples/complex_agent_flow.json"
    )
    assert os.path.exists(workflow_path), "Example workflow file not found!"
    
    task_flow = load_task_flow(workflow_path)
    
    # 2. Initialize Orchestrator with mocked executors
    orchestrator = Orchestrator(executors=mock_executors, state_manager=None)
    
    # 3. Define Input
    input_data = {"document_path": "test_data/sample.png"}
    
    # 4. Execute
    result = orchestrator.execute(flow=task_flow, input_data=input_data)
    
    # 5. Assertions
    assert result.workflow_id == "complex_agent_flow_v1"
    
    # Check intermediate results
    outputs = result.outputs
    
    # OCR
    assert "ocr_step" in outputs
    assert outputs["ocr_step"]["text"] == "Name: John Doe\nPAN: ABCDE1234F"
    
    # Classify
    assert "classify_step" in outputs
    assert outputs["classify_step"]["document_type"] == "pan"
    
    # Extract
    assert "extract_step" in outputs
    assert outputs["extract_step"]["name"] == "John Doe"
    
    # Verification of dependency calls
    mock_executors["OcrExecutor"].execute.assert_called_once()
    mock_executors["LLMExecutor"].execute.assert_called() # Called twice
    mock_executors["ValidationExecutor"].execute.assert_called_once()
    mock_executors["DatabaseExecutor"].execute.assert_called_once()
    
    logger.info("Complex flow execution successful!")

if __name__ == "__main__":
    # Setup for standalone execution
    import sys
    # Add project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Manually run the test function
    # Mocking fixtures manually
    
    # Mock mocks
    ocr_mock = MagicMock(spec=BaseExecutor)
    ocr_mock.execute.return_value = {
        "text": "Name: John Doe\nPAN: ABCDE1234F",
        "method": "mock_ocr"
    }
    
    llm_mock = MagicMock(spec=BaseExecutor)
    def llm_side_effect(config, inputs):
        task_type = inputs.get("task_type")
        if task_type == "classify":
            return {"document_type": "pan", "confidence": 0.99}
        elif task_type == "extract":
            return {"name": "John Doe", "pan_number": "ABCDE1234F"}
        return {}
    llm_mock.execute.side_effect = llm_side_effect
    
    val_mock = MagicMock(spec=BaseExecutor)
    val_mock.execute.return_value = {"is_valid": True, "errors": [], "status": "success", "fields_validated": 2}

    db_mock = MagicMock(spec=BaseExecutor)
    db_mock.execute.return_value = {"status": "stored", "table": "mock_table"}

    executors = {
        "OcrExecutor": ocr_mock,
        "LLMExecutor": llm_mock,
        "ValidationExecutor": val_mock,
        "DatabaseExecutor": db_mock
    }
    
    try:
        test_complex_agent_flow(executors)
        print("TEST PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
