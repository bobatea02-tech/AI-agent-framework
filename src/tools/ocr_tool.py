from __future__ import annotations

from pathlib import Path
from typing import Dict


def run_ocr(image_path: str | Path) -> Dict[str, str]:
    """Placeholder OCR wrapper for Tesseract/EasyOCR."""
    path = Path(image_path)
    # TODO: hook into pytesseract or easyocr
    return {"text": f"[ocr text from {path.name}]"}


