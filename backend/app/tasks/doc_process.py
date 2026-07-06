"""Celery task for async document processing."""
import asyncio
from loguru import logger
from app.tasks.celery_app import celery_app
from app.core.database import async_session_factory
from app.services.kb_service import process_document_sync


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, doc_id: str, file_path: str, file_type: str):
    """Process an uploaded document asynchronously.

    Steps: Load → Chunk → Embed → Store in ChromaDB.
    Retries on failure with exponential backoff.
    """
    logger.info(f"[Task] Processing document {doc_id}: {file_path}")

    async def _run():
        async with async_session_factory() as db:
            try:
                await process_document_sync(doc_id, file_path, file_type, db)
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise e

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create new loop for sync context
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(_run())
        else:
            loop.run_until_complete(_run())
        return {"doc_id": doc_id, "status": "completed"}
    except Exception as exc:
        logger.error(f"[Task] Failed to process document {doc_id}: {exc}")
        raise self.retry(exc=exc)
