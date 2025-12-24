
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

try:
    print("Importing FormFillingAgent...")
    from src.agents.form_filling_agent import FormFillingAgent
    agent1 = FormFillingAgent()
    print("SUCCESS: FormFillingAgent instantiated.")
except Exception as e:
    print(f"FAILURE: FormFillingAgent failed: {e}")

try:
    print("\nImporting KnowledgeQAAgent...")
    from src.agents.knowledge_qa_agent import KnowledgeQAAgent
    agent2 = KnowledgeQAAgent()
    print("SUCCESS: KnowledgeQAAgent instantiated.")
except Exception as e:
    print(f"FAILURE: KnowledgeQAAgent failed: {e}")
