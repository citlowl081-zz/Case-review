"""Knowledge-base-related request/response schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    doc_category: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class KnowledgeStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_size_bytes: int
    by_category: dict[str, int]
    by_status: dict[str, int]


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str


# --- Clinical Trial Review Schemas ---

class ReviewRequest(BaseModel):
    """Request to run a review agent on specific documents."""
    document_ids: list[str] = Field(..., min_length=1, description="待审核文档ID列表")
    review_types: list[str] = Field(
        default=["visit_window", "inclusion_exclusion", "ae_logic", "consistency"],
        description="审核类型: visit_window, inclusion_exclusion, ae_logic, consistency"
    )


class ReviewFinding(BaseModel):
    """A single finding from the review agent."""
    review_type: str = Field(..., description="审核类型")
    severity: str = Field(..., description="风险等级: 高/中/低")
    description: str = Field(..., description="问题描述")
    source_reference: str = Field(..., description="依据来源")
    suggestion: str = Field(..., description="修改建议")


class ReviewResponse(BaseModel):
    """Complete review output."""
    document_id: str
    document_name: str
    findings: list[ReviewFinding]
    summary: str
    reviewed_at: str
