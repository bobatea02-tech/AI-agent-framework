from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.models import Base, WorkflowDefinition, WorkflowExecution, TaskExecution, AgentDefinition
import uuid
from datetime import datetime

def verify_models():
    print("Verifying models...")
    # Use in-memory SQLite for verification
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create WorkflowDefinition
        workflow = WorkflowDefinition(
            workflow_id="wf-001",
            name="Test Workflow",
            description="A test workflow",
            version="1.0.0",
            task_flow={"steps": ["task1", "task2"]},
            config={"timeout": 60},
            created_by="tester"
        )
        session.add(workflow)
        session.commit()
        print(f"Created WorkflowDefinition: {workflow.id}")

        # 2. Create WorkflowExecution
        execution = WorkflowExecution(
            execution_id="exec-001",
            workflow_id=workflow.id,
            workflow_version="1.0.0",
            status="running",
            priority=1,
            input_data={"param": "value"},
            submitted_by="tester"
        )
        session.add(execution)
        session.commit()
        print(f"Created WorkflowExecution: {execution.id}")

        # 3. Create TaskExecution
        task = TaskExecution(
            task_id="task-001",
            execution_id=execution.id,
            task_name="Test Task",
            executor="python-executor",
            status="pending",
            depends_on=["start"]
        )
        session.add(task)
        session.commit()
        print(f"Created TaskExecution: {task.id}")

        # 4. Create AgentDefinition
        agent = AgentDefinition(
            agent_id="agent-001",
            name="Test Agent",
            description="A test agent",
            version="1.0.0",
            agent_type="assistant",
            workflow_id=workflow.id,
            capabilities=["chat", "code"],
            config={"model": "gemini-pro"}
        )
        session.add(agent)
        session.commit()
        print(f"Created AgentDefinition: {agent.id}")

        # Verify relationships
        assert len(workflow.executions) == 1
        assert len(workflow.agents) == 1
        assert execution.workflow_definition == workflow
        assert len(execution.task_executions) == 1
        assert task.workflow_execution == execution
        assert agent.workflow_definition == workflow
        
        print("All verifications passed successfully!")

    except Exception as e:
        print(f"Verification failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    verify_models()
