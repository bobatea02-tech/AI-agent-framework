import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

# Add airflow home to path as requested and project root for src imports
sys.path.insert(0, '/opt/airflow')
# Add project root to path to ensure src can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

from src.executors.ocr_executor import OCRExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.validation_executor import ValidationExecutor
from src.database.connection import get_db_context
from src.database.models import WorkflowExecution, TaskExecution

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def update_execution_status(execution_id: str, status: str, output: Dict = None, error: str = None):
    """Helper to update workflow execution status in DB."""
    try:
        with get_db_context() as session:
            execution = session.query(WorkflowExecution).filter_by(execution_id=execution_id).first()
            if execution:
                execution.status = status
                if output:
                    execution.output_data = output
                if error:
                    execution.error_message = error
                
                if status == 'running' and execution.started_at is None:
                    execution.started_at = datetime.utcnow()
                elif status in ['completed', 'failed']:
                     execution.completed_at = datetime.utcnow()
                     if execution.started_at:
                         execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            else:
                logger.error(f"Execution ID {execution_id} not found")
    except Exception as e:
        logger.error(f"Failed to update execution status: {e}")

def extract_text_ocr(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    documents = conf.get('documents', [])
    
    if execution_id:
        update_execution_status(execution_id, 'running')
    
    executor = OCRExecutor()
    # Input expected by OCRExecutor: {"documents": [...]}
    result = executor.run_with_monitoring({"documents": documents})
    
    if result.get("status") == "failed":
        if execution_id:
             update_execution_status(execution_id, 'failed', error=result.get("error"))
        raise RuntimeError(f"OCR Failed: {result.get('error')}")
        
    # Push text and other info to XCom
    ti.xcom_push(key='ocr_result', value=result)

def classify_documents(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    
    ocr_result = ti.xcom_pull(task_ids='extract_text_ocr', key='ocr_result')
    if not ocr_result or not ocr_result.get("output"):
         raise ValueError("Missing OCR result")

    text = ocr_result["output"].get("text", "")
    
    executor = LLMExecutor()
    # Input expected by LLMExecutor for classify: {"task_type": "classify", "text": ...}
    result = executor.run_with_monitoring({"task_type": "classify", "text": text})
    
    if result.get("status") == "failed":
        if execution_id:
            update_execution_status(execution_id, 'failed', error=result.get("error"))
        raise RuntimeError(f"Classification Failed: {result.get('error')}")

    ti.xcom_push(key='classification_result', value=result)

def extract_fields(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    
    ocr_result = ti.xcom_pull(task_ids='extract_text_ocr', key='ocr_result')
    classification_result = ti.xcom_pull(task_ids='classify_documents', key='classification_result')
    
    text = ocr_result["output"].get("text", "")
    doc_type = classification_result["output"].get("document_type")
    
    executor = LLMExecutor()
    # Input expected by LLMExecutor for extract: {"task_type": "extract", "text": ..., "document_type": ...}
    result = executor.run_with_monitoring({
        "task_type": "extract", 
        "text": text,
        "document_type": doc_type
    })
    
    if result.get("status") == "failed":
        if execution_id:
            update_execution_status(execution_id, 'failed', error=result.get("error"))
        raise RuntimeError(f"Extraction Failed: {result.get('error')}")

    ti.xcom_push(key='extraction_result', value=result)

def validate_data(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    
    extraction_result = ti.xcom_pull(task_ids='extract_fields', key='extraction_result')
    data = extraction_result["output"]
    
    executor = ValidationExecutor()
    # Input expected: {"data": ...}
    result = executor.run_with_monitoring({"data": data})
    
    if result.get("status") == "failed":
        if execution_id:
            update_execution_status(execution_id, 'failed', error=result.get("error"))
        raise RuntimeError(f"Validation Execution Failed: {result.get('error')}")

    # Note: ValidationExecutor returns 'output' which contains 'is_valid'. 
    # If is_valid is False, it's still a successful execution of the validator, but the data is invalid.
    # We might want to pass this validation report downstream.
    
    ti.xcom_push(key='validation_result', value=result)

def save_results(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    
    validation_result = ti.xcom_pull(task_ids='validate_data', key='validation_result')
    extraction_result = ti.xcom_pull(task_ids='extract_fields', key='extraction_result')
    
    final_output = {
        "extracted_data": extraction_result.get("output"),
        "validation_report": validation_result.get("output")
    }
    
    if execution_id:
        update_execution_status(execution_id, 'completed', output=final_output)

with DAG(
    dag_id='form_filling_workflow',
    default_args=default_args,
    schedule_interval=None,
    max_active_runs=10,
    tags=['agent', 'form-filling'],
    catchup=False
) as dag:

    task_ocr = PythonOperator(
        task_id='extract_text_ocr',
        python_callable=extract_text_ocr
    )

    task_classify = PythonOperator(
        task_id='classify_documents',
        python_callable=classify_documents
    )

    task_extract = PythonOperator(
        task_id='extract_fields',
        python_callable=extract_fields
    )

    task_validate = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data
    )

    task_save = PythonOperator(
        task_id='save_results',
        python_callable=save_results
    )

    task_ocr >> task_classify >> task_extract >> task_validate >> task_save
