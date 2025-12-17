from __future__ import annotations

import os
from typing import Any, Dict

from celery import Celery

from src.api.schemas import WorkflowRequest
from src.core.orchestrator import Orchestrator
from src.core.state_manager import StateManager
from src.core.task_flow import TaskFlow
from src.executors.api_caller_executor import APICallerExecutor
from src.executors.database_executor import DatabaseExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.ocr_executor import OCRExecutor
from src.executors.rag_executor import RAGRetrieverExecutor
from src.executors.validation_executor import ValidationExecutor


celery_app = Celery(
    "agent_framework",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)


def _build_orchestrator() -> Orchestrator:
    executors: Dict[str, Any] = {
        "LLMExecutor": LLMExecutor(),
        "OCRExecutor": OCRExecutor(),
        "ValidationExecutor": ValidationExecutor(),
        "DatabaseExecutor": DatabaseExecutor(session_factory=lambda: None),
        "APICallerExecutor": APICallerExecutor(),
        "RAGRetrieverExecutor": RAGRetrieverExecutor(),
    }
    state_manager = StateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ttl_seconds=int(os.getenv("STATE_TTL_SECONDS", "3600")),
    )
    return Orchestrator(executors=executors, state_manager=state_manager)


@celery_app.task(name="execute_workflow_task")
def execute_workflow_task(request_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task that executes a workflow asynchronously."""
    req = WorkflowRequest(**request_payload)
    flow = TaskFlow(workflow_id=req.workflow_id, tasks=req.tasks)
    orchestrator = _build_orchestrator()
    result = orchestrator.execute(flow, req.input_data)
    return {
        "workflow_id": result.workflow_id,
        "output": result.outputs,
        "metrics": result.metrics,
        "errors": result.errors,
    }


