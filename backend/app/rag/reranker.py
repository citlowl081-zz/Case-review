"""Re-ranker — improves retrieval precision by re-scoring top candidates."""
from typing import List, Tuple
from langchain_core.documents import Document


class SimpleReranker:
    """Lightweight re-ranker that uses keyword overlap scoring.

    For production, consider a cross-encoder model like bge-reranker-v2-m3
    or using the DashScope re-rank API.
    """

    def rerank(
        self, query: str, docs: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """Re-score documents based on keyword overlap with the query.

        Args:
            query: The search query
            docs: List of (Document, initial_score) tuples

        Returns:
            Re-ranked list of (Document, final_score) tuples
        """
        query_terms = set(query.lower().split())

        reranked = []
        for doc, score in docs:
            content_lower = doc.page_content.lower()
            content_terms = set(content_lower.split())

            # Calculate term overlap ratio
            if query_terms:
                overlap = len(query_terms & content_terms) / len(query_terms)
            else:
                overlap = 0

            # Combine vector similarity (0-1) with keyword overlap
            final_score = score * 0.6 + overlap * 0.4
            reranked.append((doc, final_score))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked


# Singleton
_reranker: SimpleReranker = None


def get_reranker() -> SimpleReranker:
    global _reranker
    if _reranker is None:
        _reranker = SimpleReranker()
    return _reranker
