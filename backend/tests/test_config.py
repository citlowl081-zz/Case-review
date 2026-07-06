"""
测试 app/core/config.py — 应用配置加载
"""
import pytest
from pathlib import Path


class TestSettings:
    """测试 Settings 配置类"""

    def test_default_values_loaded(self):
        """默认值正确加载"""
        from app.core.config import settings
        assert settings.APP_NAME == "Clinical Trial Document Review RAG Agent"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.APP_PORT == 8000

    def test_llm_model_name(self):
        """LLM 模型名存在"""
        from app.core.config import settings
        assert settings.LLM_MODEL_NAME in ("qwen3-max", "qwen-max", "qwen-plus")
        assert len(settings.LLM_MODEL_NAME) > 0

    def test_embedding_model(self):
        """Embedding 模型名存在"""
        from app.core.config import settings
        assert "embedding" in settings.EMBEDDING_MODEL

    def test_dashscope_base_url(self):
        """DashScope 地址正确"""
        from app.core.config import settings
        assert "dashscope" in settings.DASHSCOPE_BASE_URL or \
               "maas.aliyuncs.com" in settings.DASHSCOPE_BASE_URL

    def test_database_url_not_empty(self):
        """数据库 URL 已配置"""
        from app.core.config import settings
        assert len(settings.DATABASE_URL) > 0

    def test_chunk_size_positive(self):
        """chunk_size 是正数"""
        from app.core.config import settings
        assert settings.CHUNK_SIZE > 0
        assert settings.CHUNK_OVERLAP >= 0

    def test_jwt_expire_days_positive(self):
        """JWT 过期天数是正数"""
        from app.core.config import settings
        assert settings.JWT_EXPIRE_DAYS > 0

    def test_allowed_extensions_includes_pdf(self):
        """允许上传 PDF"""
        from app.core.config import settings
        assert ".pdf" in settings.ALLOWED_UPLOAD_EXTENSIONS

    def test_admin_defaults(self):
        """管理员默认配置存在"""
        from app.core.config import settings
        assert settings.ADMIN_USERNAME == "admin"
        assert settings.ADMIN_PASSWORD == "123456"

    def test_upload_dir_exists(self):
        """上传目录自动创建"""
        from app.core.config import settings
        assert Path(settings.UPLOAD_DIR).exists()
