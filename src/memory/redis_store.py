# src/memory/redis_store.py
import redis
import json
from typing import Any, Optional, Dict

class RedisStore:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        # Use decode_responses so Redis returns str instead of bytes which
        # makes json.loads() and string handling simpler.
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    
    def save_workflow_state(self, workflow_id: str, state: Dict[str, Any]):
        """Save workflow state to Redis"""
        key = f"workflow:{workflow_id}"
        # Use default=str to allow saving non-serializable objects in a readable form
        value = json.dumps(state, default=str)
        self.client.set(key, value)
        self.client.expire(key, 86400)  # 24 hour TTL
    
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow state"""
        key = f"workflow:{workflow_id}"
        value = self.client.get(key)
        if value:
            try:
                return json.loads(str(value))
            except Exception:
                # If stored value isn't valid JSON, return raw string
                return {"raw": value}
        return None
    
    def save_task_result(self, workflow_id: str, task_id: str, result: Any):
        """Save individual task result"""
        key = f"workflow:{workflow_id}:task:{task_id}"
        value = json.dumps(result, default=str)
        self.client.set(key, value)
        self.client.expire(key, 86400)
    
    def get_task_result(self, workflow_id: str, task_id: str) -> Optional[Any]:
        """Retrieve task result"""
        key = f"workflow:{workflow_id}:task:{task_id}"
        value = self.client.get(key)
        if value:
            try:
                # Ensure we pass a str/bytes/bytearray to json.loads to satisfy the type checker.
                return json.loads(str(value))
            except Exception:
                return value
        return None
