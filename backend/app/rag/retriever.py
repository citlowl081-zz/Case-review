"""Hybrid retriever — combines vector search with BM25 keyword matching."""
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from app.core.config import settings
from app.rag.vector_store import similarity_search, get_vector_store


class HybridRetriever:
    """Retriever that combines semantic vector search with BM25 keyword search.

    This is especially important for clinical trial documents where exact
    terminology matching (drug names, visit codes, lab values) matters alongside
    semantic understanding.
    """

    def __init__(self):
        self._bm25_retriever = None
        self._bm25_docs = []

    def _get_all_docs_from_store(self) -> List[Document]:
        """Fetch all documents from ChromaDB for BM25 indexing."""
        vector_store = get_vector_store()
        collection = vector_store._collection
        results = collection.get(include=["documents", "metadatas"])
        docs = []
        for content, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            docs.append(Document(page_content=content, metadata=meta or {}))
        return docs

    def _ensure_bm25_index(self):
        """Build/rebuild the BM25 index if needed."""
        all_docs = self._get_all_docs_from_store()
        # Rebuild if doc count changed
        if len(all_docs) != len(self._bm25_docs):
            self._bm25_docs = all_docs
            if all_docs:
                self._bm25_retriever = BM25Retriever.from_documents(all_docs)
                self._bm25_retriever.k = settings.HYBRID_TOP_K

    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        """Perform hybrid retrieval: vector + BM25, deduplicate, and merge.

        Returns:
            List of (Document, relevance_score) sorted by score descending
        """
        k = top_k or settings.RETRIEVAL_TOP_K

        # 1. Vector search (semantic)
        vector_results: List[Tuple[Document, float]] = similarity_search(query, k=settings.HYBRID_TOP_K)

        # 2. BM25 keyword search
        self._ensure_bm25_index()
        bm25_docs: List[Document] = []
        if self._bm25_retriever and self._bm25_docs:
            bm25_docs = self._bm25_retriever.invoke(query)

        # 3. Merge and deduplicate
        seen_contents = set()
        merged: List[Tuple[Document, float]] = []

        # Add vector results first (with their similarity scores)
        for doc, score in vector_results:
            key = doc.page_content[:200]  # Use first 200 chars as dedup key
            if key not in seen_contents:
                seen_contents.add(key)
                merged.append((doc, score))

        # Add BM25 results (assign a default score since BM25 scores are not directly comparable)
        for doc in bm25_docs:
            key = doc.page_content[:200]
            if key not in seen_contents:
                seen_contents.add(key)
                # Normalize: give BM25 results a score slightly below the average vector score
                merged.append((doc, 0.5))

        # 4. Sort by score descending
        merged.sort(key=lambda x: x[1], reverse=True)

        return merged[:k]


# Singleton
_hybrid_retriever: HybridRetriever = None


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever
