from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from src.api.schemas import WorkflowRequest, WorkflowResponse
from src.core.orchestrator import Orchestrator
from src.core.state_manager import StateManager
from src.core.task_flow import TaskFlow
from src.executors.api_caller_executor import APICallerExecutor
from src.executors.database_executor import DatabaseExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.ocr_executor import OCRExecutor
from src.executors.rag_executor import RAGRetrieverExecutor
from src.executors.validation_executor import ValidationExecutor
from src.kafka.producer import default_producer


app = FastAPI(title="AI Agent Framework", version="0.2.0")


def _build_orchestrator() -> Orchestrator:
    # Executors keyed by the names used in TaskFlow.executor
    executors: Dict[str, Any] = {
        "LLMExecutor": LLMExecutor(),
        "OCRExecutor": OCRExecutor(),
        "ValidationExecutor": ValidationExecutor(),
        # DatabaseExecutor is wired but requires a real session_factory in production
        "DatabaseExecutor": DatabaseExecutor(session_factory=lambda: None),
        "APICallerExecutor": APICallerExecutor(),
        "RAGRetrieverExecutor": RAGRetrieverExecutor(),
    }
    state_manager = StateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ttl_seconds=int(os.getenv("STATE_TTL_SECONDS", "3600")),
    )
    return Orchestrator(executors=executors, state_manager=state_manager)


orchestrator = _build_orchestrator()
producer = default_producer()


@app.post("/workflows/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """Synchronously execute a workflow described by a WorkflowRequest."""
    try:
        flow = TaskFlow(workflow_id=request.workflow_id, tasks=request.tasks)
        result = orchestrator.execute(flow, request.input_data)
        return WorkflowResponse(
            status="success",
            output=result.outputs,
            metrics=result.metrics,
            error=None if not result.errors else str(result.errors),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/enqueue", response_model=dict)
async def enqueue_workflow(request: WorkflowRequest) -> Dict[str, Any]:
    """Enqueue a workflow for async processing via Kafka."""
    try:
        payload = request.dict()
        producer.submit(payload)
        return {"status": "queued", "workflow_id": request.workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}
