"""Database helpers: CRUD operations for the clinical QC system."""
from contextlib import contextmanager
from core.models import (
    SessionLocal, init_db,
    Project, Subject, Document, DocumentChunk,
    ReviewReport, Finding, TimelineEvent,
    KnowledgeBaseIssue, ReviewConversation, ChatMessage,
)
from core.models import DOC_TYPES, DOC_TYPE_LABELS


def ensure_db():
    """Initialize database tables if needed."""
    init_db()


@contextmanager
def db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Project CRUD ──

def create_project(name: str, protocol_number: str = "", sponsor: str = "") -> Project:
    with db_session() as db:
        p = Project(name=name, protocol_number=protocol_number, sponsor=sponsor)
        db.add(p)
        db.flush()
        db.refresh(p)
        return p


def get_all_projects() -> list:
    with db_session() as db:
        return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project(project_id: str) -> Project:
    with db_session() as db:
        return db.query(Project).filter(Project.id == project_id).first()


def delete_project(project_id: str):
    with db_session() as db:
        db.query(Project).filter(Project.id == project_id).delete()
    # Also clean up ChromaDB collection
    try:
        from rag.engine import delete_project_collection
        delete_project_collection(project_id)
    except Exception:
        pass


# ── Subject CRUD ──

def create_subject(project_id: str, subject_code: str, initials: str = "") -> Subject:
    with db_session() as db:
        s = Subject(project_id=project_id, subject_code=subject_code, initials=initials)
        db.add(s)
        db.flush()
        db.refresh(s)
        return s


def get_project_subjects(project_id: str) -> list:
    with db_session() as db:
        return db.query(Subject).filter(
            Subject.project_id == project_id
        ).order_by(Subject.created_at.desc()).all()


def get_subject(subject_id: str) -> Subject:
    with db_session() as db:
        return db.query(Subject).filter(Subject.id == subject_id).first()


def delete_subject(subject_id: str):
    with db_session() as db:
        db.query(Subject).filter(Subject.id == subject_id).delete()


# ── Document CRUD ──

def create_document(
    project_id: str,
    subject_id: str,
    doc_type: str,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int = 0,
    file_format: str = "",
    doc_subtype: str = "",
    extracted_text: str = "",
) -> Document:
    with db_session() as db:
        d = Document(
            project_id=project_id,
            subject_id=subject_id,
            doc_type=doc_type,
            doc_subtype=doc_subtype,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_format=file_format,
            parse_status="pending",
            extracted_text=extracted_text,
        )
        db.add(d)
        db.flush()
        db.refresh(d)
        return d


def update_document_status(doc_id: str, status: str, error_message: str = ""):
    with db_session() as db:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.parse_status = status
            if error_message:
                doc.error_message = error_message


def update_document_text(doc_id: str, extracted_text: str, chunk_count: int = 0):
    with db_session() as db:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.extracted_text = extracted_text
            doc.chunk_count = chunk_count
            doc.parse_status = "completed"


def get_project_documents(project_id: str, subject_id: str = None) -> list:
    with db_session() as db:
        q = db.query(Document).filter(Document.project_id == project_id)
        if subject_id:
            q = q.filter(Document.subject_id == subject_id)
        return q.order_by(Document.created_at.desc()).all()


def get_document(doc_id: str) -> Document:
    with db_session() as db:
        return db.query(Document).filter(Document.id == doc_id).first()


def delete_document(doc_id: str):
    with db_session() as db:
        db.query(Document).filter(Document.id == doc_id).delete()


# ── Report CRUD ──

