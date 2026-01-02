import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Enum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class WorkflowDefinition(Base):
    __tablename__ = 'workflow_definitions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(String)
    task_flow = Column(JSON, nullable=False)
    config = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow_definition")
    agents = relationship("AgentDefinition", back_populates="workflow_definition")

class WorkflowExecution(Base):
    __tablename__ = 'workflow_executions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(String, unique=True, nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow_definitions.id'), nullable=False)
    workflow_version = Column(String)
    status = Column(Enum('pending', 'queued', 'running', 'completed', 'failed', 'cancelled', name='workflow_status_enum', create_type=False), default='pending')
    priority = Column(Integer, default=0)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    error_stack = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    submitted_by = Column(String)
    meta_data = Column("metadata", JSON)

    # Relationships
    workflow_definition = relationship("WorkflowDefinition", back_populates="executions")
    task_executions = relationship("TaskExecution", back_populates="workflow_execution")

class TaskExecution(Base):
    __tablename__ = 'task_executions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, nullable=False)
    execution_id = Column(UUID(as_uuid=True), ForeignKey('workflow_executions.id'), nullable=False)
    task_name = Column(String, nullable=False)
    executor = Column(String)
    status = Column(String) # User didn't specify enum for this, but likely similar to workflow status
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    error_stack = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    depends_on = Column(JSON) # Array stored as JSON
    meta_data = Column("metadata", JSON)

    # Relationships
    workflow_execution = relationship("WorkflowExecution", back_populates="task_executions")

class AgentDefinition(Base):
    __tablename__ = 'agent_definitions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(String)
    agent_type = Column(String)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('workflow_definitions.id'))
    capabilities = Column(JSON) # JSON array
    config = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow_definition = relationship("WorkflowDefinition", back_populates="agents")


class ModelOptimization(Base):
    __tablename__ = 'model_optimizations'

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    framework = Column(String, nullable=False) # OpenVINO, Tesseract, etc.
    precision = Column(String) # FP32, FP16, INT8
    latency_ms = Column(Float)
    throughput_rps = Column(Float)
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
