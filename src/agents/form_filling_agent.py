from __future__ import annotations

from typing import Any, Dict

from src.executors.ocr_executor import OCRExecutor
from src.executors.validation_executor import ValidationExecutor


class FormFillingAgent:
    """Reference agent for government form automation."""

    def __init__(self) -> None:
        self.ocr = OCRExecutor()
        self.validator = ValidationExecutor()

    def run(self, document_path: str) -> Dict[str, Any]:
        ocr_output = self.ocr.execute(config={}, inputs={"document": document_path})
        validation = self.validator.execute(
            config={"required_fields": ["name", "dob", "id_number"]},
            inputs=ocr_output,
        )
        return {"ocr": ocr_output, "validation": validation}


