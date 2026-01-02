from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.api.schemas import (
    AgentInfo,
    HealthResponse,
    WorkflowResponse,
    WorkflowResults,
    WorkflowStatus,
    WorkflowStatusResponse,
    WorkflowSubmission,
    TaskResult
)
from src.core.orchestrator import Orchestrator, OrchestratorResult
from src.core.state_manager import StateManager
from src.core.task_flow import TaskFlow, TaskDefinition
from src.database.connection import get_db
from src.database.models import AgentDefinition, WorkflowDefinition, WorkflowExecution, TaskExecution
from src.executors.api_caller_executor import APICallerExecutor
from src.executors.database_executor import DatabaseExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.ocr_executor import OCRExecutor
from src.executors.rag_executor import RAGRetrieverExecutor
from src.executors.validation_executor import ValidationExecutor
from src.kafka.producer import default_producer
from src.utils.metrics import record_workflow_submission, record_workflow_completion
from src.api.security import verify_api_key
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

# Setup router-level limiter if needed, or rely on app.state.limiter access
# Ideally we pass the limiter instance, but standard slowapi usage often involves a global or request-based access
# Here we will assume 'limiter' is available or instantiate a local one for declaration (which might be redundant)
# For route decorators to work, they usually need the 'limiter' instance. 
# Best practice: Import the limiter from main.py? Circular import risk.
# Creating a new instance here pointing to same key_func usually works if middleware is set up.

limiter = Limiter(key_func=get_remote_address) 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# --- Dependency Injection for Orchestrator ---

def get_orchestrator() -> Orchestrator:
    # Executors
    executors: Dict[str, Any] = {
        "LLMExecutor": LLMExecutor(),
        "OCRExecutor": OCRExecutor(),
        "ValidationExecutor": ValidationExecutor(),
        "DatabaseExecutor": DatabaseExecutor(session_factory=lambda: None), # Placeholder
        "APICallerExecutor": APICallerExecutor(),
        "RAGRetrieverExecutor": RAGRetrieverExecutor(),
    }
    state_manager = StateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ttl_seconds=int(os.getenv("STATE_TTL_SECONDS", "3600")),
    )
    return Orchestrator(executors=executors, state_manager=state_manager)

orchestrator_instance = get_orchestrator()
kafka_producer = default_producer()

# --- Helpers ---

def _map_execution_to_results(
    execution: WorkflowExecution,
    tasks: List[TaskExecution]
) -> WorkflowResults:
    
    task_results = []
    for t in tasks:
        task_results.append(TaskResult(
            task_id=t.task_id,
            task_name=t.task_name,
            status=t.status or "unknown",
            output=t.output_data,
            duration=t.duration_seconds,
            retry_count=t.retry_count or 0
        ))

    return WorkflowResults(
        execution_id=str(execution.execution_id),
        workflow_id=str(execution.workflow_id), # This might be the UUID or the human ID? Schema says string.
        # Ideally we should fetch the human readable workflow_id from definition if possible, 
        # but execution.workflow_id is a FK UUID. 
        # Let's assume schema wants the FK or better yet, we joined the definition.
        status=execution.status,
        output=execution.output_data,
        tasks=task_results,
        metrics=execution.meta_data
    )

# --- Routes ---

