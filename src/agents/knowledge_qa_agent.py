from __future__ import annotations

from typing import Any, Dict

from src.tools.llm_client import LLMClient
from src.tools.rag_retriever import RAGRetriever


class KnowledgeQAAgent:
    """Reference RAG-backed Q&A agent."""

    def __init__(self) -> None:
        self.retriever = RAGRetriever()
        self.llm = LLMClient()

    def answer(self, query: str) -> Dict[str, Any]:
        documents = self.retriever.search(query)
        context = "\n".join([d["snippet"] for d in documents])
        answer = self.llm.generate(model="gpt-4", prompt="Answer with citations:\n{context}\nQ: {query}", context={"context": context, "query": query})
        return {"answer": answer, "sources": documents}


