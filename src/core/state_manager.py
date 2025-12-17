from __future__ import annotations

from typing import Any, Dict, Optional

import json
import redis


class StateManager:
    """Simple state persistence layer backed by Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def save_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        """Persist state as JSON so it round-trips with load_state."""
        payload = json.dumps(state)
        self.client.setex(self._key(workflow_id), self.ttl_seconds, payload)

    def load_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        raw = self.client.get(self._key(workflow_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            # Fallback retains raw string for debugging
            return {"raw": raw}

    def delete_state(self, workflow_id: str) -> None:
        self.client.delete(self._key(workflow_id))

    def _key(self, workflow_id: str) -> str:
        return f"workflow:{workflow_id}"


