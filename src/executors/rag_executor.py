from __future__ import annotations

from typing import Any, Dict

from src.tools.rag_retriever import RAGRetriever
from .base import BaseExecutor


class RAGRetrieverExecutor(BaseExecutor):
    """Executor wrapper around the RAG retriever tool."""

    def __init__(self, retriever: RAGRetriever | None = None) -> None:
        self.retriever = retriever or RAGRetriever()

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
        query = inputs.get("query", "")
        k = config.get("k", 5)
        return self.retriever.search(query=query, k=k)


