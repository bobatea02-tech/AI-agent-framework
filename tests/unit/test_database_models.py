
import pytest
from sqlalchemy.exc import IntegrityError
from src.database.models import WorkflowDefinition, WorkflowExecution, TaskExecution, AgentDefinition

class TestWorkflowModels:
    
    def test_create_workflow_definition(self, test_db):
        """Test creating a workflow definition."""
        wf = WorkflowDefinition(
            workflow_id="test-wf-001",
            name="Test Workflow",
            task_flow={"steps": []}
        )
        test_db.add(wf)
        test_db.commit()
        
        saved = test_db.query(WorkflowDefinition).filter_by(workflow_id="test-wf-001").first()
        assert saved is not None
        assert saved.name == "Test Workflow"

    def test_workflow_definition_unique_id(self, test_db):
        """Test unique constraint on workflow_id."""
        wf1 = WorkflowDefinition(workflow_id="duplicate", name="First", task_flow={})
        test_db.add(wf1)
        test_db.commit()
        
        wf2 = WorkflowDefinition(workflow_id="duplicate", name="Second", task_flow={})
        test_db.add(wf2)
        with pytest.raises(IntegrityError):
            test_db.commit()

    def test_workflow_execution_relationship(self, test_db):
        """Test relationship between definition and execution."""
        wf = WorkflowDefinition(workflow_id="parent-wf", name="Parent", task_flow={})
        test_db.add(wf)
        test_db.commit()
        
        execution = WorkflowExecution(
            execution_id="exec-001",
            workflow_id=wf.id,
            status="pending"
        )
        test_db.add(execution)
        test_db.commit()
        
        # Test backref
        loaded_wf = test_db.query(WorkflowDefinition).first()
        assert len(loaded_wf.executions) == 1
        assert loaded_wf.executions[0].execution_id == "exec-001"

class TestTaskModels:
    
    def test_task_execution_create(self, test_db):
        """Test creating a task execution."""
        # Setup parent
        wf = WorkflowDefinition(workflow_id="wf", name="wf", task_flow={})
        test_db.add(wf)
        test_db.commit()
        
        exec_run = WorkflowExecution(execution_id="run", workflow_id=wf.id)
        test_db.add(exec_run)
        test_db.commit()
        
        # Test Task
        task = TaskExecution(
            task_id="step_1",
            execution_id=exec_run.id,
            task_name="Step One",
            status="completed"
        )
        test_db.add(task)
        test_db.commit()
        
        assert task.id is not None
        assert task.workflow_execution.execution_id == "run"
