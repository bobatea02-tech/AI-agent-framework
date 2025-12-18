from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowSubmission(BaseModel):
    workflow_id: str = Field(..., description="Unique identifier for the workflow definition")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the workflow execution")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional configuration overrides")

    model_config = ConfigDict(from_attributes=True)


class WorkflowResponse(BaseModel):
    execution_id: str = Field(..., description="Unique identifier for the workflow execution")
    workflow_id: str = Field(..., description="ID of the submitted workflow")
    status: str = Field(..., description="Current status of the submission")
    submitted_at: datetime = Field(..., description="Timestamp when the workflow was submitted")
    message: str = Field(..., description="Submission status message")

    model_config = ConfigDict(from_attributes=True)


class WorkflowStatusResponse(BaseModel):
    execution_id: str = Field(..., description="Unique identifier for the execution")
    workflow_id: str = Field(..., description="ID of the workflow")
    status: WorkflowStatus = Field(..., description="Current status of the workflow")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information")
    submitted_at: datetime = Field(..., description="Timestamp when the workflow was submitted")
    started_at: Optional[datetime] = Field(None, description="Timestamp when the workflow started")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when the workflow completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(0, description="Number of retries attempted")

    model_config = ConfigDict(from_attributes=True)


class TaskResult(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    task_name: str = Field(..., description="Name of the task")
    status: str = Field(..., description="Status of the task")
    output: Optional[Dict[str, Any]] = Field(None, description="Output data from the task")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    retry_count: int = Field(0, description="Number of retries attempted")

    model_config = ConfigDict(from_attributes=True)


class WorkflowResults(BaseModel):
    execution_id: str = Field(..., description="Unique identifier for the execution")
    workflow_id: str = Field(..., description="ID of the workflow")
    status: str = Field(..., description="Final status of the workflow")
    output: Optional[Dict[str, Any]] = Field(None, description="Final output of the workflow")
    tasks: List[TaskResult] = Field(default_factory=list, description="List of task results")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="System health status")
    timestamp: datetime = Field(..., description="Current server time")
    services: Dict[str, str] = Field(..., description="Status of dependent services")

    model_config = ConfigDict(from_attributes=True)


class AgentInfo(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent")
    version: str = Field(..., description="Version of the agent")
    capabilities: List[str] = Field(..., description="List of agent capabilities")

    model_config = ConfigDict(from_attributes=True)
