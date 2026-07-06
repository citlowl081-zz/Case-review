"""
测试 app/core/deps.py — FastAPI 依赖注入
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


class TestGetCurrentUser:
    """测试 JWT 认证依赖"""

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """无效 token 返回 401"""
        from app.core.deps import get_current_user

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid.token.here"

        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=mock_credentials, db=mock_db)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_user_not_found_raises_401(self):
        """有效 token 但用户不存在返回 401"""
        from app.core.deps import get_current_user
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": "nonexistent-user-id"})

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await get_current_user(credentials=mock_credentials, db=mock_db)
        assert exc.value.status_code == 401


class TestGetAdminUser:
    """测试管理员权限依赖"""

    @pytest.mark.asyncio
    async def test_regular_user_raises_403(self):
        """普通用户访问返回 403"""
        from app.core.deps import get_admin_user
        from app.models.user import User

        regular_user = User(
            id="user-123",
            username="regular_user",
            password_hash="hash",
            role="user",
            is_active=True,
        )

        with pytest.raises(HTTPException) as exc:
            await get_admin_user(current_user=regular_user)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        """管理员用户通过"""
        from app.core.deps import get_admin_user
        from app.models.user import User

        admin_user = User(
            id="admin-123",
            username="admin",
            password_hash="hash",
            role="admin",
            is_active=True,
        )

        result = await get_admin_user(current_user=admin_user)
        assert result is admin_user


class TestPaginationParams:
    """测试分页参数"""

    def test_default_values(self):
        """默认页码和每页数量"""
        from app.core.deps import PaginationParams
        # PaginationParams is designed as FastAPI dependency with Query params
        p = PaginationParams(page=1, page_size=20)
        assert p.page == 1
        assert p.page_size == 20
        assert p.offset == 0

    def test_custom_page(self):
        """自定义页码"""
        from app.core.deps import PaginationParams
        p = PaginationParams(page=3, page_size=10)
        assert p.page == 3
        assert p.page_size == 10
        assert p.offset == 20  # (3-1)*10
