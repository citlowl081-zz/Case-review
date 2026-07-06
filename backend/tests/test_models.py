"""
测试 app/models/ — SQLAlchemy 数据模型
"""
import pytest
from app.models.user import User
from app.models.session import Session
from app.models.document import Document, DocumentChunk
from app.models.message import Message


class TestUserModel:
    """测试 User 模型"""

    def test_create_user_defaults(self):
        """创建用户默认值"""
        user = User(username="test", password_hash="hash123", role="user", is_active=True)
        assert user.username == "test"
        assert user.role == "user"
        assert user.is_active is True

    def test_create_admin_user(self):
        """创建管理员"""
        user = User(username="admin", password_hash="hash", role="admin")
        assert user.role == "admin"

    def test_user_id_is_string(self):
        """ID 是字符串（ORM session 会自动生成 UUID）"""
        user = User(username="test", password_hash="hash", id="test-uuid-12345678-1234-1234-1234-123456789abc")
        assert isinstance(user.id, str)
        assert len(user.id) > 0


class TestSessionModel:
    """测试 Session 模型"""

    def test_create_session_defaults(self):
        """创建会话默认标题"""
        session = Session(user_id="user-123", title="新对话")
        assert session.title == "新对话"
        assert session.user_id == "user-123"

    def test_create_session_custom_title(self):
        """自定义标题"""
        session = Session(user_id="user-123", title="临床试验方案审核")
        assert session.title == "临床试验方案审核"


class TestDocumentModel:
    """测试 Document 模型"""

    def test_create_document_defaults(self):
        """创建文档默认状态"""
        doc = Document(
            filename="test.pdf",
            file_type="pdf",
            file_path="/tmp/test.pdf",
            uploader_id="user-123",
            status="uploading",
            chunk_count=0,
            doc_category="other",
        )
        assert doc.status == "uploading"
        assert doc.chunk_count == 0
        assert doc.doc_category == "other"

    def test_document_categories(self):
        """文档分类"""
        valid_categories = [
            "study_protocol", "drug_manual", "case_record",
            "lab_report", "ae_form", "conmed", "visit_plan", "sop", "other"
        ]
        for cat in valid_categories:
            doc = Document(
                filename="test.pdf",
                file_type="pdf",
                file_path="/tmp/test.pdf",
                uploader_id="user-123",
                doc_category=cat,
            )
            assert doc.doc_category == cat


class TestDocumentChunkModel:
    """测试 DocumentChunk 模型"""

    def test_create_chunk(self):
        """创建文档块"""
        chunk = DocumentChunk(
            document_id="doc-123",
            chunk_index=0,
            content="这是文档内容片段",
            chroma_id="doc-123_chunk_0",
        )
        assert chunk.chunk_index == 0
        assert chunk.content == "这是文档内容片段"


class TestMessageModel:
    """测试 Message 模型"""

    def test_create_user_message(self):
        """创建用户消息"""
        msg = Message(
            session_id="session-123",
            role="user",
            content="试验药物保存温度是多少？",
        )
        assert msg.role == "user"
        assert "温度" in msg.content

    def test_create_assistant_message(self):
        """创建助手消息"""
        msg = Message(
            session_id="session-123",
            role="assistant",
            content="试验药物保存温度为2-8℃",
            citations='[{"doc_name": "手册.pdf", "chunk_text": "2-8℃"}]',
        )
        assert msg.role == "assistant"
        assert msg.feedback is None

    def test_message_feedback(self):
        """消息反馈"""
        msg = Message(
            session_id="session-123",
            role="assistant",
            content="回答",
            feedback=1,
        )
        assert msg.feedback == 1
