"""RAG Engine — wraps ChromaDB + LangChain for project-isolated retrieval."""
import os
import sys
from typing import List, Tuple, Optional

# Import from existing backend RAG modules
_backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from app.rag.embeddings import get_embeddings
from app.rag.retriever import HybridRetriever
from app.rag.reranker import get_reranker
from app.core.config import settings


# ── ChromaDB collections per project ──

_chroma_client: Optional[chromadb.PersistentClient] = None
_collections: dict = {}  # project_id -> Chroma instance


def _get_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def _collection_name(project_id: str) -> str:
    # Sanitize project_id for ChromaDB
    return f"project_{project_id.replace('-', '_')}"


def get_project_store(project_id: str) -> Chroma:
    """Get or create a ChromaDB collection for a specific project."""
    col_name = _collection_name(project_id)
    if project_id not in _collections:
        client = _get_client()
        _collections[project_id] = Chroma(
            client=client,
            collection_name=col_name,
            embedding_function=get_embeddings(),
        )
    return _collections[project_id]


def add_documents(project_id: str, docs: List[Document], chunk_ids: List[str] = None) -> List[str]:
    """Add document chunks to a project's vector store."""
    store = get_project_store(project_id)
    if chunk_ids is None:
        chunk_ids = [f"{project_id}_chunk_{i}" for i in range(len(docs))]
    store.add_documents(documents=docs, ids=chunk_ids)
    return chunk_ids


def delete_project_collection(project_id: str):
    """Delete an entire project's collection."""
    col_name = _collection_name(project_id)
    try:
        client = _get_client()
        client.delete_collection(col_name)
    except Exception:
        pass
    if project_id in _collections:
        del _collections[project_id]


def delete_document_chunks(project_id: str, document_id: str) -> int:
    """Delete all chunks for a specific document."""
    store = get_project_store(project_id)
    try:
        collection = store._collection
        results = collection.get(where={"document_id": document_id})
        ids = results.get("ids", [])
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception:
        return 0


# ── Chunking ──

CLINICAL_SEPARATORS = [
    "\n\n", "\n", "。", "；", "; ", "，", ", ", " ", "",
]


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 80) -> List[Document]:
    """Split text into chunks optimized for RAG retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CLINICAL_SEPARATORS,
        length_function=len,
    )
    return splitter.create_documents([text])


# ── Hybrid Retrieval ──

_hybrid_retrievers: dict = {}


def get_retriever(project_id: str) -> HybridRetriever:
    """Get a hybrid retriever for a project."""
    if project_id not in _hybrid_retrievers:
        _hybrid_retrievers[project_id] = HybridRetriever()
    return _hybrid_retrievers[project_id]


def search(project_id: str, query: str, top_k: int = 10) -> List[Tuple[Document, float]]:
    """Search the project's knowledge base using vector similarity."""
    store = get_project_store(project_id)
    try:
        return store.similarity_search_with_score(query, k=top_k)
    except Exception:
        return []


def search_and_rerank(project_id: str, query: str, top_k: int = 10) -> List[Tuple[Document, float]]:
    """Search + rerank for higher precision."""
    retrieved = search(project_id, query, top_k=top_k * 2)
    reranker = get_reranker()
    return reranker.rerank(query, retrieved)[:top_k]


# ── Cross-Project Search ──

def search_all_projects(query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
    """Search across ALL project ChromaDB collections.

    Used by the global Q&A panel to search the entire knowledge base
    regardless of which project is currently selected.

    Returns:
        List of (Document, score) sorted by relevance descending
    """
    try:
        client = _get_client()
        all_collections = client.list_collections()
        project_cols = [c for c in all_collections if c.name.startswith("project_")]

        if not project_cols:
            return []

        all_results = []
        for col in project_cols:
            try:
                # Create a Chroma instance for this collection
                store = Chroma(
                    client=client,
                    collection_name=col.name,
                    embedding_function=get_embeddings(),
                )
                results = store.similarity_search_with_score(query, k=top_k)
                all_results.extend(results)
            except Exception:
                continue

        # Deduplicate by content prefix
        seen = set()
        unique = []
        for doc, score in all_results:
            key = doc.page_content[:200]
            if key not in seen:
                seen.add(key)
                unique.append((doc, score))

        # Sort by score descending (lower distance = more relevant)
        unique.sort(key=lambda x: x[1])

        return unique[:top_k]
    except Exception:
        return []


# ── Document Loading Pipeline ──

def load_and_index_document(
    project_id: str,
    document_id: str,
    text: str,
    metadata: dict = None,
    chunk_size: int = 800,
) -> int:
    """Load text, split into chunks, embed, and index in ChromaDB.

    Returns number of chunks created.
    """
    chunks = split_text(text, chunk_size=chunk_size)
    if not chunks:
        return 0

    # Attach metadata to each chunk
    base_meta = metadata or {}
    base_meta["document_id"] = document_id
    chunk_ids = []

    for i, chunk in enumerate(chunks):
        cid = f"{document_id}_chunk_{i}"
        chunk_ids.append(cid)
        chunk.metadata.update(base_meta)
        chunk.metadata["chunk_index"] = i

    add_documents(project_id, chunks, chunk_ids)
    return len(chunks)
