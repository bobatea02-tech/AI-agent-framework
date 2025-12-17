from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (  # pyright: ignore[reportMissingImports]
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import declarative_base, relationship  # pyright: ignore[reportMissingImports]


Base = declarative_base()


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowDefinition(Base):
    """Stored definition of a workflow (TaskFlow JSON, config, metadata)."""

    __tablename__ = "workflow_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(64), nullable=False, default="v1")
    task_flow = Column(JSON, nullable=False)  # raw TaskFlow / DAG definition
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255), nullable=True)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    agents = relationship("AgentDefinition", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowExecution(Base):
    """One run of a workflow definition."""

    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(String(255), unique=True, nullable=False, index=True)

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False, index=True)
    workflow_version = Column(String(64), nullable=False)

    status = Column(SAEnum(WorkflowStatus, name="workflow_status"), nullable=False, default=WorkflowStatus.PENDING)
    priority = Column(Integer, nullable=False, default=0)

    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)

    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    submitted_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    submitted_by = Column(String(255), nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="executions")
    tasks = relationship("TaskExecution", back_populates="execution", cascade="all, delete-orphan")


class TaskExecution(Base):
    """Execution record for a single task within a workflow execution."""

    __tablename__ = "task_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    task_id = Column(String(255), nullable=False)  # logical task identifier from the workflow
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False, index=True)

    task_name = Column(String(255), nullable=True)
    executor = Column(String(255), nullable=False)
    status = Column(SAEnum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.PENDING)

    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)

    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Dependencies between tasks within the same execution (list of task_ids)
    depends_on = Column(JSON, nullable=True)

    metadata = Column(JSON, nullable=True)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="tasks")


class AgentDefinition(Base):
    """Definition of an agent that is backed by a workflow."""

    __tablename__ = "agent_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), unique=True, nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(64), nullable=False, default="v1")
    agent_type = Column(String(128), nullable=False)  # e.g. "form_filling", "knowledge_qa"

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False)

    capabilities = Column(JSON, nullable=True)  # JSON array of capability descriptors
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    workflow = relationship("WorkflowDefinition", back_populates="agents")



