from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

from .dag import DAG


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StateMachine:
    """Simple state machine to track task execution state for a DAG.

    Responsibilities:
    - Track each task's state (pending, running, succeeded, failed, skipped)
    - Store per-task results and errors
    - Determine which tasks are runnable (all upstream tasks succeeded)
    - Serialize/deserialize state
    """

    dag: DAG
    states: Dict[str, TaskState] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate the DAG (edges reference known tasks)
        self.dag.validate()

        # Initialize missing task states to PENDING
        for tid in self.dag.tasks.keys():
            self.states.setdefault(tid, TaskState.PENDING)

        # Ensure there is no cycle (topological sort will raise if there is)
        _ = self.dag.topological_sort()

    def is_runnable(self, task_id: str) -> bool:
        """Return True if the task is ready to run: it's pending and all upstream tasks succeeded."""
        if self.states.get(task_id) != TaskState.PENDING:
            return False

        # If no upstream dependencies, it's runnable
        upstream = self.dag.upstream(task_id)
        if not upstream:
            return True

        # All upstream must be SUCCEEDED
        for u in upstream:
            if self.states.get(u) != TaskState.SUCCEEDED:
                return False
        return True

    def next_runnable(self, limit: Optional[int] = None) -> List[str]:
        """Return a list of runnable task ids, ordered by DAG topological order.

        If `limit` is provided, return at most `limit` tasks.
        """
        order = self.dag.topological_sort()
        runnable = [tid for tid in order if self.is_runnable(tid)]
        if limit is not None:
            return runnable[:limit]
        return runnable

    def mark_running(self, task_id: str) -> None:
        self._ensure_known(task_id)
        if self.states.get(task_id) != TaskState.PENDING:
            raise RuntimeError(f"Cannot mark task {task_id} running from state {self.states.get(task_id)}")
        self.states[task_id] = TaskState.RUNNING

    def mark_succeeded(self, task_id: str, result: Any = None) -> None:
        self._ensure_known(task_id)
        self.states[task_id] = TaskState.SUCCEEDED
        if result is not None:
            self.results[task_id] = result

    def mark_failed(self, task_id: str, error: str | Exception) -> None:
        self._ensure_known(task_id)
        self.states[task_id] = TaskState.FAILED
        self.errors[task_id] = str(error)

    def mark_skipped(self, task_id: str, reason: Optional[str] = None) -> None:
        self._ensure_known(task_id)
        self.states[task_id] = TaskState.SKIPPED
        if reason:
            self.errors[task_id] = reason

    def all_done(self) -> bool:
        """Return True when no tasks remain pending or running."""
        for s in self.states.values():
            if s in (TaskState.PENDING, TaskState.RUNNING):
                return False
        return True

    def _ensure_known(self, task_id: str) -> None:
        if task_id not in self.states:
            raise KeyError(f"Unknown task id: {task_id}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "states": {tid: state.value for tid, state in self.states.items()},
            "results": self.results,
            "errors": self.errors,
            "dag": self.dag.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateMachine":
        dag = DAG.from_dict(data.get("dag", {}))
        sm = cls(dag=dag)
        # load states
        for tid, st in data.get("states", {}).items():
            try:
                sm.states[tid] = TaskState(st)
            except ValueError:
                # unknown state string -> keep as pending
                sm.states[tid] = TaskState.PENDING
        sm.results = data.get("results", {}) or {}
        sm.errors = data.get("errors", {}) or {}
        return sm
