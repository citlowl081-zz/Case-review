"""
测试 app/core/security.py — JWT 令牌和密码哈希
"""
import pytest
from unittest.mock import patch
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestHashPassword:
    """测试密码哈希功能"""

    def test_hash_returns_different_from_input(self):
        """加密后的结果和原始密码不同"""
        result = hash_password("123456")
        assert result != "123456"

    def test_hash_starts_with_bcrypt_prefix(self):
        """bcrypt 哈希以 $2b$ 开头"""
        result = hash_password("mypassword")
        assert result.startswith("$2b$")

    def test_same_password_produces_different_hash(self):
        """每次加密同一个密码产生不同哈希（盐值随机）"""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2

    def test_empty_password(self):
        """空密码也能正常加密"""
        result = hash_password("")
        assert result.startswith("$2b$")


class TestVerifyPassword:
    """测试密码验证功能"""

    def test_correct_password_returns_true(self):
        """正确密码验证通过"""
        h = hash_password("correct123")
        assert verify_password("correct123", h) is True

    def test_wrong_password_returns_false(self):
        """错误密码验证失败"""
        h = hash_password("real_password")
        assert verify_password("wrong_password", h) is False

    def test_case_sensitive(self):
        """密码区分大小写"""
        h = hash_password("Password123")
        assert verify_password("password123", h) is False

    def test_empty_password_verification(self):
        """空密码也能正常验证"""
        h = hash_password("")
        assert verify_password("", h) is True


class TestJWTToken:
    """测试 JWT 令牌功能"""

    def test_create_token_returns_string(self):
        """create_access_token 返回字符串"""
        token = create_access_token(data={"sub": "user123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_three_parts(self):
        """JWT 由三部分组成，用 . 分隔"""
        token = create_access_token(data={"sub": "user123"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_decode_valid_token_returns_payload(self):
        """有效令牌可以解码出原始数据"""
        token = create_access_token(data={"sub": "user123", "role": "admin"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    def test_decode_invalid_token_returns_none(self):
        """无效令牌返回 None"""
        payload = decode_access_token("invalid.token.here")
        assert payload is None

    def test_decode_empty_string_returns_none(self):
        """空字符串返回 None"""
        payload = decode_access_token("")
        assert payload is None

    def test_decode_garbled_text_returns_none(self):
        """乱码文本返回 None"""
        payload = decode_access_token("这不是一个有效的JWT令牌")
        assert payload is None

    def test_token_includes_expiration(self):
        """令牌包含过期时间 exp"""
        token = create_access_token(data={"sub": "user123"})
        payload = decode_access_token(token)
        assert "exp" in payload