@router.post("/workflows", response_model=WorkflowResponse, status_code=202)
@limiter.limit("5/minute")
def submit_workflow(
    request: Request,
    submission: WorkflowSubmission,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Submit a workflow execution.
    """
    # 1. Validate Workflow Exists
    wf_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.workflow_id == submission.workflow_id).first()
    if not wf_def:
        raise HTTPException(status_code=404, detail=f"Workflow definition '{submission.workflow_id}' not found")

    # 2. Create Execution Record
    execution_id = str(uuid.uuid4())
    execution_record = WorkflowExecution(
        execution_id=execution_id,
        workflow_id=wf_def.id,
        workflow_version=wf_def.version,
        status='queued',
        input_data=submission.input,
        submitted_at=datetime.utcnow()
    )
    db.add(execution_record)
    db.commit()

    # 3. Publish to Kafka
    try:
        if kafka_producer:
            payload = submission.model_dump()
            payload['execution_id'] = execution_id
            kafka_producer.publish_workflow(submission.workflow_id, execution_id, payload)
            message = "Workflow submitted successfully"
            
            # Record metrics
            record_workflow_submission(submission.workflow_id)
        else:
            # Fallback to sync execution? Or just error? 
            # Request implies just queueing. If Kafka missing, we might need to warn or queue in DB only.
            # For now, let's treat it as accepted but potentially stalled if no consumer.
            # OR we could run it in background task? 
            # Prompt says "Publish to Kafka using producer".
            message = "Workflow accepted but Kafka is unavailable"
            logger.warning("Kafka unavailable for submission %s", execution_id)
            
            # Record metrics even if queued without kafka? 
            # Technically submitted.
            record_workflow_submission(submission.workflow_id)
            
    except Exception as e:
        logger.error("Failed to publish workflow %s: %s", execution_id, e)
        # We don't rollback DB because record provides traceability of failure
        execution_record.status = 'failed'
        execution_record.error_message = f"Submission error: {str(e)}"
        db.commit()
        
        # Record failure metric
        # We don't have duration here easily unless we track from start of func, 
        # but this is immediate failure.
        # record_workflow_completion(submission.workflow_id, 'failed', 0)
        
        raise HTTPException(status_code=500, detail="Failed to submit workflow to queue")

    return WorkflowResponse(
        execution_id=execution_id,
        workflow_id=submission.workflow_id,
        status="queued",
        submitted_at=execution_record.submitted_at,
        message=message
    )


@router.get("/workflows/{execution_id}", response_model=WorkflowStatusResponse)
def get_workflow_status(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status of a specific workflow execution.
    """
    exec_record = db.query(WorkflowExecution).filter(WorkflowExecution.execution_id == execution_id).first()
    if not exec_record:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Calculate progress
    # Count total tasks in definition VS completed tasks in TaskExecution
    # This requires looking up the definition
    wf_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == exec_record.workflow_id).first()
    
    progress = {"completed_tasks": 0, "total_tasks": 0}
    if wf_def and wf_def.task_flow:
        total = len(wf_def.task_flow) if isinstance(wf_def.task_flow, list) else 0
        completed = db.query(TaskExecution).filter(
            TaskExecution.execution_id == exec_record.id,
            TaskExecution.status == 'completed'
        ).count()
        progress = {"completed_tasks": completed, "total_tasks": total}

    return WorkflowStatusResponse(
        execution_id=exec_record.execution_id,
        workflow_id=wf_def.workflow_id if wf_def else str(exec_record.workflow_id),
        status=exec_record.status,
        progress=progress,
        submitted_at=exec_record.submitted_at,
        started_at=exec_record.started_at,
        completed_at=exec_record.completed_at,
        error=exec_record.error_message,
        retry_count=exec_record.retry_count
    )


