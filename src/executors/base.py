# src/executors/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
        """
        Execute task
        
        Args:
            config: Task configuration (model name, prompt template, etc)
            inputs: Input data
        
        Returns:
            Task result
        """
        pass
