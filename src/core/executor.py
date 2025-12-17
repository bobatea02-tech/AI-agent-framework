from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Executor(ABC):
    """Base executor interface used by orchestrators and task runners."""

    @abstractmethod
    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
        """Run a single task step and return its output."""
        raise NotImplementedError