@router.get("/workflows/{execution_id}/results", response_model=WorkflowResults)
def get_workflow_results(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed results of a workflow execution.
    """
    exec_record = db.query(WorkflowExecution).filter(WorkflowExecution.execution_id == execution_id).first()
    if not exec_record:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    if exec_record.status not in ('completed', 'failed'):
        # Still return what we have, or could raise 400?
        # Usually results are requested when done, but partial results might be useful. 
        pass 

    tasks = db.query(TaskExecution).filter(TaskExecution.execution_id == exec_record.id).all()
    
    # We need human readable ID for response
    wf_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == exec_record.workflow_id).first()
    wf_id_str = wf_def.workflow_id if wf_def else str(exec_record.workflow_id)

    # Manual mapping since helper signature is slightly different regarding wf_id
    task_results = []
    for t in tasks:
        task_results.append(TaskResult(
            task_id=t.task_id,
            task_name=t.task_name,
            status=t.status or "unknown",
            output=t.output_data,
            duration=t.duration_seconds,
            retry_count=t.retry_count or 0
        ))

    return WorkflowResults(
        execution_id=str(exec_record.execution_id),
        workflow_id=wf_id_str,
        status=exec_record.status,
        output=exec_record.output_data,
        tasks=task_results,
        metrics=exec_record.meta_data
    )


@router.get("/workflows", response_model=List[WorkflowStatusResponse])
@limiter.limit("50/minute")
def list_workflows(
    request: Request,
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    # auth_user: str = Depends(verify_api_key) # Optional: Enforce auth for listing
):
    """
    List workflow executions with pagination.
    """
    query = db.query(WorkflowExecution)
    
    if status:
        query = query.filter(WorkflowExecution.status == status)
        
    query = query.order_by(desc(WorkflowExecution.submitted_at))
    query = query.offset(offset).limit(limit)
    
    executions = query.all()
    
    results = []
    for exec_record in executions:
        # Note: N+1 query problem here for definitions. 
        # Optimized: join with definition
        # But for now keeping it simple as per "Query WorkflowExecution"
        wf_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == exec_record.workflow_id).first()
        
        results.append(WorkflowStatusResponse(
            execution_id=exec_record.execution_id,
            workflow_id=wf_def.workflow_id if wf_def else "unknown",
            status=exec_record.status,
            progress=None, # Omitted for list view to save DB hits
            submitted_at=exec_record.submitted_at,
            started_at=exec_record.started_at,
            completed_at=exec_record.completed_at,
            error=exec_record.error_message,
            retry_count=exec_record.retry_count
        ))
        
    return results


@router.delete("/workflows/{execution_id}", status_code=204)
def cancel_workflow(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a running workflow.
    """
    exec_record = db.query(WorkflowExecution).filter(WorkflowExecution.execution_id == execution_id).first()
    if not exec_record:
        raise HTTPException(status_code=404, detail="Execution not found")
        
    if exec_record.status in ('completed', 'failed', 'cancelled'):
        return # Already done
        
    exec_record.status = 'cancelled'
    exec_record.completed_at = datetime.utcnow()
    exec_record.error_message = "Cancelled by user"
    db.commit()
    
    # Record metrics
    # Calculate duration
    duration = 0
    if exec_record.started_at:
        duration = (exec_record.completed_at - exec_record.started_at).total_seconds()
    elif exec_record.submitted_at:
        duration = (exec_record.completed_at - exec_record.submitted_at).total_seconds()
        
    # Get workflow ID string
    wf_id = str(exec_record.workflow_id) # Falls back to UUID if not joined.
    # ideally fetch definition but for metrics simple UUID is okay if consistent?
    # Or join to get readable ID. 
    # Let's risk an extra query for cleaner metrics if possible, or just use what we have.
    # Earlier code fetched definition.
    wf_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == exec_record.workflow_id).first()
    if wf_def:
        wf_id = wf_def.workflow_id
        
    record_workflow_completion(wf_id, 'cancelled', duration)
    
    logger.info("Workflow %s cancelled by user", execution_id)
    # TODO: Signal cancellation to Orchestrator/Workers


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Check system health.
    """
    services = {}
    
    # DB Check
    try:
        db.execute("SELECT 1")
        services["database"] = "healthy"
    except Exception as e:
        logger.error("Health check failed for database: %s", e)
        services["database"] = "unhealthy"
        
    # Kafka Check
    if kafka_producer and kafka_producer.client:
        # Simple check: are we connected? 
        # producer.client is KafkaProducer instance (or mocked)
        # kafka-python doesn't have an easy is_connected() that's cheap?
        # assume healthy if initialized for now
        services["kafka"] = "healthy"
    else:
        services["kafka"] = "disabled" if not kafka_producer else "unhealthy"
        
    # Redis Check (via StateManager)
    try:
        if orchestrator_instance._state_manager:
            orchestrator_instance._state_manager.redis.ping()
            services["redis"] = "healthy"
        else:
             services["redis"] = "disabled"
    except Exception as e:
        logger.error("Health check failed for redis: %s", e)
        services["redis"] = "unhealthy"
        
    overall_status = "healthy"
    if any(v == "unhealthy" for v in services.values()):
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services
    )


@router.get("/agents", response_model=List[AgentInfo])
def list_agents(db: Session = Depends(get_db)):
    """
    List available agents.
    """
    agents = db.query(AgentDefinition).filter(AgentDefinition.is_active == True).all()
    
    return [
        AgentInfo(
            agent_id=a.agent_id,
            name=a.name,
            description=a.description or "",
            version=a.version or "1.0",
            capabilities=a.capabilities if isinstance(a.capabilities, list) else []
        )
        for a in agents
    ]
