"""
测试 app/rag/reranker.py — 重排序器
"""
import pytest
from langchain_core.documents import Document
from app.rag.reranker import SimpleReranker, get_reranker


class TestSimpleReranker:
    """测试关键词重排序"""

    def test_rerank_preserves_all_docs(self):
        """重排序不丢失文档"""
        reranker = SimpleReranker()
        docs = [
            (Document(page_content="试验药物保存温度为2-8℃", metadata={"source": "a.pdf"}), 0.8),
            (Document(page_content="筛选期需完成血常规检查", metadata={"source": "b.pdf"}), 0.6),
            (Document(page_content="AE定义为不良医学事件", metadata={"source": "c.pdf"}), 0.4),
        ]
        result = reranker.rerank("药物保存温度", docs)
        assert len(result) == len(docs)

    def test_rerank_sorts_by_relevance(self):
        """更相关的文档排在前面（英文关键词匹配）"""
        reranker = SimpleReranker()
        docs = [
            (Document(page_content="weather is nice today for walking", metadata={}), 0.7),
            (Document(page_content="drug storage temperature is 2-8 celsius", metadata={}), 0.5),
        ]
        result = reranker.rerank("drug storage temperature", docs)
        # 包含关键词 "drug storage temperature" 的文档应该得分更高
        assert "drug" in result[0][0].page_content

    def test_rerank_empty_query(self):
        """空查询不报错"""
        reranker = SimpleReranker()
        docs = [
            (Document(page_content="测试内容", metadata={}), 0.5),
        ]
        result = reranker.rerank("", docs)
        assert len(result) == 1

    def test_rerank_empty_docs(self):
        """空文档列表不报错"""
        reranker = SimpleReranker()
        result = reranker.rerank("测试", [])
        assert result == []


class TestGetReranker:
    """测试单例"""

    def test_returns_same_instance(self):
        """两次调用返回同一实例"""
        r1 = get_reranker()
        r2 = get_reranker()
        assert r1 is r2

    def test_returns_simple_reranker(self):
        """返回 SimpleReranker 实例"""
        r = get_reranker()
        assert isinstance(r, SimpleReranker)
