"""Knowledge base routes — upload, list, delete documents (admin only)."""
import os
import uuid
import asyncio
from typing import Optional
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_admin_user, PaginationParams
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.knowledge import (
    DocumentResponse,
    DocumentListResponse,
    KnowledgeStatsResponse,
    UploadResponse,
    ReviewRequest,
    ReviewResponse,
    ReviewFinding,
)
from app.rag.vector_store import get_store_stats

router = APIRouter()


def _validate_file(filename: str) -> str:
    """Validate file extension and return file type."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式: {ext}。支持格式: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}",
        )
    return ext


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Form(default="other"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """上传文档到知识库（仅管理员）."""
    # Validate
    ext = _validate_file(file.filename)
    file_size = 0

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE_MB}MB)",
        )

    # Save to disk with unique name
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    document = Document(
        id=doc_id,
        filename=file.filename,
        file_type=ext.lstrip("."),
        doc_category=category,
        file_path=file_path,
        file_size=file_size,
        status="uploading",
        uploader_id=admin.id,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Trigger async document processing (Celery task)
    try:
        from app.tasks.doc_process import process_document
        process_document.delay(doc_id, file_path, ext.lstrip("."))
    except Exception as e:
        # Celery 不可用 — 降级为同步处理，避免文档永远卡在 "uploading" 状态
        logger.warning(f"Celery 不可用，降级为同步处理文档 {doc_id}: {e}")
        try:
            asyncio.ensure_future(_run_sync_process(doc_id, file_path, ext.lstrip(".")))
        except Exception as sync_e:
            logger.error(f"同步处理文档 {doc_id} 也失败: {sync_e}")

    return UploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        message="文档已上传，正在后台处理",
    )


async def _run_sync_process(doc_id: str, file_path: str, file_type: str):
    """降级方案：在当前进程中同步处理文档"""
    from app.core.database import async_session_factory
    from app.services.kb_service import process_document_sync
    async with async_session_factory() as db:
        try:
            await process_document_sync(doc_id, file_path, file_type, db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"同步处理文档 {doc_id} 失败: {e}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(default=None, description="按分类筛选"),
    status: Optional[str] = Query(default=None, description="按状态筛选"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取文档列表（仅管理员）."""
    # Build query
    query = select(Document)
    count_query = select(func.count(Document.id))

    if category:
        query = query.where(Document.doc_category == category)
        count_query = count_query.where(Document.doc_category == category)
    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Document.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    documents = result.scalars().all()

    doc_list = []
    for d in documents:
        doc_list.append(
            DocumentResponse(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                doc_category=d.doc_category,
                file_size=d.file_size or 0,
                status=d.status,
                chunk_count=d.chunk_count or 0,
                error_message=d.error_message,
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
        )

    return DocumentListResponse(documents=doc_list, total=total)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除文档及其向量数据（仅管理员）."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    # Delete from ChromaDB
    from app.rag.vector_store import delete_document_from_store
    deleted_vectors = delete_document_from_store(document_id)

    # Delete file from disk
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from DB (cascades to chunks)
    await db.delete(document)
    await db.flush()

    return {
        "message": "文档已删除",
        "deleted_chunks": deleted_vectors,
    }


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库统计信息（仅管理员）."""
    # DB stats
    total_docs_result = await db.execute(select(func.count(Document.id)))
    total_docs = total_docs_result.scalar() or 0

    total_chunks_result = await db.execute(select(func.sum(Document.chunk_count)))
    total_chunks = total_chunks_result.scalar() or 0

    total_size_result = await db.execute(select(func.sum(Document.file_size)))
    total_size = total_size_result.scalar() or 0

    # By category
    cat_result = await db.execute(
        select(Document.doc_category, func.count(Document.id)).group_by(Document.doc_category)
    )
    by_category = {row[0]: row[1] for row in cat_result.all()}

    # By status
    status_result = await db.execute(
        select(Document.status, func.count(Document.id)).group_by(Document.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    # ChromaDB stats
    chroma_stats = get_store_stats()

    return KnowledgeStatsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks or chroma_stats["total_vectors"],
        total_size_bytes=total_size or 0,
        by_category=by_category,
        by_status=by_status,
    )


@router.post("/review", response_model=ReviewResponse)
async def review_documents(
    req: ReviewRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """对指定文档进行临床审核（仅管理员）."""
    from datetime import datetime, timezone
    from app.rag.chain import run_structured_review

    # Fetch document content from DB
    documents_content = []
    doc_names = []
    for doc_id in req.document_ids:
        result = await db.execute(
            select(Document).where(Document.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 {doc_id} 不存在",
            )
        doc_names.append(doc.filename)

        # Get all chunks for this document
        chunks_result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == doc_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()
        if chunks:
            doc_content = "\n\n".join([c.content for c in chunks])
        else:
            # Fallback: try to load from file
            try:
                from app.rag.loader import load_document
                loaded_docs = load_document(doc.file_path, doc.file_type)
                doc_content = "\n\n".join([d.page_content for d in loaded_docs])
            except Exception:
                doc_content = f"[无法加载文档内容: {doc.filename}]"

        documents_content.append(f"--- 文档: {doc.filename} ---\n{doc_content}")

    if not documents_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可审核的文档内容",
        )

    combined_content = "\n\n".join(documents_content)

    # Run structured review
    result = await run_structured_review(
        content=combined_content,
        review_types=req.review_types,
    )

    # Build response
    findings = []
    for f in result.get("findings", []):
        findings.append(
            ReviewFinding(
                review_type=f.get("review_type", ""),
                severity=f.get("severity", "中"),
                description=f.get("description", ""),
                source_reference=f.get("source_reference", ""),
                suggestion=f.get("suggestion", ""),
            )
        )

    return ReviewResponse(
        document_id=req.document_ids[0],
        document_name=", ".join(doc_names),
        findings=findings,
        summary=result.get("summary", "审核完成"),
        reviewed_at=datetime.now(timezone.utc).isoformat(),
    )
