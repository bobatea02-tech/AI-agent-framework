from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional
from src.core.executor import BaseExecutor

logger = logging.getLogger(__name__)

class ValidationExecutor(BaseExecutor):
    """
    Executor for validating data against defined rules.
    Supports regex pattern matching for standardized fields.
    """

    DEFAULT_RULES = {
        "aadhaar_number": r"^\d{12}$",
        "pan_number": r"^[A-Z]{5}\d{4}[A-Z]$",
        "dob": r"^\d{2}/\d{2}/\d{4}$",
        "name": r"^[A-Za-z\s]+$"
    }

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data against rules.

        Args:
            inputs: Dictionary containing:
                - data: Dict[str, Any] - Data fields to validate.
                - rules: Optional[Dict[str, str]] - Custom regex rules to override defaults.

        Returns:
            Dictionary containing:
                - is_valid: bool
                - errors: List[str]
                - warnings: List[str]
                - fields_validated: int
                - status: str ('success', 'failure')
        """
        data = inputs.get("data")
        if not isinstance(data, dict):
             raise ValueError(f"Expected 'data' to be a dict, got {type(data)}")

        user_rules = inputs.get("rules") or {}
        # Merge default rules with user rules (user rules take precedence)
        rules = {**self.DEFAULT_RULES, **user_rules}

        errors = []
        warnings = []
        fields_validated = 0

        logger.info(f"Validating {len(data)} fields against rules.")

        for field, value in data.items():
            # Check for empty values
            if value is None or (isinstance(value, str) and not value.strip()):
                warnings.append(f"Field '{field}' is empty or None")
                continue

            # Only validate if we have a rule for the field
            if field in rules:
                pattern = rules[field]
                fields_validated += 1
                
                if not isinstance(value, str):
                    value_str = str(value)
                else:
                    value_str = value
                
                if not re.match(pattern, value_str):
                    errors.append(
                        f"Validation failed for '{field}': Value '{value}' does not match pattern '{pattern}'"
                    )
            # Else: No specific rule for this field, considered valid by default (or ignored)

        is_valid = len(errors) == 0
        status = "success" if is_valid else "failure" # This is distinct from executor status 'success'/'failed' which indicates run success. 
        # But BaseExecutor checks for exceptions. Here we complete successfully but `status` in payload reflects validation result? 
        # Actually logic is: executor result tells if *execution* worked. Result payload tells if *validation* passed.
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "fields_validated": fields_validated,
            "status": status 
        }
