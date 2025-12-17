from __future__ import annotations

from typing import Any, Dict

from .base import BaseExecutor


class OCRExecutor(BaseExecutor):
    """Placeholder OCR executor using Tesseract/EasyOCR."""

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: integrate real OCR pipeline
        document = inputs.get("document")
        return {"text": f"[ocr output placeholder for {document}]"}


