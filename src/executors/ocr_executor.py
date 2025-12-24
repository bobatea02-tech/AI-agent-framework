from __future__ import annotations

import os
import tempfile
import logging
from typing import Any, Dict, List, Optional
from PIL import Image
import pytesseract
import pdf2image

from src.core.executor import BaseExecutor

logger = logging.getLogger(__name__)

class OCRExecutor(BaseExecutor):
    """
    Executor for Optical Character Recognition (OCR) tasks.
    Supports PDF and Image files using Tesseract.
    """

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute OCR on provided documents.

        Args:
            inputs: Dictionary containing:
                - documents: List[str] - List of file paths to process.

        Returns:
            Dictionary containing:
                - documents: List[Dict] - Results for each document.
                - total_documents: int - Count of processed documents.
                - text: str - Combined text from all documents.
        """
        documents = inputs.get("documents", [])
        if not isinstance(documents, list):
            raise ValueError(f"Expected 'documents' to be a list, got {type(documents)}")

        results = []
        combined_text = []

        for doc_path in documents:
            if not os.path.exists(doc_path):
                logger.warning(f"File not found: {doc_path}")
                results.append({
                    "file": doc_path,
                    "status": "error",
                    "error": "File not found"
                })
                continue

            try:
                text = ""
                ext = os.path.splitext(doc_path)[1].lower()
                
                if ext == ".pdf":
                    text = self._extract_from_pdf(doc_path)
                elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                    text = self._extract_from_image(doc_path)
                else:
                    logger.warning(f"Unsupported file format: {doc_path}")
                    results.append({
                        "file": doc_path,
                        "status": "error",
                        "error": "Unsupported file format"
                    })
                    continue

                results.append({
                    "file": doc_path,
                    "status": "success",
                    "text": text
                })
                combined_text.append(text)

            except Exception as e:
                logger.error(f"Failed to process {doc_path}: {e}", exc_info=True)
                results.append({
                    "file": doc_path,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "documents": results,
            "total_documents": len(documents),
            "text": "\n\n".join(combined_text)
        }

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file by converting pages to images.
        """
        logger.info(f"Processing PDF: {pdf_path}")
        text_parts = []
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                for i, image in enumerate(images):
                    # Save image to temp file (optional, but good for debugging or memory mgmt)
                    image_path = os.path.join(temp_dir, f"page_{i}.png")
                    image.save(image_path, "PNG")
                    
                    # Perform OCR
                    page_text = pytesseract.image_to_string(
                        Image.open(image_path),
                        lang='eng+hin',
                        config='--psm 6'
                    )
                    text_parts.append(page_text)
                    
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {e}")
            raise

    def _extract_from_image(self, image_path: str) -> str:
        """
        Extract text from an image file.
        """
        logger.info(f"Processing Image: {image_path}")
        try:
            text = pytesseract.image_to_string(
                Image.open(image_path),
                lang='eng+hin',
                config='--psm 6'
            )
            return text
        except Exception as e:
            logger.error(f"Error extracting from image {image_path}: {e}")
            raise
