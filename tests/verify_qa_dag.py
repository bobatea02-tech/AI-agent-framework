import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['airflow'] = MagicMock()
sys.modules['airflow.operators.python'] = MagicMock()
sys.modules['airflow.models'] = MagicMock()
sys.modules['openai'] = MagicMock()
# Mock executors if they import specific libs
sys.modules['pdf2image'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()

# Mock DAG context manager
mock_dag = MagicMock()
mock_dag.__enter__ = MagicMock(return_value=mock_dag)
mock_dag.__exit__ = MagicMock(return_value=None)
sys.modules['airflow'].DAG = MagicMock(return_value=mock_dag)

# Add src to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

class TestQADAGStructure(unittest.TestCase):
    def test_dag_loading(self):
        print("Attempting to import QA DAG...")
        try:
            from src.airflow.dags import knowledge_qa_dag
            print("Import successful.")
            
            # Verify tasks
            python_operator_mock = sys.modules['airflow.operators.python'].PythonOperator
            
            # Check tasks: preprocess_query, generate_answer, save_results
            task_ids = [call.kwargs['task_id'] for call in python_operator_mock.call_args_list]
            expected_ids = ['preprocess_query', 'generate_answer', 'save_results']
            
            for tid in expected_ids:
                self.assertIn(tid, task_ids)
                print(f"Found task: {tid}")

        except ImportError as e:
            self.fail(f"Failed to import DAG: {e}")
        except Exception as e:
            self.fail(f"DAG definition raised exception: {e}")

if __name__ == "__main__":
    unittest.main()
