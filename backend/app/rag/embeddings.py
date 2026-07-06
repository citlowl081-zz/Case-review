"""Embeddings factory — DashScope (阿里云百炼) with custom HTTP client.

Uses direct httpx calls because the openai SDK formats embedding requests
in a way incompatible with DashScope's OpenAI-compatible endpoint.
"""
from typing import List
import httpx
from langchain_core.embeddings import Embeddings
from app.core.config import settings


class DashScopeEmbeddings(Embeddings):
    """Custom embedding class that calls DashScope compatible API via httpx."""

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.model = model or settings.EMBEDDING_MODEL
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = (base_url or settings.DASHSCOPE_BASE_URL).rstrip("/")
        self._client = httpx.Client(timeout=60)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = []
        for text in texts:
            resp = self._client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text,
                },
            )
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Embedding API error {resp.status_code}: {resp.text[:500]}"
                )
            data = resp.json()
            embeddings.append(data["data"][0]["embedding"])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.embed_documents([text])[0]


# Singleton
_embeddings: DashScopeEmbeddings = None


def get_embeddings() -> DashScopeEmbeddings:
    """Get or create the DashScope embeddings singleton."""
    global _embeddings
    if _embeddings is None:
        _embeddings = DashScopeEmbeddings()
    return _embeddings
