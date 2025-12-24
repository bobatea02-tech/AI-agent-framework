import sys
import os
import uuid
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Test Database Setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def app():
    from src.api.main import app as _app
    return _app

@pytest.fixture(scope="function")
def test_db():
    from src.database.models import Base
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def sync_client(app):
    from fastapi.testclient import TestClient
    from src.database.connection import get_db
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest_asyncio.fixture(scope="function")
async def async_client(app):
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(autouse=True)
def mock_external_services():
    mock_producer = MagicMock()
    mock_state_manager = MagicMock()
    mock_state_manager.redis.ping.return_value = True

    # Use patch with string targets to avoid early imports
    with patch("src.api.routes.kafka_producer", mock_producer):
        with patch("src.api.routes.orchestrator_instance._state_manager", mock_state_manager):
            yield (mock_producer, mock_state_manager)

def test_submit_workflow_api(test_db, sync_client):
    from src.database.models import WorkflowDefinition
    wf_id = "test-workflow"
    wf_def = WorkflowDefinition(
        id=uuid.uuid4(),
        workflow_id=wf_id,
        name="Test Workflow",
        task_flow=[{"task_id": "task1", "type": "OCR"}],
        version="1.0"
    )
    test_db.add(wf_def)
    test_db.commit()

    response = sync_client.post("/api/v1/workflows", json={
        "workflow_id": wf_id,
        "input": {"doc_path": "test.pdf"}
    })
    
    assert response.status_code == 202
    assert "execution_id" in response.json()

@pytest.mark.asyncio
async def test_get_workflow_status(test_db, async_client):
    from src.database.models import WorkflowDefinition, WorkflowExecution
    wf_def_id = uuid.uuid4()
    wf_id = "status-workflow"
    wf_def = WorkflowDefinition(
        id=wf_def_id,
        workflow_id=wf_id,
        name="Status Workflow",
        task_flow=[{"task_id": "task1", "type": "OCR"}],
        version="1.0"
    )
    test_db.add(wf_def)
    test_db.commit()

    exec_id = str(uuid.uuid4())
    execution = WorkflowExecution(
        execution_id=exec_id,
        workflow_id=wf_def_id,
        status="pending", # Changed to pending as it's more standard for a new execution
        submitted_at=datetime.utcnow()
    )
    test_db.add(execution)
    test_db.commit()

    response = await async_client.get(f"/api/v1/workflows/{exec_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
