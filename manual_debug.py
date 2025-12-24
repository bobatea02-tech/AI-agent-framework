
from unittest.mock import MagicMock
import sys
import asyncio
import traceback
import os

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mock dependencies matching conftest.py
mock_modules = [
    'kafka', 'kafka.producer', 'kafka.admin',
    'redis',
    # 'structlog', 'structlog.contextvars', 'structlog.processors', 'structlog.dev', # Use real structlog checks
    'pdf2image',
    'pytesseract',
    'PIL', 'PIL.Image',
    'openai'
]
for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()

# Explicit mocks for things that might be accessed
# sys.modules['structlog'].get_logger.return_value = MagicMock()

try:
    print("Starting manual debug...")
    # Manual setup matching conftest
    from src.database.connection import get_db
    from src.database.models import Base
    from src.api.main import app
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    
    print("Imports successful")
    
    # Setup DB
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Seed
    from src.database.models import WorkflowDefinition
    wf = WorkflowDefinition(workflow_id="test-workflow-001", name="Test", version="1.0", task_flow=[], config={})
    db.add(wf)
    db.commit()
    print("Seeding successful")
    
    # Test Logic - Submit
    from httpx import AsyncClient, ASGITransport
    
    async def run_test():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Override dependency
            app.dependency_overrides[get_db] = lambda: db
            
            resp = await ac.post("/api/v1/workflows", json={
                "workflow_id": "test-workflow-001",
                "input": {"a": 1}
            })
            print(f"Response status: {resp.status_code}")
            print(f"Response body: {resp.text}")
            if resp.status_code != 202:
                print("FAILURE: Submission Status code mismatch")
            else:
                data = resp.json()
                execution_id = data['execution_id']
                print(f"Submission passed. Execution ID: {execution_id}")

                # Test Status
                resp_status = await ac.get(f"/api/v1/workflows/{execution_id}")
                print(f"Status check code: {resp_status.status_code}")
                # print(f"Status check body: {resp_status.text}")
                
                if resp_status.status_code != 200:
                    print("FAILURE: Status check code mismatch")
                else:
                    status_data = resp_status.json()
                    print(f"Status returned: {status_data.get('status')}")
                    if status_data.get('execution_id') != execution_id:
                        print("FAILURE: Execution ID mismatch")
                    else:
                        print("Status check passed!")
                        
                # 3. Check Metrics
                resp_metrics = await ac.get("/metrics", follow_redirects=True)
                if resp_metrics.status_code != 200:
                     print("FAILURE: Metrics endpoint returned", resp_metrics.status_code)
                else:
                    metrics_text = resp_metrics.text
                    print("Metrics endpoint check passed")
                    if 'workflows_submitted_total' in metrics_text and 'test-workflow-001' in metrics_text:
                        print("SUCCESS: workflows_submitted_total metric found.")
                    else:
                        print("FAILURE: Metric workflow_submitted_total not found or incorrect.")



    asyncio.run(run_test())

except Exception:
    with open("debug_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Test exploded, error written to debug_error.txt")
