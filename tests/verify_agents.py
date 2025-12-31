#!/usr/bin/env python3
"""
Verification script to test both reference agents.
Tests Form Filling Agent and Knowledge Q&A Agent workflows.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import Orchestrator
from src.core.task_flow import TaskFlow, load_task_flow
from src.executors.ocr_executor import OcrExecutor
from src.executors.validation_executor import ValidationExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.rag_executor import RAGRetrieverExecutor


def test_form_filling_agent():
    """Test the Form Filling Agent workflow."""
    print("\n" + "="*60)
    print("Testing Form Filling Agent")
    print("="*60)
    
    # Create executors
    executors = {
        "OCRExecutor": OcrExecutor(),
        "ValidationExecutor": ValidationExecutor(),
    }
    
    # Create orchestrator
    orchestrator = Orchestrator(executors=executors)
    
    # Load workflow definition
    workflow_path = Path(__file__).parent.parent / "workflows" / "form_filling_flow.json"
    
    try:
        flow = load_task_flow(str(workflow_path))
        print(f"✓ Loaded workflow: {flow.workflow_id}")
        print(f"  Tasks: {[t.id for t in flow.tasks]}")
        
        # Test with sample input
        test_input = {
            "document": "sample_aadhaar.pdf"  # Mock document path
        }
        
        print(f"\n→ Executing workflow with input: {test_input}")
        result = orchestrator.execute(flow, test_input)
        
        print(f"\n✓ Workflow completed!")
        print(f"  Status: {len([s for s in result.metrics['task_statuses'].values() if s == 'succeeded'])} tasks succeeded")
        print(f"  Duration: {result.metrics['total_duration_ms']:.2f}ms")
        
        if result.errors:
            print(f"\n⚠ Errors encountered:")
            for task_id, error in result.errors.items():
                print(f"    {task_id}: {error}")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ Workflow file not found: {workflow_path}")
        return False
    except Exception as e:
        print(f"✗ Error executing workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_qa_agent():
    """Test the Knowledge Q&A Agent workflow."""
    print("\n" + "="*60)
    print("Testing Knowledge Q&A Agent")
    print("="*60)
    
    # Create executors
    executors = {
        "RAGRetrieverExecutor": RAGRetrieverExecutor(),
        "LLMExecutor": LLMExecutor(),
    }
    
    # Create orchestrator
    orchestrator = Orchestrator(executors=executors)
    
    # Load workflow definition
    workflow_path = Path(__file__).parent.parent / "workflows" / "knowledge_qa_flow.json"
    
    try:
        flow = load_task_flow(str(workflow_path))
        print(f"✓ Loaded workflow: {flow.workflow_id}")
        print(f"  Tasks: {[t.id for t in flow.tasks]}")
        
        # Test with sample query
        test_input = {
            "query": "What is the capital of France?"
        }
        
        print(f"\n→ Executing workflow with input: {test_input}")
        result = orchestrator.execute(flow, test_input)
        
        print(f"\n✓ Workflow completed!")
        print(f"  Status: {len([s for s in result.metrics['task_statuses'].values() if s == 'succeeded'])} tasks succeeded")
        print(f"  Duration: {result.metrics['total_duration_ms']:.2f}ms")
        
        if result.errors:
            print(f"\n⚠ Errors encountered:")
            for task_id, error in result.errors.items():
                print(f"    {task_id}: {error}")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ Workflow file not found: {workflow_path}")
        return False
    except Exception as e:
        print(f"✗ Error executing workflow: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_agent_definitions():
    """Check if agents are registered in the database."""
    print("\n" + "="*60)
    print("Checking Agent Definitions in Database")
    print("="*60)
    
    try:
        from src.database.connection import get_db
        from src.database.models import AgentDefinition
        from sqlalchemy import select
        
        db = next(get_db())
        
        agents = db.execute(select(AgentDefinition)).scalars().all()
        
        if agents:
            print(f"✓ Found {len(agents)} registered agents:")
            for agent in agents:
                print(f"  - {agent.agent_id}: {agent.name}")
                print(f"    Description: {agent.description}")
                print(f"    Workflow: {agent.workflow_id}")
                print()
            return True
        else:
            print("⚠ No agents found in database")
            print("  Run: python -m src.database.init_db")
            return False
            
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        print("  Make sure database is initialized")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*70)
    print(" AI AGENT FRAMEWORK - AGENT VERIFICATION")
    print("="*70)
    
    results = []
    
    # Check database registrations
    results.append(("Agent Definitions", check_agent_definitions()))
    
    # Test Form Filling Agent
    results.append(("Form Filling Agent", test_form_filling_agent()))
    
    # Test Knowledge Q&A Agent
    results.append(("Knowledge Q&A Agent", test_knowledge_qa_agent()))
    
    # Summary
    print("\n" + "="*70)
    print(" VERIFICATION SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
