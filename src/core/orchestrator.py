# src/core/orchestrator.py
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class WorkflowState:
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.task_results: Dict[str, Any] = {}
        self.task_status: Dict[str, TaskStatus] = {}
        self.task_duration: Dict[str, float] = {}
        self.started_at = datetime.now()
    
    def get_task_output(self, task_id: str) -> Optional[Any]:
        return self.task_results.get(task_id)
    
    def set_task_result(self, task_id: str, result: Any, duration: float):
        self.task_results[task_id] = result
        self.task_duration[task_id] = duration
        self.task_status[task_id] = TaskStatus.SUCCESS
    
    def set_task_failed(self, task_id: str):
        self.task_status[task_id] = TaskStatus.FAILED
    
    def get_metrics(self) -> Dict[str, Any]:
        total_duration = (datetime.now() - self.started_at).total_seconds() * 1000
        return {
            "total_duration_ms": total_duration,
            "task_durations": self.task_duration,
            "task_statuses": {k: v.value for k, v in self.task_status.items()}
        }

class Orchestrator:
    def __init__(self, executors_map: Dict[str, Any]):
        """
        Initialize orchestrator with executor implementations
        
        Args:
            executors_map: {
                "llm": LLMExecutor(),
                "tool": ToolExecutor(),
                "script": ScriptExecutor(),
                ...
            }
        """
        self.executors = executors_map
    
    def execute(self, workflow, input_data: Dict[str, Any]) -> WorkflowState:
        """Execute workflow from start to finish"""
        
        logger.info(f"Starting workflow execution: {workflow.name}")
        state = WorkflowState(workflow.name)
        
        # Add initial input to state
        state.task_results["__input__"] = input_data
        
        # Get topologically sorted tasks
        tasks = workflow.topological_sort()
        
        for task in tasks:
            try:
                logger.info(f"Executing task: {task.id}")
                result = self._execute_task(task, state)
                state.set_task_result(task.id, result, 0)
            except Exception as e:
                logger.error(f"Task {task.id} failed: {str(e)}")
                state.set_task_failed(task.id)
                raise
        
        logger.info(f"Workflow completed: {workflow.name}")
        return state
    
    def _execute_task(self, task, state: WorkflowState) -> Any:
        """Execute individual task"""
        start_time = time.time()
        
        # Resolve input references (e.g., ${task_1.output})
        task_input = self._resolve_inputs(task.inputs, state)
        
        # Get executor for this task type
        executor = self.executors.get(task.type.value)
        if not executor:
            raise ValueError(f"No executor found for task type: {task.type}")
        
        # Execute task
        result = executor.execute(task.config, task_input)
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"Task {task.id} completed in {duration:.2f}ms")
        
        return result
    
    def _resolve_inputs(self, inputs: Dict[str, str], state: WorkflowState) -> Dict[str, Any]:
        """Resolve input references to actual values"""
        resolved = {}
        
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Parse reference: ${task_id.output}
                ref = value[2:-1]  # Remove ${ and }
                task_id, var = ref.split(".")
                resolved[key] = state.get_task_output(task_id)
            else:
                resolved[key] = value
        
        return resolved
