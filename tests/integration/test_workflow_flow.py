
import sys
import os
import uuid
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

# --- CRITICAL: MOCK BEFORE ANY SRC IMPORTS (Redundant but safe) ---
mock_modules = [
    'kafka', 'kafka.producer', 'kafka.admin', 'redis', 
    'structlog', 'structlog.contextvars', 'structlog.processors', 'structlog.dev',
    'pdf2image', 'pytesseract', 'PIL', 'PIL.Image', 'openai'
]
for m in mock_modules:
    if m not in sys.modules:
        sys.modules[m] = MagicMock()

# Setup functional mock for structlog
mock_structlog = sys.modules['structlog']
if not isinstance(mock_structlog.get_logger, MagicMock):
    mock_logger = MagicMock()
    mock_structlog.get_logger.return_value = mock_logger
    mock_structlog.make_filtering_bound_logger.return_value = mock_logger
    mock_structlog.processors.JSONRenderer = MagicMock()
    mock_structlog.processors.TimeStamper = MagicMock()
    mock_structlog.dev.ConsoleRenderer = MagicMock()
    mock_structlog.processors.StackInfoRenderer = MagicMock()
    mock_structlog.processors.add_log_level = MagicMock()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# --- Fixtures ---

@pytest.fixture(scope="session")
def app():
    from src.api.main import app as _app
    return _app

@pytest.fixture(scope="function")
def test_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from src.database.models import Base
    
    # Use in-memory SQLite
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
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
    
    # We need to access the db created in test_db fixture, 
    # but fixtures are independent. 
    # Best way is to use dependency override that yields a FRESH session from the SAME engine 
    # or just mocks the get_db.
    # But since we use in-memory DB, we need to share the engine.
    
    # Simpler approach: Create engine effectively global for this module
    # But for now, let's just re-create the session factory inside dependency
    # Note: sharing data between test_db fixture and app dependency is tricky with in-memory DB
    # because they need same engine instance.
    
    pass
    # REVISIT: The previous approach defined engine globally. Let's do that.

# Global test engine to share state between test setup and API calls
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
GLOBAL_TEST_ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
GLOBAL_TEST_SESSION = sessionmaker(autocommit=False, autoflush=False, bind=GLOBAL_TEST_ENGINE)

@pytest.fixture(scope="function")
def shared_test_db():
    from src.database.models import Base
    Base.metadata.create_all(bind=GLOBAL_TEST_ENGINE)
    db = GLOBAL_TEST_SESSION()
    try:
        yield db
    finally:
        db.close()
        # Drop all not strictly necessary if we use StaticPool but good practice
        Base.metadata.drop_all(bind=GLOBAL_TEST_ENGINE)

@pytest.fixture(scope="function")
def client(app, shared_test_db):
    from fastapi.testclient import TestClient
    from src.database.connection import get_db
    
    def override_get_db():
        db = GLOBAL_TEST_SESSION()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest_asyncio.fixture(scope="function")
async def async_client(app, shared_test_db):
    from httpx import AsyncClient, ASGITransport
    from src.database.connection import get_db
    
    def override_get_db():
        db = GLOBAL_TEST_SESSION()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_workflow_submission():
    from src.api.schemas import WorkflowSubmission
    return WorkflowSubmission(
        workflow_id="test-workflow-001",
        input={"doc_path": "test.pdf"},
        config={}
    )

@pytest.fixture
def seed_workflow(shared_test_db):
    from src.database.models import WorkflowDefinition
    wf = WorkflowDefinition(
        id=uuid.uuid4(),
        workflow_id="test-workflow-001",
        name="Test Workflow",
        version="1.0",
        task_flow=[{"id": "task1", "type": "llm"}],
        config={}
    )
    shared_test_db.add(wf)
    shared_test_db.commit()
    return wf

@pytest.fixture(autouse=True)
def mock_external_services():
    mock_producer = MagicMock()
    mock_state_manager = MagicMock()
    mock_state_manager.redis.ping.return_value = True

    with patch("src.api.routes.kafka_producer", mock_producer):
        with patch("src.api.routes.orchestrator_instance._state_manager", mock_state_manager):
            yield (mock_producer, mock_state_manager)

# --- Tests ---

def test_submit_workflow_api(client, seed_workflow, sample_workflow_submission):
    # Sync test
    payload = sample_workflow_submission.model_dump()
    response = client.post("/api/v1/workflows", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_submit_workflow_async(async_client, seed_workflow, sample_workflow_submission):
    # Async test
    payload = sample_workflow_submission.model_dump()
    response = await async_client.post("/api/v1/workflows", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "queued"

@pytest.mark.asyncio
async def test_get_workflow_status(async_client, seed_workflow, sample_workflow_submission):
    # 1. Submit
    payload = sample_workflow_submission.model_dump()
    response = await async_client.post("/api/v1/workflows", json=payload)
    assert response.status_code == 202
    execution_id = response.json()["execution_id"]
    
    # 2. Get status
    status_res = await async_client.get(f"/api/v1/workflows/{execution_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "queued"