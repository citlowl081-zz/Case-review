"""ChromaDB vector store wrapper — persistence and CRUD."""
import uuid
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from app.core.config import settings
from app.rag.embeddings import get_embeddings

# Global ChromaDB client (lazy initialization)
_chroma_client: Optional[chromadb.PersistentClient] = None
_vector_store: Optional[Chroma] = None


def _get_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_vector_store() -> Chroma:
    """Get or create the Chroma vector store singleton."""
    global _vector_store
    if _vector_store is None:
        client = _get_client()
        _vector_store = Chroma(
            client=client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=get_embeddings(),
        )
    return _vector_store


def add_documents_to_store(docs: list, doc_id: str) -> List[str]:
    """Add document chunks to ChromaDB.

    Args:
        docs: List of LangChain Document objects (with page_content and metadata)
        doc_id: Parent document UUID for tracking

    Returns:
        List of ChromaDB chunk IDs
    """
    vector_store = get_vector_store()
    chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(docs))]

    # Assign chunk IDs and metadata
    for i, (doc, cid) in enumerate(zip(docs, chunk_ids)):
        doc.metadata["chunk_id"] = cid
        doc.metadata["document_id"] = doc_id
        doc.metadata["chunk_index"] = i

    vector_store.add_documents(documents=docs, ids=chunk_ids)
    return chunk_ids


def delete_document_from_store(document_id: str) -> int:
    """Delete all chunks belonging to a document from ChromaDB.

    Returns count of deleted chunks.
    """
    vector_store = get_vector_store()
    collection = vector_store._collection

    # Find all chunk IDs for this document
    results = collection.get(
        where={"document_id": document_id},
        include=["metadatas"],
    )
    ids_to_delete = results.get("ids", [])
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)


def similarity_search(query: str, k: int = None) -> list:
    """Semantic similarity search in ChromaDB."""
    vector_store = get_vector_store()
    k = k or settings.RETRIEVAL_TOP_K
    return vector_store.similarity_search_with_score(query, k=k)


def get_store_stats() -> dict:
    """Get collection statistics."""
    vector_store = get_vector_store()
    collection = vector_store._collection
    count = collection.count()
    return {
        "total_vectors": count,
        "collection_name": settings.CHROMA_COLLECTION_NAME,
    }
