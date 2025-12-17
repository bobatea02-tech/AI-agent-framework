from __future__ import annotations

from typing import List


class RAGRetriever:
    """Stub retriever for FAISS/ChromaDB backed document search."""

    def __init__(self, index_path: str | None = None) -> None:
        self.index_path = index_path or "data/index.faiss"

    def search(self, query: str, k: int = 5) -> List[dict]:
        # TODO: integrate FAISS/Chroma
        return [{"id": i, "snippet": f"Result {i} for {query}"} for i in range(k)]


