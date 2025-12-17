from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def extract_text_from_pdf(path: str | Path) -> List[str]:
    """Placeholder PDF text extractor."""
    path = Path(path)
    # TODO: integrate pdfplumber or PyPDF2
    return [f"Sample text from {path.name}"]


def load_pdf(path: str | Path) -> Dict[str, List[str]]:
    return {"pages": extract_text_from_pdf(path)}


