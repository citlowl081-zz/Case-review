"""
测试 app/schemas/ — Pydantic 请求/响应模型
"""
import pytest
from app.schemas.auth import RegisterRequest, LoginRequest, ChangePasswordRequest
from app.schemas.chat import ChatRequest, Citation, MessageFeedbackRequest
from app.schemas.session import SessionCreateRequest, SessionUpdateRequest
from app.schemas.knowledge import DocumentResponse


class TestAuthSchemas:
    """测试认证相关的 Schema"""

    def test_register_request_valid(self):
        """有效的注册请求"""
        req = RegisterRequest(
            username="testuser",
            password="123456",
            confirm_password="123456",
        )
        assert req.username == "testuser"

    def test_register_username_too_short(self):
        """用户名太短"""
        with pytest.raises(Exception):
            RegisterRequest(username="ab", password="123456", confirm_password="123456")

    def test_register_password_too_short(self):
        """密码太短"""
        with pytest.raises(Exception):
            RegisterRequest(username="validuser", password="12", confirm_password="12")

    def test_login_request(self):
        """登录请求"""
        req = LoginRequest(username="admin", password="123456")
        assert req.username == "admin"
        assert req.password == "123456"

    def test_change_password_request(self):
        """修改密码请求"""
        req = ChangePasswordRequest(
            old_password="old",
            new_password="new123",
            confirm_password="new123",
        )
        assert req.old_password == "old"
        assert req.new_password == "new123"


class TestChatSchemas:
    """测试聊天相关的 Schema"""

    def test_chat_request(self):
        """聊天请求"""
        req = ChatRequest(message="试验药物保存温度是多少？")
        assert "温度" in req.message

    def test_chat_request_empty_message(self):
        """空消息被拒绝"""
        with pytest.raises(Exception):
            ChatRequest(message="")

    def test_citation_model(self):
        """引用模型"""
        cit = Citation(
            doc_name="研究方案v3.pdf",
            chunk_text="温度应为2-8℃",
            page=12,
            chunk_id="doc123_chunk_0",
        )
        assert cit.doc_name == "研究方案v3.pdf"
        assert cit.page == 12

    def test_feedback_valid_values(self):
        """反馈值范围"""
        req1 = MessageFeedbackRequest(feedback=1)
        assert req1.feedback == 1

        req2 = MessageFeedbackRequest(feedback=-1)
        assert req2.feedback == -1

    def test_feedback_invalid_value(self):
        """无效反馈值"""
        with pytest.raises(Exception):
            MessageFeedbackRequest(feedback=99)


class TestSessionSchemas:
    """测试会话相关的 Schema"""

    def test_create_session_default_title(self):
        """创建会话默认标题"""
        req = SessionCreateRequest()
        assert req.title == "新对话"

    def test_create_session_custom_title(self):
        """自定义会话标题"""
        req = SessionCreateRequest(title="临床试验方案审核")
        assert req.title == "临床试验方案审核"

    def test_update_session(self):
        """更新会话"""
        req = SessionUpdateRequest(title="重命名的会话")
        assert req.title == "重命名的会话"

    def test_update_session_empty_title(self):
        """空标题被拒绝"""
        with pytest.raises(Exception):
            SessionUpdateRequest(title="")


class TestKnowledgeSchemas:
    """测试知识库相关的 Schema"""

    def test_document_response_fields(self):
        """文档响应字段"""
        from datetime import datetime
        doc = DocumentResponse(
            id="doc-123",
            filename="test.pdf",
            file_type="pdf",
            doc_category="study_protocol",
            file_size=1024,
            status="completed",
            chunk_count=5,
            created_at=datetime.now().isoformat(),
        )
        assert doc.id == "doc-123"
        assert doc.status == "completed"
        assert doc.chunk_count == 5
