
import pytest
import os
import sys
from typing import Generator
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.database.connection import get_db
from src.database.models import Base
from src.api.schemas import WorkflowSubmission

# --- Database Fixture ---

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create a persistent in-memory SQLite database for the test session.
    Using StaticPool to maintain the memory across multiple connections.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """
    Yield a database session for a single test function.
    Rolls back transaction after test to ensure isolation.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

# --- Client Fixture ---

@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden database dependency.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass # Session handled by fixture
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# --- Data Fixtures ---

@pytest.fixture(scope="function")
def sample_workflow_submission() -> WorkflowSubmission:
    """
    Sample valid workflow submission data.
    """
    return WorkflowSubmission(
        workflow_id="test-workflow-001",
        input={"doc_type": "aadhaar", "text": "Sample text"},
        config={"priority": "high"}
    )

# --- Mock Fixtures ---

@pytest.fixture(scope="function")
def mock_openai_response():
    """
    Mocks the OpenAI API response for checking structure vs logic.
    """
    mock_content = {
        "document_type": "aadhaar", 
        "confidence": 0.95, 
        "reasoning": "Detected keywords"
    }
    
    mock_choice = MagicMock()
    mock_choice.message.content = str(mock_content).replace("'", '"')
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    return mock_response
