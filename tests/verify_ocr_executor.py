import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies BEFORE importing the module under test
sys.modules['pdf2image'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Now import the module
from src.executors.ocr_executor import OCRExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestOCRExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = OCRExecutor()

    def test_image_execution(self):
        """Test OCR on a standard image file."""
        print("\nTesting Image Execution...")
        
        # We need to mock the methods we use directly
        with patch('src.executors.ocr_executor.pytesseract.image_to_string') as mock_ocr, \
             patch('src.executors.ocr_executor.Image.open') as mock_open:
            
            mock_ocr.return_value = "Mocked Image Text"
            mock_open.return_value = MagicMock()
            
            # Create dummy file to pass os.path.exists check
            with open("test_image.png", "w") as f:
                f.write("dummy")
                
            try:
                inputs = {"documents": ["test_image.png"]}
                result = self.executor.execute(inputs)
                
                print(f"Result: {result}")
                
                self.assertEqual(result["total_documents"], 1)
                self.assertEqual(result["documents"][0]["status"], "success")
                self.assertEqual(result["documents"][0]["text"], "Mocked Image Text")
                self.assertEqual(result["text"], "Mocked Image Text")
            finally:
                if os.path.exists("test_image.png"):
                    os.remove("test_image.png")

    def test_pdf_execution(self):
        """Test OCR on a PDF file."""
        print("\nTesting PDF Execution...")
        
        with patch('src.executors.ocr_executor.pdf2image.convert_from_path') as mock_pdf_convert, \
             patch('src.executors.ocr_executor.pytesseract.image_to_string') as mock_ocr, \
             patch('src.executors.ocr_executor.Image.open') as mock_open:
            
            # Setup mocks
            mock_image = MagicMock()
            mock_image.save = MagicMock()
            mock_pdf_convert.return_value = [mock_image, mock_image] # 2 pages
            mock_ocr.side_effect = ["Page 1 Text", "Page 2 Text"]
            
            # Create dummy pdf
            with open("test_doc.pdf", "w") as f:
                f.write("dummy")
                
            try:
                inputs = {"documents": ["test_doc.pdf"]}
                result = self.executor.execute(inputs)
                
                print(f"Result: {result}")
                
                self.assertEqual(result["total_documents"], 1)
                self.assertEqual(result["documents"][0]["status"], "success")
                expected_text = "Page 1 Text\nPage 2 Text"
                self.assertEqual(result["documents"][0]["text"], expected_text)
                
            finally:
                if os.path.exists("test_doc.pdf"):
                    os.remove("test_doc.pdf")

    def test_input_validation(self):
        """Test input validation."""
        print("\nTesting Input Validation...")
        with self.assertRaises(ValueError):
            self.executor.execute({"documents": "not a list"})

    def test_file_not_found(self):
        """Test handling of missing files."""
        print("\nTesting File Not Found...")
        result = self.executor.execute({"documents": ["non_existent.png"]})
        print(f"Result: {result}")
        self.assertEqual(result["documents"][0]["status"], "error")
        self.assertEqual(result["documents"][0]["error"], "File not found")

if __name__ == "__main__":
    unittest.main()
