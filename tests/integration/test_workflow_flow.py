
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from src.api.main import app
from src.database.models import WorkflowDefinition
from src.database.connection import get_db

# --- Fixtures ---

@pytest.fixture
def seed_workflow(test_db: Session):
    """
    Seeds a workflow definition into the database.
    Required for submission tests to pass validation.
    """
    wf = WorkflowDefinition(
        workflow_id="test-workflow-001",
        name="Test Workflow",
        version="1.0",
        task_flow=[{"id": "task1", "type": "llm"}],
        config={}
    )
    test_db.add(wf)
    test_db.commit()
    return wf

@pytest.fixture
async def async_client(test_db):
    """
    Async client for testing async endpoints.
    Overrides get_db to use the test session.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass 

    app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport to communicate with the FastAPI app directly
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

# --- Tests ---

@pytest.mark.asyncio
async def test_submit_workflow_api(async_client, seed_workflow, sample_workflow_submission):
    """
    Test submitting a workflow via POST /api/v1/workflows.
    """
    # Ensure workflow_id matches the seeded one
    submission_data = sample_workflow_submission.model_dump()
    submission_data['workflow_id'] = seed_workflow.workflow_id
    
    response = await async_client.post("/api/v1/workflows", json=submission_data)
    
    assert response.status_code == 202
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "queued"
    assert data["workflow_id"] == seed_workflow.workflow_id

def test_get_workflow_status(client, seed_workflow, sample_workflow_submission):
    """
    Test retrieving workflow status via GET /api/v1/workflows/{execution_id}.
    Using sync TestClient as requested for this part.
    """
    # 1. Submit a workflow to get an ID (using sync client for setup convenience)
    submission_data = sample_workflow_submission.model_dump()
    submission_data['workflow_id'] = seed_workflow.workflow_id
    
    submit_response = client.post("/api/v1/workflows", json=submission_data)
    assert submit_response.status_code == 202
    execution_id = submit_response.json()["execution_id"]
    
    # 2. Query status
    status_response = client.get(f"/api/v1/workflows/{execution_id}")
    
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["execution_id"] == execution_id
    assert "status" in status_data
    assert status_data["workflow_id"] == seed_workflow.workflow_id
