from __future__ import annotations

from typing import Any, Dict

from .base import BaseExecutor


class ValidationExecutor(BaseExecutor):
    """Performs schema/field validation on extracted data."""

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = config.get("required_fields", [])
        errors = {}
        for field in required_fields:
            # Consider a field missing only if the key is absent, not just falsy.
            if field not in inputs:
                errors[field] = "missing"
        return {"valid": not errors, "errors": errors, "data": inputs}


