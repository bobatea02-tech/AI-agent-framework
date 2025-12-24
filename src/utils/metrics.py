from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Dict, Generator

from prometheus_client import Counter, Gauge, Histogram, REGISTRY
from prometheus_client import exposition

# --- Metrics Definitions ---

# Workflow Metrics
WORKFLOWS_SUBMITTED = Counter(
    "workflows_submitted_total",
    "Total number of workflows submitted",
    ["workflow_id"],
)

WORKFLOWS_COMPLETED = Counter(
    "workflows_completed_total",
    "Total number of workflows completed",
    ["workflow_id", "status"],
)

WORKFLOW_DURATION = Histogram(
    "workflow_duration_seconds",
    "Time taken for workflow to complete",
    ["workflow_id"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, float("inf")),
)

ACTIVE_WORKFLOWS = Gauge(
    "active_workflows",
    "Number of currently running workflows",
    ["workflow_id"],
)

# Task Metrics
TASK_EXECUTIONS = Counter(
    "task_executions_total",
    "Total number of task executions",
    ["executor", "status"],
)

TASK_DURATION = Histogram(
    "task_duration_seconds",
    "Time taken for task execution",
    ["executor"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, float("inf")),
)


# --- Helper Functions ---

def record_workflow_submission(workflow_id: str) -> None:
    """Increment submitted counter and active gauge."""
    WORKFLOWS_SUBMITTED.labels(workflow_id=workflow_id).inc()
    ACTIVE_WORKFLOWS.labels(workflow_id=workflow_id).inc()


def record_workflow_completion(workflow_id: str, status: str, duration: float) -> None:
    """
    Record workflow completion stats.
    
    Args:
        workflow_id: ID of the workflow definition.
        status: Final status (completed/failed).
        duration: Duration in seconds.
    """
    WORKFLOWS_COMPLETED.labels(workflow_id=workflow_id, status=status).inc()
    WORKFLOW_DURATION.labels(workflow_id=workflow_id).observe(duration)
    # Decrement active gauge, ensuring it doesn't go below 0 (though Gauge allows textually, logic implies 0 floor)
    ACTIVE_WORKFLOWS.labels(workflow_id=workflow_id).dec()


def record_task_execution(executor: str, status: str, duration: float) -> None:
    """
    Record task execution stats.
    
    Args:
        executor: Name of the executor (e.g. LLMExecutor).
        status: Task status (success/failure).
        duration: Duration in seconds.
    """
    TASK_EXECUTIONS.labels(executor=executor, status=status).inc()
    TASK_DURATION.labels(executor=executor).observe(duration)


@contextmanager
def track_task_duration(executor: str) -> Generator[None, None, None]:
    """Context manager to auto-track task duration."""
    start_time = time.time()
    try:
        yield
        status = "success"
    except Exception:
        status = "failure"
        raise
    finally:
        duration = time.time() - start_time
        record_task_execution(executor, status, duration)
