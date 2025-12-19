import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock dependencies BEFORE importing anything from src
sys.modules['airflow'] = MagicMock()
sys.modules['airflow.operators.python'] = MagicMock()
sys.modules['airflow.models'] = MagicMock()

# Mock Executor dependencies
sys.modules['pdf2image'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['openai'] = MagicMock()

# Mock Database dependencies (optional, but safer if environment is thin)
# We won't mock sqlalchemy completely because models might need real classes if possible, 
# but if sqlalchemy is missing, we must mock it.
# Check if sqlalchemy matches
try:
    import sqlalchemy
except ImportError:
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.orm'] = MagicMock()
    sys.modules['sqlalchemy.dialects.postgresql'] = MagicMock()
    sys.modules['dotenv'] = MagicMock()

# Mock DAG context manager behavior
mock_dag = MagicMock()
mock_dag.__enter__ = MagicMock(return_value=mock_dag)
mock_dag.__exit__ = MagicMock(return_value=None)
sys.modules['airflow'].DAG = MagicMock(return_value=mock_dag)

# Add src to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

class TestDAGStructure(unittest.TestCase):
    def test_dag_loading(self):
        print("Attempting to import DAG...")
        try:
            from src.airflow.dags import form_filling_dag
            print("Import successful.")
            
            # Verify tasks are created
            python_operator_mock = sys.modules['airflow.operators.python'].PythonOperator
            
            # Check if PythonOperator was called 5 times
            self.assertEqual(python_operator_mock.call_count, 5, "PythonOperator should be called 5 times")
            
            # Check task_ids
            task_ids = [call.kwargs['task_id'] for call in python_operator_mock.call_args_list]
            expected_ids = ['extract_text_ocr', 'classify_documents', 'extract_fields', 'validate_data', 'save_results']
            
            for tid in expected_ids:
                self.assertIn(tid, task_ids)
                print(f"Found task: {tid}")

        except ImportError as e:
            self.fail(f"Failed to import DAG: {e}")
        except Exception as e:
            self.fail(f"DAG definition raised exception: {e}")

if __name__ == "__main__":
    unittest.main()
