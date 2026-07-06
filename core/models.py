"""SQLAlchemy ORM models for clinical trial QC system."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, ForeignKey, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'clinical_qc.db')
DB_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def _uid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── Project ──

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=_uid)
    name = Column(String(200), nullable=False)
    protocol_number = Column(String(100))
    sponsor = Column(String(200))
    status = Column(String(20), default="active")  # active / archived
    created_at = Column(String(30), default=_now)
    updated_at = Column(String(30), default=_now)

    subjects = relationship("Subject", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("ReviewReport", back_populates="project", cascade="all, delete-orphan")


# ── Subject ──

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(36), primary_key=True, default=_uid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    subject_code = Column(String(50), nullable=False)  # e.g. "S-001-042"
    initials = Column(String(10))
    status = Column(String(20), default="active")  # screening / active / completed / withdrawn
    created_at = Column(String(30), default=_now)
    updated_at = Column(String(30), default=_now)

    project = relationship("Project", back_populates="subjects")
    documents = relationship("Document", back_populates="subject", cascade="all, delete-orphan")
    reports = relationship("ReviewReport", back_populates="subject", cascade="all, delete-orphan")


# ── Document ──

DOC_TYPES = [
    "protocol",              # 研究方案
    "investigator_brochure", # 研究者手册
    "drug_manual",           # 药物管理手册
    "screening_record",      # 筛选期病历
    "baseline_record",       # 基线期病历
    "visit_record",          # 随访病历
    "lab_report",            # 检查报告
    "diary_card",            # 日记卡
    "prick_test",            # 点刺试验记录
    "ae_record",             # AE/不良事件记录
    "cm_record",             # CM/合并用药记录
    "drug_dispense",         # 药物发放回收记录
    "other",                 # 其他
]

DOC_TYPE_LABELS = {
    "protocol": "研究方案",
    "investigator_brochure": "研究者手册",
    "drug_manual": "药物管理手册",
    "screening_record": "筛选期病历",
    "baseline_record": "基线期病历",
    "visit_record": "随访病历",
    "lab_report": "检查报告",
    "diary_card": "日记卡",
    "prick_test": "点刺试验记录",
    "ae_record": "AE/不良事件记录",
    "cm_record": "CM/合并用药记录",
    "drug_dispense": "药物发放回收记录",
    "other": "其他",
}


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_uid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True)
    doc_type = Column(String(50), nullable=False)
    doc_subtype = Column(String(50))  # e.g. V1/V2/V3 for visit_record
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, default=0)
    file_format = Column(String(20))  # pdf / docx / xlsx / txt / image
    parse_status = Column(String(20), default="pending")  # pending / parsing / completed / failed
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text)
    extracted_text = Column(Text)  # Full extracted text
    metadata_json = Column(Text, default="{}")
    created_at = Column(String(30), default=_now)

    project = relationship("Project", back_populates="documents")
    subject = relationship("Subject", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


# ── Document Chunk ──

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=_uid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chroma_id = Column(String(200))
    page_number = Column(Integer)
    created_at = Column(String(30), default=_now)

    document = relationship("Document", back_populates="chunks")


# ── Review Report ──

class ReviewReport(Base):
    __tablename__ = "review_reports"

    id = Column(String(36), primary_key=True, default=_uid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    status = Column(String(20), default="running")  # running / completed / failed
    overall_conclusion = Column(String(50))  # no_issue / needs_confirm / has_issue / critical
    overall_risk_summary = Column(Text)
    report_markdown = Column(Text)
    report_json = Column(Text)  # Structured JSON
    started_at = Column(String(30))
    completed_at = Column(String(30))
    created_at = Column(String(30), default=_now)

    project = relationship("Project", back_populates="reports")
    subject = relationship("Subject", back_populates="reports")
    findings = relationship("Finding", back_populates="report", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="report", cascade="all, delete-orphan")
    conversations = relationship("ReviewConversation", back_populates="report", cascade="all, delete-orphan")


# ── Finding (审核发现) ──

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=_uid)
    report_id = Column(String(36), ForeignKey("review_reports.id", ondelete="CASCADE"), nullable=False)
    finding_type = Column(String(30), nullable=False)  # definite / suspected / suggestion
    review_category = Column(String(30), nullable=False)  # inclusion / timeline / ae / cm / prick_test / lab / drug / completeness / query
    severity = Column(String(10), default="medium")  # high / medium / low
    title = Column(String(500))
    description = Column(Text, nullable=False)
    source_files = Column(Text)  # JSON array
    evidence = Column(Text)
    suggestion = Column(Text)
    query_statement = Column(Text)  # 建议澄清语句
    risk_impact = Column(Text)
    status = Column(String(20), default="open")  # open / confirmed / dismissed / fixed
    created_at = Column(String(30), default=_now)

    report = relationship("ReviewReport", back_populates="findings")


# ── Timeline Event ──

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True, default=_uid)
    report_id = Column(String(36), ForeignKey("review_reports.id", ondelete="CASCADE"), nullable=False)
    event_date = Column(String(30))
    event_time = Column(String(10))
    event_name = Column(String(300), nullable=False)
    source_file = Column(String(500))
    has_issue = Column(Boolean, default=False)
    issue_description = Column(Text)
    sort_order = Column(Integer, default=0)

    report = relationship("ReviewReport", back_populates="timeline_events")


# ── Knowledge Base Issue (历史问题库) ──

class KnowledgeBaseIssue(Base):
    __tablename__ = "knowledge_base_issues"

    id = Column(String(36), primary_key=True, default=_uid)
    review_category = Column(String(30), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    typical_cause = Column(Text)
    typical_query = Column(Text)
    occurrence_count = Column(Integer, default=1)
    tags = Column(Text)  # JSON array
    created_at = Column(String(30), default=_now)


# ── Review Conversation (追问) ──

class ReviewConversation(Base):
    __tablename__ = "review_conversations"

    id = Column(String(36), primary_key=True, default=_uid)
    report_id = Column(String(36), ForeignKey("review_reports.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(10), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    citations = Column(Text, default="[]")
    created_at = Column(String(30), default=_now)

    report = relationship("ReviewReport", back_populates="conversations")


# ── Global Chat Messages (Q&A Panel) ──

class ChatMessage(Base):
    """Chat messages for the global Q&A panel — optionally linked to a project."""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=_uid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(10), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    citations = Column(Text, default="[]")
    created_at = Column(String(30), default=_now)


# ── Init DB ──

def init_db():
    """Create all tables if they don't exist."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
