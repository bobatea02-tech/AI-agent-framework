from __future__ import annotations

from typing import Any, Dict

from src.executors.llm_executor import LLMExecutor


class LLMClient:
    """Thin wrapper around LLMExecutor for tool-style usage."""

    def __init__(self, executor: LLMExecutor | None = None) -> None:
        self.executor = executor or LLMExecutor()

    def generate(self, model: str, prompt: str, context: Dict[str, Any] | None = None) -> str:
        return self.executor.execute(
            config={"model": model, "prompt": prompt},
            inputs=context or {},
        )


