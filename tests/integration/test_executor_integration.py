
import pytest
from src.executors.ocr_executor import OCRExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.validation_executor import ValidationExecutor

class TestExecutorIntegrationChain:
    """
    Test the flow of data between executors: OCR Output -> LLM Input -> Validation Input
    """
    
    @pytest.fixture
    def executor_chain(self):
        return {
            "ocr": OCRExecutor(),
            "llm": LLMExecutor(config={"api_key": "test"}),
            "validator": ValidationExecutor()
        }

    def test_ocr_to_llm_flow(self, executor_chain):
        """Simulate passing OCR output to LLM."""
        # 1. Simulate OCR Output (Mocking actual OCR to avoid Tesseract dependency)
        ocr_output = {"text": "Aadhaar Card: 1234 5678 9012\nDOB: 01/01/1990"}
        
        # 2. LLM Execution (Classify)
        # Mock LLM internal client
        with pytest.mock.patch.object(executor_chain["llm"].client.chat.completions, 'create') as mock_create:
            mock_create.return_value.choices[0].message.content = '{"document_type": "aadhaar", "id_number": "123456789012"}'
            
            # Exec
            llm_result = executor_chain["llm"].execute(
                inputs={"text": ocr_output["text"]},
                config={"task": "classify"}
            )
            
            assert llm_result["document_type"] == "aadhaar"
            assert llm_result["id_number"] == "123456789012"

    def test_llm_to_validation_flow(self, executor_chain):
        """Simulate LLM extracted data passing to Validation."""
        # 1. LLM Output
        llm_output = {
            "document_type": "aadhaar",
            "id_number": "123456789012"
        }
        
        # 2. Validation
        # Adapt inputs: Validator expects "data" dict
        validation_input = {
            "aadhaar_number": llm_output["id_number"]
        }
        
        val_result = executor_chain["validator"].execute(
            inputs={}, 
            config={"data": validation_input}
        )
        
        assert val_result["is_valid"] is True
