# src/api/routes.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import json

from src.core.workflow import Workflow, Task, TaskType
from src.core.orchestrator import Orchestrator
from src.executors.llm_executor import LLMExecutor
from src.executors.tool_executor import ToolExecutor
from src.executors.script_executor import ScriptExecutor

app = FastAPI(title="AI Agent Framework", version="0.1.0")

# Initialize orchestrator with executors
executors = {
    "llm": LLMExecutor(),
    "tool": ToolExecutor(),
    "script": ScriptExecutor(),
}
orchestrator = Orchestrator(executors)

# Request/Response models
class TaskDef(BaseModel):
    id: str
    type: str
    config: Dict[str, Any]
    inputs: Dict[str, str] = {}

class WorkflowRequest(BaseModel):
    name: str
    description: str
    tasks: List[TaskDef]
    edges: List[tuple]

class ExecuteRequest(BaseModel):
    workflow: WorkflowRequest
    input_data: Dict[str, Any]

@app.post("/workflows/execute")
async def execute_workflow(request: ExecuteRequest):
    """Execute a workflow"""
    try:
        # Build workflow object
        workflow = Workflow(
            name=request.workflow.name,
            description=request.workflow.description
        )
        
        for task_def in request.workflow.tasks:
            task = Task(
                id=task_def.id,
                type=TaskType(task_def.type),
                config=task_def.config,
                inputs=task_def.inputs
            )
            workflow.add_task(task)
        
        for src, dst in request.workflow.edges:
            workflow.connect(src, dst)
        
        # Execute
        state = orchestrator.execute(workflow, request.input_data)
        
        return {
            "status": "success",
            "output": state.task_results,
            "metrics": state.get_metrics()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