def create_report(project_id: str, subject_id: str) -> ReviewReport:
    from datetime import datetime, timezone
    with db_session() as db:
        r = ReviewReport(
            project_id=project_id,
            subject_id=subject_id,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(r)
        db.flush()
        db.refresh(r)
        return r


def save_report(
    report_id: str,
    markdown: str,
    report_json: str,
    conclusion: str,
    risk_summary: str,
):
    from datetime import datetime, timezone
    with db_session() as db:
        r = db.query(ReviewReport).filter(ReviewReport.id == report_id).first()
        if r:
            r.status = "completed"
            r.report_markdown = markdown
            r.report_json = report_json
            r.overall_conclusion = conclusion
            r.overall_risk_summary = risk_summary
            r.completed_at = datetime.now(timezone.utc).isoformat()


def fail_report(report_id: str, error: str):
    with db_session() as db:
        r = db.query(ReviewReport).filter(ReviewReport.id == report_id).first()
        if r:
            r.status = "failed"
            r.overall_risk_summary = error


def get_subject_reports(subject_id: str) -> list:
    with db_session() as db:
        return db.query(ReviewReport).filter(
            ReviewReport.subject_id == subject_id
        ).order_by(ReviewReport.created_at.desc()).all()


def get_report(report_id: str) -> ReviewReport:
    with db_session() as db:
        return db.query(ReviewReport).filter(ReviewReport.id == report_id).first()


# ── Finding CRUD ──

def add_findings(report_id: str, findings_list: list):
    """Bulk insert findings for a report."""
    with db_session() as db:
        for f_data in findings_list:
            f = Finding(
                report_id=report_id,
                finding_type=f_data.get("type", "suspected"),
                review_category=f_data.get("review_category", f_data.get("category", "other")),
                severity=f_data.get("severity", "medium"),
                title=f_data.get("title", ""),
                description=f_data.get("description", ""),
                source_files=str(f_data.get("source_files", [])),
                evidence=f_data.get("evidence", ""),
                suggestion=f_data.get("suggestion", ""),
                query_statement=f_data.get("query_statement", ""),
                risk_impact=f_data.get("risk_impact", ""),
            )
            db.add(f)


def get_report_findings(report_id: str, category: str = None) -> list:
    with db_session() as db:
        q = db.query(Finding).filter(Finding.report_id == report_id)
        if category:
            q = q.filter(Finding.review_category == category)
        return q.all()


# ── Timeline CRUD ──

def add_timeline_events(report_id: str, events: list):
    with db_session() as db:
        for i, ev in enumerate(events):
            te = TimelineEvent(
                report_id=report_id,
                event_date=ev.get("date", ""),
                event_time=ev.get("time", ""),
                event_name=ev.get("event", ""),
                source_file=ev.get("source_file", ""),
                has_issue=ev.get("has_issue", False),
                issue_description=ev.get("issue_description", ""),
                sort_order=i,
            )
            db.add(te)


def get_report_timeline(report_id: str) -> list:
    with db_session() as db:
        return db.query(TimelineEvent).filter(
            TimelineEvent.report_id == report_id
        ).order_by(TimelineEvent.sort_order).all()


# ── Conversation CRUD ──

def add_conversation(report_id: str, role: str, content: str, citations: str = "[]"):
    with db_session() as db:
        c = ReviewConversation(
            report_id=report_id,
            role=role,
            content=content,
            citations=citations,
        )
        db.add(c)
        return c


def get_report_conversations(report_id: str) -> list:
    with db_session() as db:
        return db.query(ReviewConversation).filter(
            ReviewConversation.report_id == report_id
        ).order_by(ReviewConversation.created_at.asc()).all()


# ── Knowledge Base CRUD ──

def add_kb_issue(category: str, title: str, description: str,
                  typical_cause: str = "", typical_query: str = "", tags: str = "[]"):
    with db_session() as db:
        # Check if similar issue already exists
        existing = db.query(KnowledgeBaseIssue).filter(
            KnowledgeBaseIssue.review_category == category,
            KnowledgeBaseIssue.title == title,
        ).first()
        if existing:
            existing.occurrence_count += 1
        else:
            ki = KnowledgeBaseIssue(
                review_category=category,
                title=title,
                description=description,
                typical_cause=typical_cause,
                typical_query=typical_query,
                tags=tags,
            )
            db.add(ki)


def search_kb_issues(category: str = None, query: str = None) -> list:
    with db_session() as db:
        q = db.query(KnowledgeBaseIssue)
        if category:
            q = q.filter(KnowledgeBaseIssue.review_category == category)
        q = q.order_by(KnowledgeBaseIssue.occurrence_count.desc())
        return q.limit(20).all()


# ── Global Chat CRUD (Q&A Panel) ──

def add_chat_message(project_id: str, role: str, content: str, citations: str = "[]"):
    with db_session() as db:
        msg = ChatMessage(
            project_id=project_id,
            role=role,
            content=content,
            citations=citations,
        )
        db.add(msg)
        return msg


def get_chat_messages(project_id: str = None) -> list:
    """Get chat messages for a project (or global if project_id is None)."""
    with db_session() as db:
        q = db.query(ChatMessage)
        if project_id:
            q = q.filter(ChatMessage.project_id == project_id)
        else:
            q = q.filter(ChatMessage.project_id.is_(None))
        return q.order_by(ChatMessage.created_at.asc()).all()
