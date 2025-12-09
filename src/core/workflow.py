# src/core/workflow.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class TaskType(str, Enum):
    LLM = "llm"
    TOOL = "tool"
    SCRIPT = "script"
    CONDITIONAL = "conditional"

@dataclass
class Task:
    id: str
    type: TaskType
    config: Dict[str, Any]
    inputs: Dict[str, str] = field(default_factory=dict)  # task_id:output_var
    retries: int = 3
    timeout_seconds: int = 300

@dataclass
class Workflow:
    name: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    edges: List[tuple] = field(default_factory=list)  # (task_id1, task_id2)
    
    def add_task(self, task: Task):
        self.tasks.append(task)
    
    def connect(self, task1_id: str, task2_id: str):
        """Add dependency: task1 → task2"""
        self.edges.append((task1_id, task2_id))
    
    def get_dependencies(self, task_id: str) -> List[str]:
        """Get tasks that must run before this task"""
        return [src for src, dst in self.edges if dst == task_id]
    
    def get_dependents(self, task_id: str) -> List[str]:
        """Get tasks that depend on this task"""
        return [dst for src, dst in self.edges if src == task_id]
    
    def topological_sort(self) -> List[Task]:
        """Return tasks in execution order"""
        from functools import reduce
        
        # Build adjacency list
        task_map = {t.id: t for t in self.tasks}
        in_degree = {t.id: len(self.get_dependencies(t.id)) for t in self.tasks}
        
        # Kahn's algorithm
        queue = [t for t in self.tasks if in_degree[t.id] == 0]
        result = []
        
        while queue:
            task = queue.pop(0)
            result.append(task)
            
            for dependent in self.get_dependents(task.id):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(task_map[dependent])
        
        if len(result) != len(self.tasks):
            raise ValueError("Workflow contains cycles!")
        
        return result
