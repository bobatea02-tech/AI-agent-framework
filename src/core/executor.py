from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

# Configure logging if not already configured
logger = logging.getLogger(__name__)

class BaseExecutor(ABC):
    """
    Abstract base class for all executors.
    Provides standardized execution flow with monitoring, logging, and error handling.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the executor.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}

    @abstractmethod
    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
        """
        Execute the core logic. Must be implemented by subclasses.

        Args:
            config: Task-specific configuration.
            inputs: Dictionary of input parameters.

        Returns:
            The execution result.
        """
        pass

    def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Validate inputs before execution. can be overridden by subclasses.

        Args:
            inputs: Dictionary of input parameters.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not isinstance(inputs, dict):
            raise ValueError(f"Inputs must be a dictionary, got {type(inputs)}")

    def run_with_monitoring(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run execute() with monitoring, logging, and error handling.

        Args:
            config: Task-specific configuration.
            inputs: Dictionary of input parameters.

        Returns:
            Dictionary containing:
            - status: 'success' or 'failed'
            - output: Result of execute() if successful, else None
            - error: Error message if failed, else None
            - duration: Execution time in seconds
            - timestamp: ISO format timestamp of start
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        result = {
            "status": "failed",
            "output": None,
            "error": None,
            "duration": 0.0,
            "timestamp": timestamp
        }

        try:
            self.validate_inputs(inputs)
            logger.info(f"Starting execution with inputs keys: {list(inputs.keys())}")
            
            output = self.execute(config, inputs)
            
            result["status"] = "success"
            result["output"] = output
            logger.info("Execution completed successfully")
            
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}", exc_info=True)
            result["error"] = str(e)
            result["status"] = "failed"
            
        finally:
            duration = time.time() - start_time
            result["duration"] = duration
            logger.info(f"Execution finished in {duration:.4f}s")
            
        return result
