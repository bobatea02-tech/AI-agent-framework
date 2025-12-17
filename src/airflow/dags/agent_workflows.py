from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator  # pyright: ignore[reportMissingImports]

from src.api.schemas import WorkflowRequest, TaskInput
from src.kafka.producer import default_producer


def trigger_workflow(**context):
    """Airflow task that enqueues a sample workflow via Kafka."""
    producer = default_producer()

    # Example: trigger the knowledge_qa workflow defined in workflows/knowledge_qa_flow.json
    workflow = WorkflowRequest(
        workflow_id="knowledge_qa_v1",
        tasks=[
            TaskInput(
                id="retrieve",
                executor="RAGRetrieverExecutor",
                inputs={"query": "${__input__.query}"},
            ),
            TaskInput(
                id="answer",
                executor="LLMExecutor",
                inputs={"context": "${retrieve}", "query": "${__input__.query}"},
                depends_on=["retrieve"],
            ),
        ],
        input_data={"query": "What is the capital of France?"},
    )

    producer.submit(workflow.dict())


default_args = {
    "owner": "ai-agent-framework",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="agent_workflows",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:
    trigger = PythonOperator(
        task_id="trigger_agent_workflow",
        python_callable=trigger_workflow,
    )


