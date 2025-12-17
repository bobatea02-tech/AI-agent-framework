from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    id: str
    executor: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    retry: int = 3
    timeout: int = 60
    depends_on: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    workflow_id: str
    tasks: List[TaskInput]
    input_data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


