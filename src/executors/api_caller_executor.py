from __future__ import annotations

from typing import Any, Dict

import requests

from .base import BaseExecutor


class APICallerExecutor(BaseExecutor):
    """Simple HTTP executor for calling external services."""

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        method = config.get("method", "GET").upper()
        url = config["url"]
        headers = config.get("headers", {})
        params = config.get("params", {})
        json_body = config.get("json", {})

        response = requests.request(method, url, headers=headers, params=params, json=json_body, timeout=15)
        response.raise_for_status()
        return {"status_code": response.status_code, "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text}


