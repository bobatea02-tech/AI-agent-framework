
import pytest
from src.database.models import WorkflowDefinition, WorkflowExecution

class TestAPIDatabaseIntegration:
    
    def test_create_workflow_persistence(self, client, test_db, sample_workflow_submission):
        """Test that submitting a workflow persists it to the DB."""
        # 1. Create a definition first (required FK)
        wf_def = WorkflowDefinition(
            workflow_id=sample_workflow_submission.workflow_id,
            name="Test Integration WF", 
            task_flow={"steps": []}
        )
        test_db.add(wf_def)
        test_db.commit()
        
        # 2. Submit via API
        response = client.post("/api/v1/workflows", json=sample_workflow_submission.model_dump())
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        execution_id = data["execution_id"]
        
        # 3. Verify DB persistence
        # We need to query the DB directly to ensure logic didn't just mock it
        # The test_db fixture is the same session used by client override
        saved = test_db.query(WorkflowExecution).filter_by(execution_id=execution_id).first()
        assert saved is not None
        assert saved.workflow_id == wf_def.id
        assert saved.input_data["doc_type"] == "aadhaar"

    def test_get_workflow_status_integration(self, client, test_db):
        """Test retrieving status from DB via API."""
        # Setup
        wf_def = WorkflowDefinition(workflow_id="status-test", name="Status Test", task_flow={})
        test_db.add(wf_def)
        test_db.commit()
        
        exec_run = WorkflowExecution(
            execution_id="exec-status-1",
            workflow_id=wf_def.id,
            status="running",
            input_data={}
        )
        test_db.add(exec_run)
        test_db.commit()
        
        # Act
        response = client.get(f"/api/v1/workflows/exec-status-1")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "running"
        assert data["workflow_id"] == "status-test"

    def test_list_workflows_integration(self, client, test_db):
        """Test list endpoint pagination and filtering."""
        wf_def = WorkflowDefinition(workflow_id="list-wf", name="List Test", task_flow={})
        test_db.add(wf_def)
        test_db.commit()
        
        # Create 15 executions
        for i in range(15):
            test_db.add(WorkflowExecution(
                execution_id=f"exec-{i}",
                workflow_id=wf_def.id,
                status="completed" if i < 10 else "failed"
            ))
        test_db.commit()
        
        # Test Default
        res = client.get("/api/v1/workflows")
        assert len(res.json()) == 10
        
        # Test Filter
        res_failed = client.get("/api/v1/workflows?status=failed")
        assert len(res_failed.json()) == 5
