import sys
import os
import logging
import unittest

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.executors.validation_executor import ValidationExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestValidationExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = ValidationExecutor()

    def test_valid_data(self):
        print("\nTesting Valid Data...")
        data = {
            "aadhaar_number": "123456789012",
            "pan_number": "ABCDE1234F",
            "dob": "01/01/2000",
            "name": "John Doe",
            "extra_field": "ignored"
        }
        inputs = {"data": data}
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["fields_validated"], 4)

    def test_invalid_data(self):
        print("\nTesting Invalid Data...")
        data = {
            "aadhaar_number": "123", # Too short
            "pan_number": "12345",   # Invalid format
            "dob": "2000-01-01",     # Invalid format (expects DD/MM/YYYY)
            "name": "John123"        # Contains number
        }
        inputs = {"data": data}
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertFalse(result["is_valid"])
        self.assertEqual(len(result["errors"]), 4)

    def test_empty_warning(self):
        print("\nTesting Empty Warning...")
        data = {
            "name": ""
        }
        inputs = {"data": data}
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertTrue(result["is_valid"]) # Assuming empty doesn't fail validation by default rule, just warns. 
        # Actually pattern ^[A-Za-z\s]+$ requires at least 1 char. So empty string fails regex AND triggers empty check?
        # My code checks if empty/None FIRST, adds warning, and DOES continue? No, "continue" keyword is used in the implementation:
        # if value is None or ...: warnings.append(...); continue
        # So it skips validation pattern check. Thus valid=True but with warning.
        
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(len(result["errors"]), 0)

    def test_custom_rules(self):
        print("\nTesting Custom Rules...")
        data = {
            "custom_field": "123"
        }
        rules = {
            "custom_field": r"^\d+$"
        }
        inputs = {"data": data, "rules": rules}
        result = self.executor.execute(inputs)
        print(f"Result: {result}")
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["fields_validated"], 1)

if __name__ == "__main__":
    unittest.main()
