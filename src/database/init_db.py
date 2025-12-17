import logging
import sys
import os
from sqlalchemy import select

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.connection import engine, get_db_context
from database.models import Base, WorkflowDefinition, AgentDefinition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
    
    load_sample_workflows()

def load_sample_workflows():
    """Load sample workflows and agents if they don't exist"""
    logger.info("Checking for sample workflows...")
    
    with get_db_context() as session:
        # Check and create Form Filling Workflow
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.workflow_id == "form_filling_v1")
        existing_wf1 = session.execute(stmt).scalar_one_or_none()
        
        wf1 = existing_wf1
        if not existing_wf1:
            logger.info("Creating 'form_filling_v1' workflow...")
            wf1 = WorkflowDefinition(
                workflow_id="form_filling_v1",
                name="Form Filling Workflow",
                description="Automated form filling workflow",
                version="1.0.0",
                task_flow={"steps": ["extract", "verify", "fill"]},
                config={"timeout": 300},
                created_by="system"
            )
            session.add(wf1)
            session.flush() # Flush to get ID for agent
        else:
            logger.info("'form_filling_v1' workflow already exists.")

        # Check and create Agent for Form Filling
        stmt = select(AgentDefinition).where(AgentDefinition.agent_id == "form_filling_agent")
        existing_agent1 = session.execute(stmt).scalar_one_or_none()
        
        if not existing_agent1:
            logger.info("Creating 'form_filling_agent'...")
            agent1 = AgentDefinition(
                agent_id="form_filling_agent",
                name="Form Filler Agent",
                description="Agent specialized in filling forms",
                version="1.0.0",
                agent_type="form_filler",
                workflow_id=wf1.id,
                capabilities=["pdf_reading", "text_extraction", "form_filling"],
                config={"model": "gpt-4"}
            )
            session.add(agent1)
        else:
            logger.info("'form_filling_agent' already exists.")

        # Check and create Knowledge QA Workflow
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.workflow_id == "knowledge_qa_v1")
        existing_wf2 = session.execute(stmt).scalar_one_or_none()
        
        wf2 = existing_wf2
        if not existing_wf2:
            logger.info("Creating 'knowledge_qa_v1' workflow...")
            wf2 = WorkflowDefinition(
                workflow_id="knowledge_qa_v1",
                name="Knowledge QA Workflow",
                description="Question answering from knowledge base",
                version="1.0.0",
                task_flow={"steps": ["retrieve", "answer"]},
                config={"timeout": 120},
                created_by="system"
            )
            session.add(wf2)
            session.flush()
        else:
            logger.info("'knowledge_qa_v1' workflow already exists.")

        # Check and create Agent for Knowledge QA
        stmt = select(AgentDefinition).where(AgentDefinition.agent_id == "knowledge_qa_agent")
        existing_agent2 = session.execute(stmt).scalar_one_or_none()
        
        if not existing_agent2:
            logger.info("Creating 'knowledge_qa_agent'...")
            agent2 = AgentDefinition(
                agent_id="knowledge_qa_agent",
                name="QA Assistant Agent",
                description="Agent for answering questions",
                version="1.0.0",
                agent_type="qa_assistant",
                workflow_id=wf2.id,
                capabilities=["search", "qa", "summarization"],
                config={"model": "gpt-3.5-turbo"}
            )
            session.add(agent2)
        else:
            logger.info("'knowledge_qa_agent' already exists.")

if __name__ == "__main__":
    init_database()
