from __future__ import annotations

from typing import Any, Dict, Optional

import json
import redis


class StateManager:
    """State persistence layer backed by Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl_seconds: int = 86400):
        """
        Initialize StateManager.
        
        Args:
            redis_url: Connection URL for Redis.
            ttl_seconds: Time-to-live for state keys in seconds (default 24h).
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def save_workflow_state(self, execution_id: str, state: Dict[str, Any]) -> None:
        """
        Save the overall state of a workflow execution.
        
        Args:
            execution_id: Unique identifier for the workflow execution.
            state: Dictionary containing the workflow state.
        """
        self.client.setex(
            self._workflow_key(execution_id),
            self.ttl_seconds,
            json.dumps(state)
        )

    def get_workflow_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the state of a workflow execution.
        
        Args:
            execution_id: Unique identifier for the workflow execution.
            
        Returns:
            Dictionary containing the workflow state, or None if not found.
        """
        raw = self.client.get(self._workflow_key(execution_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def save_task_output(self, execution_id: str, task_id: str, output: Any) -> None:
        """
        Save the output of a specific task within a workflow execution.
        
        Args:
            execution_id: Unique identifier for the workflow execution.
            task_id: Unique identifier for the task.
            output: The output data to save (must be JSON-serializable).
        """
        self.client.setex(
            self._task_key(execution_id, task_id),
            self.ttl_seconds,
            json.dumps(output)
        )

    def get_task_output(self, execution_id: str, task_id: str) -> Optional[Any]:
        """
        Retrieve the output of a specific task.
        
        Args:
            execution_id: Unique identifier for the workflow execution.
            task_id: Unique identifier for the task.
            
        Returns:
            The task output data, or None if not found.
        """
        raw = self.client.get(self._task_key(execution_id, task_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def delete_state(self, execution_id: str) -> None:
        """
        Delete all state associated with a workflow execution (workflow state and task outputs).
        Note: This simplistic implementation only deletes the main workflow key.
              To delete task keys, we'd need to track them or use scan/keys (expensive).
              For now, we rely on TTL expiry for cleanup or explicit deletion if keys are known.
        """
        self.client.delete(self._workflow_key(execution_id))

    def _workflow_key(self, execution_id: str) -> str:
        return f"workflow:{execution_id}:state"

    def _task_key(self, execution_id: str, task_id: str) -> str:
        return f"workflow:{execution_id}:task:{task_id}:output"


