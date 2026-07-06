"""
测试 app/rag/embeddings.py — 阿里云百炼 Embedding
"""
import pytest
from unittest.mock import patch, MagicMock
from app.rag.embeddings import DashScopeEmbeddings, get_embeddings


class TestDashScopeEmbeddings:
    """测试自定义 Embedding 类"""

    def test_init_defaults(self):
        """默认参数初始化"""
        emb = DashScopeEmbeddings()
        assert emb.model is not None
        assert len(emb.model) > 0
        assert emb.api_key is not None

    def test_init_custom_params(self):
        """自定义参数初始化"""
        emb = DashScopeEmbeddings(
            model="text-embedding-v3",
            api_key="sk-test-key",
            base_url="https://test.example.com/v1",
        )
        assert emb.model == "text-embedding-v3"
        assert emb.api_key == "sk-test-key"
        assert "test.example.com" in emb.base_url

    def test_embed_query_returns_list(self):
        """embed_query 返回浮点数列表"""
        emb = DashScopeEmbeddings(
            api_key="sk-test-key",
            base_url="https://test.example.com/v1",
        )
        with patch.object(emb, '_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}]
            }
            mock_client.post.return_value = mock_resp

            result = emb.embed_query("测试文本")
            assert isinstance(result, list)
            assert len(result) == 5
            assert all(isinstance(x, float) for x in result)

    def test_embed_documents_returns_list_of_lists(self):
        """embed_documents 返回二维列表"""
        emb = DashScopeEmbeddings(
            api_key="sk-test-key",
            base_url="https://test.example.com/v1",
        )
        with patch.object(emb, '_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            mock_client.post.return_value = mock_resp

            result = emb.embed_documents(["文本1", "文本2"])
            assert len(result) == 2
            assert all(isinstance(v, list) for v in result)

    def test_api_error_raises_runtime_error(self):
        """API 错误抛出 RuntimeError"""
        emb = DashScopeEmbeddings(
            api_key="sk-test-key",
            base_url="https://test.example.com/v1",
        )
        with patch.object(emb, '_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.text = "Internal Server Error"
            mock_client.post.return_value = mock_resp

            with pytest.raises(RuntimeError, match="500"):
                emb.embed_query("测试")


class TestGetEmbeddings:
    """测试单例"""

    def test_returns_same_instance(self):
        """返回同一实例"""
        e1 = get_embeddings()
        e2 = get_embeddings()
        assert e1 is e2

    def test_returns_dashscope_embeddings(self):
        """返回 DashScopeEmbeddings"""
        e = get_embeddings()
        assert isinstance(e, DashScopeEmbeddings)
