from datetime import datetime
import pytest
from pydantic import ValidationError
from src.api.schemas import (
    WorkflowSubmission, 
    WorkflowResponse, 
    WorkflowStatus, 
    WorkflowStatusResponse,
    HealthResponse,
    AgentInfo
)

class TestWorkflowSchemas:
    
    def test_workflow_submission_valid(self):
        """Test valid workflow submission data."""
        data = {
            "workflow_id": "wf-123",
            "input": {"key": "val"},
            "config": {"debug": True}
        }
        model = WorkflowSubmission(**data)
        assert model.workflow_id == "wf-123"
        assert model.input["key"] == "val"
        assert model.config["debug"] is True

    def test_workflow_submission_missing_field(self):
        """Test validation error on missing required field."""
        with pytest.raises(ValidationError):
            WorkflowSubmission(input={}) # Missing workflow_id

    def test_workflow_submission_defaults(self):
        """Test default values."""
        model = WorkflowSubmission(workflow_id="wf-123")
        assert model.input == {}
        assert model.config is None

class TestResponseSchemas:
    
    def test_workflow_response(self):
        """Test response serialization."""
        data = {
            "execution_id": "exec-abc",
            "workflow_id": "wf-123",
            "status": "queued",
            "submitted_at": datetime.now(),
            "message": "Accepted"
        }
        model = WorkflowResponse(**data)
        assert model.execution_id == "exec-abc"
        assert model.status == "queued"

    def test_workflow_status_response_enum(self):
        """Test status enum validation."""
        # Valid status
        model = WorkflowStatusResponse(
            execution_id="1", 
            workflow_id="wf", 
            status=WorkflowStatus.RUNNING, 
            submitted_at=datetime.now()
        )
        assert model.status == "running"

        # Invalid status cast
        with pytest.raises(ValidationError):
            WorkflowStatusResponse(
                execution_id="1", 
                workflow_id="wf", 
                status="super_fast_mode", # Invalid
                submitted_at=datetime.now()
            )

class TestHealthSchema:
    def test_health_response(self):
        """Test health check formatting."""
        model = HealthResponse(
            timestamp=datetime.now(),
            services={"db": "healthy"}
        )
        assert model.status == "healthy" # default
        assert model.services["db"] == "healthy"

class TestAgentSchema:
    def test_agent_info(self):
        model = AgentInfo(
            agent_id="agent-1",
            name="Test Agent",
            description="Tests things",
            version="1.0.0",
            capabilities=["testing"]
        )
        assert model.agent_id == "agent-1"
