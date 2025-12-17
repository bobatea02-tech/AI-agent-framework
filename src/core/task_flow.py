from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class TaskDefinition(BaseModel):
    id: str
    executor: str = Field(..., description="Executor identifier, e.g. OCRExecutor")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    retry: int = Field(3, ge=0)
    timeout: int = Field(30, ge=1, description="Timeout in seconds")
    depends_on: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)

    @validator("id")
    def non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("task id must be non-empty")
        return v


class TaskFlow(BaseModel):
    workflow_id: str
    tasks: List[TaskDefinition]

    @root_validator
    def validate_dependencies(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        task_ids = {t.id for t in values.get("tasks", [])}
        for task in values.get("tasks", []):
            for dep in task.depends_on:
                if dep not in task_ids:
                    raise ValueError(f"Task '{task.id}' depends on unknown task '{dep}'")
        return values

    def as_dag_edges(self) -> List[tuple]:
        """Return list of edges (dependency -> task)."""
        edges: List[tuple] = []
        for task in self.tasks:
            for dep in task.depends_on:
                edges.append((dep, task.id))
        return edges


def load_task_flow(path: str | Path) -> TaskFlow:
    """Load a workflow definition from JSON or YAML."""
    import json

    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    data: Dict[str, Any]
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml  # type: ignore

        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)
    return TaskFlow(**data)


