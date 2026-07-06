"""Knowledge base service — document processing orchestration."""
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from app.models.document import Document, DocumentChunk
from app.rag.loader import load_document
from app.rag.chunker import split_documents
from app.rag.vector_store import add_documents_to_store


async def process_document_sync(
    doc_id: str,
    file_path: str,
    file_type: str,
    db: AsyncSession,
) -> None:
    """Synchronous document processing pipeline (used when Celery is unavailable).

    Steps:
    1. Load document with appropriate LangChain loader
    2. Split into chunks with clinical-trial-aware separators
    3. Embed and store in ChromaDB
    4. Update document status in PostgreSQL
    """
    # Get document record
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalar_one_or_none()
    if not document:
        logger.error(f"Document {doc_id} not found")
        return

    try:
        # Step 1: Update status → parsing
        document.status = "parsing"
        await db.flush()

        # Step 2: Load document
        logger.info(f"Loading document: {file_path}")
        docs = load_document(file_path, file_type)

        if not docs:
            raise ValueError("文档解析结果为空，请检查文件内容")

        # Step 3: Update status → embedding & split
        document.status = "embedding"
        await db.flush()

        # Step 4: Split into chunks
        chunks = split_documents(docs)
        logger.info(f"Split into {len(chunks)} chunks")

        # Step 5: Add to ChromaDB
        chunk_ids = add_documents_to_store(chunks, doc_id)

        # Step 6: Save chunk records to PostgreSQL
        for i, (chunk, chroma_id) in enumerate(zip(chunks, chunk_ids)):
            chunk_record = DocumentChunk(
                document_id=doc_id,
                chunk_index=i,
                content=chunk.page_content,
                chroma_id=chroma_id,
                metadata_=str(chunk.metadata),
            )
            db.add(chunk_record)

        # Step 7: Update document status → completed
        document.status = "completed"
        document.chunk_count = len(chunks)
        await db.flush()

        logger.info(f"Document {doc_id} processed successfully: {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        document.status = "failed"
        document.error_message = str(e)
        await db.flush()
