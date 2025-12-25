from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskDefinition(BaseModel):
    id: str
    executor: str = Field(..., description="Executor identifier, e.g. OCRExecutor")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    retry: int = Field(3, ge=0)
    timeout: int = Field(30, ge=1, description="Timeout in seconds")
    depends_on: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("task id must be non-empty")
        return v


class TaskFlow(BaseModel):
    workflow_id: str
    tasks: List[TaskDefinition]

    @model_validator(mode='after')
    def validate_dependencies(self) -> TaskFlow:
        task_ids = {t.id for t in self.tasks}
        for task in self.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    raise ValueError(f"Task '{task.id}' depends on unknown task '{dep}'")
        return self

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



class TaskFlowParser:
    """Parses and validates workflow definitions."""

    def parse_workflow(self, workflow_path: str) -> Dict[str, Any]:
        """
        Loads workflow definition from JSON file, validates it, and resolves dependencies.

        Args:
            workflow_path: Path to the workflow JSON file.

        Returns:
            Dict containing the parsed workflow definition.
        """
        import json

        path = Path(workflow_path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in workflow file: {e}")

        if not self.validate_task_flow(workflow_data):
           raise ValueError("Invalid task flow structure")

        tasks = workflow_data.get("tasks", [])
        self.resolve_dependencies(tasks)
        
        return workflow_data

    def validate_task_flow(self, task_flow: Dict[str, Any]) -> bool:
        """
        Validates the structure of the task flow.

        Args:
            task_flow: The dictionary representation of the workflow.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(task_flow, dict):
             return False
        
        if "workflow_id" not in task_flow:
            return False

        if "tasks" not in task_flow or not isinstance(task_flow["tasks"], list):
            return False

        required_task_fields = {"id", "executor"}
        
        for task in task_flow["tasks"]:
            if not isinstance(task, dict):
                return False
            if not required_task_fields.issubset(task.keys()):
                 return False

        return True

    def resolve_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Resolves task dependencies and checks for circular references.

        Args:
            tasks: List of task definitions.

        Returns:
            Dictionary mapping task IDs to their dependencies.
        """
        task_ids = {task["id"] for task in tasks}
        dependencies = {}
        
        # Build dependency graph
        for task in tasks:
            task_id = task["id"]
            deps = task.get("depends_on", [])
            
            # Validate that all dependencies exist
            for dep in deps:
                if dep not in task_ids:
                    raise ValueError(f"Task '{task_id}' depends on unknown task '{dep}'")
            
            dependencies[task_id] = deps

        # Check for circular dependencies
        visited = set()
        path = set()
        
        def check_cycle(curr_task):
            visited.add(curr_task)
            path.add(curr_task)
            
            for neighbor in dependencies.get(curr_task, []):
                if neighbor not in visited:
                    if check_cycle(neighbor):
                        return True
                elif neighbor in path:
                     return True
            
            path.remove(curr_task)
            return False

        for task_id in task_ids:
            if task_id not in visited:
                if check_cycle(task_id):
                     raise ValueError("Circular dependency detected in workflow")

        return dependencies
