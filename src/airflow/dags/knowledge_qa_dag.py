import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

# Add airflow home to path and project root
sys.path.insert(0, '/opt/airflow')
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.executors.llm_executor import LLMExecutor
from src.database.connection import get_db_context
from src.database.models import WorkflowExecution

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
                     # Merge or overwrite output. For simple flow, overwrite.
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

def preprocess_query(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    query = conf.get('query')
    
    if execution_id:
        update_execution_status(execution_id, 'running')
        
    if not query:
        err = "Missing 'query' in DAG input"
        if execution_id:
             update_execution_status(execution_id, 'failed', error=err)
        raise ValueError(err)

    # Basic cleanup
    cleaned_query = query.strip()
    ti.xcom_push(key='cleaned_query', value=cleaned_query)

def generate_answer(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    
    cleaned_query = ti.xcom_pull(task_ids='preprocess_query', key='cleaned_query')
    
    executor = LLMExecutor()
    # Using generic completion. In future, this will involve RAG retrieval first.
    prompt = f"Answer the following question based on your general knowledge (RAG placeholder): {cleaned_query}"
    
    result = executor.run_with_monitoring({
        "task_type": "completion",
        "prompt": prompt,
        "model": "gpt-4o-mini"
    })
    
    if result.get("status") == "failed":
        if execution_id:
            update_execution_status(execution_id, 'failed', error=result.get("error"))
        raise RuntimeError(f"Answer Generation Failed: {result.get('error')}")

    ti.xcom_push(key='generated_answer', value=result)

def save_results(ti, **context):
    conf = context.get('dag_run').conf or {}
    execution_id = conf.get('execution_id')
    
    answer_result = ti.xcom_pull(task_ids='generate_answer', key='generated_answer')
    
    final_output = {
        "answer": answer_result.get("output", {}).get("content"),
        "raw_result": answer_result
    }
    
    if execution_id:
        update_execution_status(execution_id, 'completed', output=final_output)

with DAG(
    dag_id='knowledge_qa_workflow',
    default_args=default_args,
    schedule_interval=None,
    max_active_runs=10,
    tags=['agent', 'knowledge-qa', 'rag'],
    catchup=False
) as dag:

    task_preprocess = PythonOperator(
        task_id='preprocess_query',
        python_callable=preprocess_query
    )

    task_generate = PythonOperator(
        task_id='generate_answer',
        python_callable=generate_answer
    )

    task_save = PythonOperator(
        task_id='save_results',
        python_callable=save_results
    )

    task_preprocess >> task_generate >> task_save
