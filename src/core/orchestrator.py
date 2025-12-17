from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping, Optional

from .dag import DAG, TaskNode
from .state_machine import StateMachine, TaskState
from .state_manager import StateManager
from .task_flow import TaskFlow, TaskDefinition

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    """Standard result payload returned by the orchestrator."""

    workflow_id: str
    outputs: Dict[str, Any]
    metrics: Dict[str, Any]
    errors: Dict[str, str]


class Orchestrator:
    """Core orchestration engine for TaskFlow-based workflows.

    Responsibilities:
    - Parse TaskFlow into a DAG
    - Use StateMachine to determine runnable tasks
    - Execute tasks via injected executors with retries
    - Resolve inputs from prior task outputs (and initial input)
    - Persist state via StateManager (optional)
    - Collect execution metrics
    """

    def __init__(
        self,
        executors: Mapping[str, Any],
        state_manager: Optional[StateManager] = None,
    ) -> None:
        """
        Args:
            executors: Mapping from executor name -> executor instance
                       (e.g. {"LLMExecutor": llm_exec, "OCRExecutor": ocr_exec})
            state_manager: Optional StateManager for persistence/checkpointing
        """
        self._executors = dict(executors)
        self._state_manager = state_manager

    # Public API -----------------------------------------------------

    def execute(self, flow: TaskFlow, input_data: Dict[str, Any]) -> OrchestratorResult:
        """Execute a workflow described by a TaskFlow.

        This is a synchronous, in-process runner suitable as a default
        orchestrator when Airflow/Celery are not used.
        """
        logger.info("Starting workflow %s", flow.workflow_id)
        started_at = time.time()

        dag, task_index = self._build_dag(flow)
        sm = StateMachine(dag=dag)

        # Seed initial input into state machine results
        sm.results["__input__"] = input_data

        task_durations: Dict[str, float] = {}
        task_statuses: Dict[str, str] = {}

        # Main execution loop: run while there is runnable work
        while not sm.all_done():
            runnable = sm.next_runnable()
            if not runnable:
                # No runnable tasks but not all done -> deadlock / failure
                logger.error("No runnable tasks but workflow not complete; breaking")
                break

            for task_id in runnable:
                task_def = task_index[task_id]
                self._run_single_task(task_def, sm, task_durations, task_statuses)

                # Persist state after each task if a manager is configured
                if self._state_manager:
                    try:
                        self._state_manager.save_state(flow.workflow_id, sm.to_dict())
                    except Exception as e:  # pragma: no cover - defensive
                        logger.warning("Failed to persist state for %s: %s", flow.workflow_id, e)

        total_duration_ms = (time.time() - started_at) * 1000.0
        metrics = {
            "total_duration_ms": total_duration_ms,
            "task_durations": task_durations,
            "task_statuses": task_statuses,
        }

        logger.info("Workflow %s finished in %.2fms", flow.workflow_id, total_duration_ms)
        return OrchestratorResult(
            workflow_id=flow.workflow_id,
            outputs=sm.results,
            metrics=metrics,
            errors=sm.errors,
        )

    # Internal helpers -----------------------------------------------

    def _build_dag(self, flow: TaskFlow) -> tuple[DAG, Dict[str, TaskDefinition]]:
        """Build a DAG and a quick index from a TaskFlow."""
        tasks = [TaskNode(id=t.id, type=t.executor, config=t.config, inputs=t.inputs) for t in flow.tasks]
        edges = flow.as_dag_edges()
        dag = DAG(tasks=tasks, edges=edges)
        index = {t.id: t for t in flow.tasks}
        return dag, index

    def _run_single_task(
        self,
        task: TaskDefinition,
        sm: StateMachine,
        task_durations: Dict[str, float],
        task_statuses: Dict[str, str],
    ) -> None:
        """Execute one task with retries and basic error handling."""
        tid = task.id
        logger.info("Running task %s with executor %s", tid, task.executor)

        if not sm.is_runnable(tid):
            logger.debug("Task %s is not runnable, skipping for now", tid)
            return

        sm.mark_running(tid)
        executor = self._executors.get(task.executor)
        if executor is None:
            err = f"No executor registered for '{task.executor}'"
            logger.error(err)
            sm.mark_failed(tid, err)
            task_statuses[tid] = TaskState.FAILED.value
            return

        attempt = 0
        last_error: Optional[Exception] = None
        start_time = time.time()

        while attempt <= task.retry:
            attempt += 1
            try:
                resolved_inputs = self._resolve_inputs(task.inputs, sm.results)
                result = executor.execute(task.config, resolved_inputs)
                duration_ms = (time.time() - start_time) * 1000.0
                task_durations[tid] = duration_ms
                sm.mark_succeeded(tid, result)
                task_statuses[tid] = TaskState.SUCCEEDED.value
                logger.info("Task %s succeeded in %.2fms (attempt %d)", tid, duration_ms, attempt)
                return
            except Exception as e:  # pragma: no cover - runtime behavior
                last_error = e
                logger.warning("Task %s failed on attempt %d: %s", tid, attempt, e)
                if attempt > task.retry:
                    break
                # Simple backoff: sleep proportional to attempt number
                time.sleep(min(1.0 * attempt, 5.0))

        # If we arrive here, all retries failed
        duration_ms = (time.time() - start_time) * 1000.0
        task_durations[tid] = duration_ms
        sm.mark_failed(tid, last_error or "unknown error")
        task_statuses[tid] = TaskState.FAILED.value
        logger.error("Task %s ultimately failed after %.2fms", tid, duration_ms)

    def _resolve_inputs(self, inputs: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve `${task_id.output}`-style references from previous results.

        The left part before the dot is treated as a task id. The right part
        is treated as a key within that task's result (if the result is a dict).
        A special `__input__` task id refers to the original workflow input.
        """
        resolved: Dict[str, Any] = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                ref = value[2:-1]  # strip ${ }
                task_id, _, field = ref.partition(".")
                source = results.get(task_id)
                if isinstance(source, dict) and field:
                    resolved[key] = source.get(field)
                else:
                    resolved[key] = source
            else:
                resolved[key] = value
        return resolved
