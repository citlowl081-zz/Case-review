"""
测试 app/api/auth.py — 认证 API 路由（FastAPI TestClient）
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """创建 TestClient"""
    from app.main import app
    return TestClient(app)


class TestRegisterAPI:
    """测试注册接口"""

    def test_register_success(self, client):
        """注册 — mock 数据库完整流程"""
        import datetime

        # Create a realistic mock user that gets "populated" by db.refresh
        real_user_id = "new-user-id-999"
        new_user = None

        mock_db = AsyncMock()

        async def mock_flush():
            pass

        async def mock_refresh(user):
            # Simulate DB populating the user after flush+refresh
            user.id = real_user_id
            user.role = "user"
            user.is_active = True
            user.created_at = datetime.datetime.now()

        mock_db.flush = mock_flush
        mock_db.refresh = mock_refresh

        # Mock user existence check — no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(*args, **kwargs):
            return mock_result

        mock_db.execute = mock_execute

        from app.core.database import get_db
        app = client.app
        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.post("/api/auth/register", json={
            "username": "newuser999",
            "password": "password123",
            "confirm_password": "password123",
        })
        app.dependency_overrides.clear()

        assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser999"
        assert data["user"]["role"] == "user"

    def test_register_password_mismatch(self, client):
        """密码不匹配"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "password123",
            "confirm_password": "different",
        })
        assert response.status_code == 400
        assert "不一致" in response.json()["detail"]

    def test_register_short_username(self, client):
        """用户名太短"""
        response = client.post("/api/auth/register", json={
            "username": "ab",
            "password": "123456",
            "confirm_password": "123456",
        })
        assert response.status_code == 422


class TestLoginAPI:
    """测试登录接口"""

    def test_login_wrong_credentials(self, client):
        """错误的用户名密码"""
        # Mock no user found
        with patch("app.api.auth.select") as mock_select:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db = AsyncMock()
            mock_db.execute.return_value = mock_result

            from app.core.database import get_db
            app = client.app
            app.dependency_overrides[get_db] = lambda: mock_db

            response = client.post("/api/auth/login", json={
                "username": "nonexistent",
                "password": "wrong",
            })
            app.dependency_overrides.clear()

            assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """缺少字段"""
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422


class TestChangePasswordAPI:
    """测试修改密码接口"""

    def test_change_password_no_auth(self, client):
        """未认证请求被拒绝（401 或 403）"""
        response = client.post("/api/auth/change-password", json={
            "old_password": "old",
            "new_password": "new123",
            "confirm_password": "new123",
        })
        assert response.status_code in (401, 403)
